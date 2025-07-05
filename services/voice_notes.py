import os
import subprocess
import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.config_voice import VOICE_AUTHORIZED_USERS, VOICE_DEST_CHANNEL_ID

def is_user_authorized(user_id, username):
    return user_id in VOICE_AUTHORIZED_USERS or username in VOICE_AUTHORIZED_USERS

def convert_mp3_to_ogg(input_path, output_path, title=None, artist=None, album=None):
    """Convierte cualquier formato de audio a OGG/OPUS para nota de voz con metadata personalizada"""
    # Buscar ffmpeg en ubicaciones comunes
    possible_paths = [
        "ffmpeg",  # Si está en PATH
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"
    ]
    
    ffmpeg_path = None
    for path in possible_paths:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            ffmpeg_path = path
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not ffmpeg_path:
        raise Exception("FFmpeg no encontrado. Por favor instala FFmpeg o especifica la ruta correcta.")
    
    # Comando base
    cmd = [
        ffmpeg_path, "-i", input_path,
        "-vn",  # ¡IMPORTANTE! Desactivar video (no incluir carátulas)
        "-ac", "1",  # Mono
        "-ar", "48000",  # 48kHz
        "-c:a", "libopus",  # Codec OPUS
        "-b:a", "64k",  # Bitrate optimizado para voz
        "-f", "ogg",  # Forzar formato OGG
    ]
    
    # Agregar metadata si se proporciona
    if title:
        cmd.extend(["-metadata", f"title={title}"])
    if artist:
        cmd.extend(["-metadata", f"artist={artist}"])
    if album:
        cmd.extend(["-metadata", f"album={album}"])
    
    # Agregar metadata adicional para canal premium
    cmd.extend([
        "-metadata", "comment=Contenido Premium Exclusivo",
        "-metadata", "genre=Premium Content",
        "-metadata", f"date={__import__('datetime').datetime.now().year}"
    ])
    
    # Archivo de salida y sobrescribir
    cmd.extend([output_path, "-y"])
    
    subprocess.run(cmd, check=True)

# Actualizar la función send_voice_note para incluir metadata
async def send_voice_note(bot, chat_id, ogg_path, caption="", title=None):
    """Envía un archivo como nota de voz a Telegram con metadata"""
    with open(ogg_path, "rb") as voice_file:
        # Si hay título, incluirlo en el filename del archivo
        filename = f"{title}.ogg" if title else "voice_note.ogg"
        
        await bot.send_voice(
            chat_id=chat_id,
            voice=voice_file,
            caption=caption,
            parse_mode="HTML",
            filename=filename  # Nombre del archivo personalizado
        )

async def send_voice_note(bot, chat_id, ogg_path, caption=""):
    """Envía un archivo como nota de voz a Telegram"""
    with open(ogg_path, "rb") as voice_file:
        await bot.send_voice(
            chat_id=chat_id,
            voice=voice_file,
            caption=caption,
            parse_mode="HTML"
        )

async def handle_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para procesar archivos de audio enviados al bot"""
    user = update.effective_user
    if not is_user_authorized(user.id, user.username):
        await update.message.reply_text("❌ Acceso no permitido.")
        return

    audio = update.message.audio or update.message.voice or update.message.document
    if not audio:
        await update.message.reply_text("Por favor, envía un archivo de audio.")
        return

    # Verificar si es un archivo de audio válido
    valid_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.wma']
    file_name = getattr(audio, 'file_name', '')
    
    if not any(file_name.lower().endswith(ext) for ext in valid_extensions):
        await update.message.reply_text("Por favor, envía un archivo de audio válido (MP3, WAV, M4A, OGG, FLAC, WMA).")
        return

    file_id = audio.file_id
    temp_input = f"temp_{file_id}_input.{file_name.split('.')[-1] if '.' in file_name else 'mp3'}"
    temp_ogg = f"temp_{file_id}.ogg"

    try:
        # Descargar el archivo
        file = await context.bot.get_file(file_id)
        await file.download_to_drive(temp_input)
        logging.info(f"Descargado: {file_id} -> {temp_input}")

        # Convertir a OGG/OPUS (nota de voz)
        convert_mp3_to_ogg(temp_input, temp_ogg)
        logging.info(f"Convertido: {temp_input} -> {temp_ogg}")

        # Enviar como nota de voz
        caption = update.message.caption or ""
        await send_voice_note(context.bot, VOICE_DEST_CHANNEL_ID, temp_ogg, caption)
        
        await update.message.reply_text("✅ Nota de voz enviada al canal exitosamente!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error al procesar el archivo: {str(e)}")
        logging.error(f"Error al procesar archivo de audio: {e}")
    finally:
        # Limpiar archivos temporales
        for temp_file in [temp_input, temp_ogg]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Eliminado: {temp_file}")

def get_audio_quality_settings():
    """Get audio quality settings for voice notes"""
    return {
        "low": {"bitrate": "32k", "name": "Básico (32k) - Para voz simple"},
        "medium": {"bitrate": "64k", "name": "Estándar (64k) - Calidad buena"},
        "high": {"bitrate": "96k", "name": "Alta (96k) - Calidad premium"},
        "ultra": {"bitrate": "128k", "name": "Ultra (128k) - Máxima calidad para voz"}
    }
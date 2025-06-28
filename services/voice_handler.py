from telegram.ext import MessageHandler, filters
from .voice_notes import handle_voice_note

def get_voice_note_handler():
    return MessageHandler(
        filters.AUDIO | filters.Document.AUDIO | filters.VOICE,
        handle_voice_note
    )
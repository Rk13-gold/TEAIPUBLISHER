"""
Generador de contenido AI para posts de criptomonedas.

Usa la librería openai (compatible con Ollama, OpenAI, LM Studio, etc.)
para generar análisis de 3 párrafos con llamado a la acción urgente.
"""

import logging

from openai import OpenAI

from core.config import Config
from core.database import Database
from core.models import Nicho

logger = logging.getLogger(__name__)

_POST_SYSTEM_PROMPT = (
    "Eres un analista de criptomonedas con 10 años de experiencia. "
    "Escribís en español neutro con tono directo y seguro. "
    "Usás datos concretos del mercado on-chain, derivados y órdenes. "
    "No usas adjetivos vacíos ni promesas irreales."
)

_USER_PROMPT = (
    "Generá un post de análisis de criptomonedas de EXACTAMENTE 3 párrafos.\n\n"
    "Estructura:\n"
    "1. Párrafo 1 – Hook: dato on-chain o de mercado que llame la atención.\n"
    "2. Párrafo 2 – Análisis: explicación técnica clara del contexto actual.\n"
    "3. Párrafo 3 – Cierre con llamado a la acción URGENTE (ej: 'No te quedes afuera', "
    "'Entrá ahora antes del next pump', 'Preparate para la volatilidad').\n\n"
    "NO incluyas título, ni saludo, ni hashtags. Solo 3 párrafos separados "
    "por un salto de línea."
)


def generate_post(nicho_id: int, config: Config | None = None) -> str:
    """
    Genera un post de análisis de criptomonedas basado en el prompt_base
    de un Nicho.

    Args:
        nicho_id: ID del Nicho en la DB.
        config: Instancia de Config (opcional, se crea una por defecto).

    Returns:
        Texto del post generado, o mensaje de error si falla.
    """
    if config is None:
        config = Config()

    db = Database()
    session = db.get_session()
    try:
        nicho = session.query(Nicho).get(nicho_id)
        if not nicho:
            raise ValueError(f"Nicho con id={nicho_id} no encontrado en la DB.")

        prompt_base = (nicho.prompt_base or "").strip()
        system_msg = prompt_base if prompt_base else _POST_SYSTEM_PROMPT

        client = OpenAI(
            base_url=config.ai_gen_base_url,
            api_key=config.ai_gen_api_key or "ollama",
        )

        logger.info(
            "Generando post para nicho '%s' (id=%d) con modelo %s",
            nicho.nombre, nicho_id, config.ai_gen_model,
        )

        response = client.chat.completions.create(
            model=config.ai_gen_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": _USER_PROMPT},
            ],
            temperature=0.7,
            max_tokens=600,
        )

        text = response.choices[0].message.content.strip()
        logger.info("Post generado (%d caracteres).", len(text))
        return text

    except ValueError:
        raise
    except Exception as e:
        logger.exception("Error generando post con OpenAI")
        return f"[Error al generar post: {e}]"
    finally:
        session.close()


def format_for_telegram(texto: str, ebook_id: int | None = None) -> str:
    """
    Prepara el texto para Telegram.

    Si se pasa ebook_id, agrega un marcador [BOTON_COMPRAR:{ebook_id}]
    al final para que el sistema de publicación lo reemplace por un botón inline.

    Args:
        texto: El texto generado por la IA.
        ebook_id: ID del eBook opcional para agregar el botón de compra.

    Returns:
        Texto listo para publicar en Telegram.
    """
    partes = [texto.strip()]

    if ebook_id is not None:
        partes.append("")
        partes.append(f"[BOTON_COMPRAR:{ebook_id}]")

    return "\n".join(partes)

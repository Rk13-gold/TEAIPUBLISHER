import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from core.models import Base

logger = logging.getLogger(__name__)

_LEGACY_TABLES = [
    'user_events', 'metrics', 'posts', 'images', 'titles',
    'bot_config', 'chat_config',
]

_TABLES_TO_RECREATE = ['ventas', 'ebooks', 'usuarios']


class Database:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)

        db_path = os.path.join(data_dir, 'database.db')
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        self.SessionFactory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(self.SessionFactory)

    def create_tables(self):
        try:
            self._migrate_if_needed()
            Base.metadata.create_all(self.engine)
        except Exception as e:
            logger.error(f"Error al crear las tablas: {e}")
            raise

    def _migrate_if_needed(self):
        """Migración one-shot: si detecta tablas del esquema anterior
        (bot_config, titles, etc.) las elimina y recrea ebooks/usuarios/ventas."""
        insp = inspect(self.engine)
        existing = set(insp.get_table_names())

        # Solo migra si aún existen tablas legacy
        legacy_present = [t for t in _LEGACY_TABLES if t in existing]
        if not legacy_present:
            return  # Esquema nuevo ya vigente

        with self.engine.connect() as conn:
            # Desactivar FKs temporalmente para poder dropear en orden
            conn.execute(text("PRAGMA foreign_keys = OFF"))

            for table in _TABLES_TO_RECREATE + _LEGACY_TABLES:
                if table in existing:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))

            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()

        logger.info("Migración completada: tablas legacy eliminadas, esquema listo para recrearse.")

    def get_session(self):
        return self.Session()

    def dispose(self):
        self.Session.remove()
        self.engine.dispose()


def get_telegram_credentials():
    """Return (token, chat_id) from the first active Bot + Chat in DB,
    or (None, None) if nothing is configured."""
    from core.models import Bot, Chat
    try:
        db = Database()
        session = db.get_session()
        bot = session.query(Bot).filter_by(activo=True).first()
        if bot:
            chat = session.query(Chat).filter_by(bot_id=bot.id, activo=True).first()
            if chat:
                return bot.token_api, chat.chat_id
    except Exception:
        pass
    finally:
        db.dispose()
    return None, None

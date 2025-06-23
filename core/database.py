import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from data.models import Base

class Database:
    def __init__(self):
        # Asegura que la carpeta 'data' exista
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)

        db_path = os.path.join(data_dir, 'database.db')
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        self.SessionFactory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(self.SessionFactory)

    def create_tables(self):
        """
        Crea todas las tablas definidas en los modelos si no existen.
        """
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            print(f"Error al crear las tablas de la base de datos: {e}")
            raise

    def get_session(self):
        """
        Devuelve una nueva sesión de base de datos.
        Recuerda cerrar la sesión después de usarla.
        """
        return self.Session()

    def dispose(self):
        """
        Libera los recursos del engine y las sesiones.
        """
        self.Session.remove()
        self.engine.dispose()
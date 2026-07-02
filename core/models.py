from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class Nicho(Base):
    __tablename__ = 'nichos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    prompt_base = Column(Text, nullable=True)

    ebooks = relationship("Ebook", back_populates="nicho", cascade="all, delete-orphan")


class Ebook(Base):
    __tablename__ = 'ebooks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nicho_id = Column(Integer, ForeignKey('nichos.id'), nullable=False)
    titulo = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    ruta_pdf = Column(String, nullable=True)
    caratula = Column(String, nullable=True)

    nicho = relationship("Nicho", back_populates="ebooks")
    ventas = relationship("Venta", back_populates="ebook", cascade="all, delete-orphan")


class Bot(Base):
    __tablename__ = 'bots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    token_api = Column(String, nullable=False)
    activo = Column(Boolean, default=True)

    chats = relationship("Chat", back_populates="bot", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('bots.id'), nullable=False)
    tipo = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    nombre = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    bot = relationship("Bot", back_populates="chats")


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    estado = Column(String, nullable=False, default='Lead')

    ventas = relationship("Venta", back_populates="usuario", cascade="all, delete-orphan")


class Venta(Base):
    __tablename__ = 'ventas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    ebook_id = Column(Integer, ForeignKey('ebooks.id'), nullable=False)
    metodo_pago = Column(String, nullable=False)
    payment_id = Column(String, nullable=True)
    monto = Column(Float, nullable=False)
    estado = Column(String, nullable=False, default='Pendiente')

    usuario = relationship("Usuario", back_populates="ventas")
    ebook = relationship("Ebook", back_populates="ventas")


class ScheduleStatus(enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('bots.id'), nullable=False)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    content = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    repeat = Column(String, nullable=True)  # None, 'daily', 'weekly', 'monthly'
    status = Column(String, nullable=False, default='pending')
    created_at = Column(DateTime, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)

    bot = relationship("Bot")
    chat = relationship("Chat")

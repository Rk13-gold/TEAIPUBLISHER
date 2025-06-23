from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    user_event_id = Column(Integer, ForeignKey('user_events.id'))
    clicks = Column(Integer, default=0)
    reactions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="metrics")
    user_event = relationship("UserEvent", back_populates="metrics")

class Title(Base):
    __tablename__ = 'titles'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    images = relationship("Image", back_populates="title", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="title", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('titles.id'), nullable=False)
    path = Column(String, nullable=False)
    keywords = Column(String)
    tone = Column(String)

    title = relationship("Title", back_populates="images")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('titles.id'), nullable=False)
    image_path = Column(String, nullable=True)  # Permite posts solo de texto
    content = Column(Text, nullable=False)
    schedule_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    title = relationship("Title", back_populates="posts")
    metrics = relationship("Metric", back_populates="post", cascade="all, delete-orphan")

class UserEvent(Base):
    __tablename__ = 'user_events'
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metrics = relationship("Metric", back_populates="user_event", cascade="all, delete-orphan")
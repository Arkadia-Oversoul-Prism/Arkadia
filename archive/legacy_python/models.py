# models.py
# Arkadia — ORM Models

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from db import engine, Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(128), unique=True, index=True, nullable=False)
    display_name = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    threads = relationship("Thread", back_populates="user")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    role = Column(String(32), nullable=False)  # "user" or "arkana"
    sender = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    thread = relationship("Thread", back_populates="messages")


def init_db() -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

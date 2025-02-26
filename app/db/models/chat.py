from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.db.models.base import Base
from app.db.models.user import User


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, nullable=True)  # null for private chats
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    chat_participant = relationship(
        "ChatParticipant", back_populates="chat_room")
    chat_message = relationship("ChatMessage", back_populates="chat_room")


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    chat_id = Column(Integer, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=func.now())

    chat_room = relationship("ChatRoom", back_populates="chat_participant")
    user = relationship("User", back_populates="chat_participant")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    chat_id = Column(Integer, ForeignKey("chat_rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    chat_room = relationship("ChatRoom", back_populates="chat_message")
    user = relationship("User", back_populates="chat_message")

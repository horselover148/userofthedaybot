"""Database models"""

from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, ForeignKey, UniqueConstraint, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    firstname: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relationships
    chat_users: Mapped[List["ChatUser"]] = relationship(back_populates="user")
    
    def get_notification_name(self) -> str:
        """Get name for notification"""
        if self.username:
            return f"@{self.username}"
        return self.firstname or "Аноним"
    
    def get_stats_name(self) -> str:
        """Get name for statistics display: firstname (username) or just firstname"""
        if self.username:
            return f"{self.firstname} (@{self.username})"
        return self.firstname or "Аноним"


class Chat(Base):
    """Chat model"""
    __tablename__ = "chats"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_of_the_day: Mapped[str] = mapped_column(String(255), nullable=True)
    pidor_of_the_day: Mapped[str] = mapped_column(String(255), nullable=True)
    user_of_the_day_run_day: Mapped[int] = mapped_column(Integer, nullable=True)
    pidor_of_the_day_run_day: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Relationships
    chat_users: Mapped[List["ChatUser"]] = relationship(back_populates="chat")


class ChatUser(Base):
    """Chat-User relationship model"""
    __tablename__ = "chat_user"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    user_day_counter: Mapped[int] = mapped_column(Integer, default=0)
    pidor_counter: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_users")
    chat: Mapped["Chat"] = relationship(back_populates="chat_users")
    
    __table_args__ = (
        UniqueConstraint('chat_id', 'user_id', name='unique_chat_user'),
    )

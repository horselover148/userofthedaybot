"""Database connection and operations"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError

from bot.config import config
from bot.models import Base, User, Chat, ChatUser

logger = logging.getLogger(__name__)


class Database:
    """Database handler"""
    
    def __init__(self):
        self.engine = create_async_engine(
            config.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def init_db(self):
        """Initialize database - create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    
    async def registration(
        self,
        chat_id: int,
        user_id: int,
        username: Optional[str],
        firstname: Optional[str]
    ) -> Tuple[bool, str]:
        """
        Register user in chat
        Returns: (success: bool, message: str)
        """
        async with self.async_session() as session:
            try:
                # Check if user already registered in this chat
                stmt = select(ChatUser).where(
                    and_(
                        ChatUser.chat_id == chat_id,
                        ChatUser.user_id == user_id
                    )
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    return False, "Ты уже в игре"
                
                # Add or update user
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    user = User(user_id=user_id, username=username, firstname=firstname)
                    session.add(user)
                else:
                    # Update user info
                    user.username = username
                    user.firstname = firstname
                
                # Add or get chat
                stmt = select(Chat).where(Chat.chat_id == chat_id)
                result = await session.execute(stmt)
                chat = result.scalar_one_or_none()
                
                if not chat:
                    chat = Chat(chat_id=chat_id)
                    session.add(chat)
                
                # Add chat-user relationship
                chat_user = ChatUser(chat_id=chat_id, user_id=user_id)
                session.add(chat_user)
                
                await session.commit()
                return True, f"{firstname or username}, Ты в игре"
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Registration error: {e}")
                return False, "Ошибка регистрации"
    
    async def get_players(self, chat_id: int) -> List[Tuple[User, int, int]]:
        """
        Get list of players in chat
        Returns: List of (User, user_day_counter, pidor_counter)
        """
        async with self.async_session() as session:
            stmt = (
                select(User, ChatUser.user_day_counter, ChatUser.pidor_counter)
                .join(ChatUser, User.user_id == ChatUser.user_id)
                .where(ChatUser.chat_id == chat_id)
                .order_by(ChatUser.user_day_counter.desc())
            )
            result = await session.execute(stmt)
            return result.all()
    
    async def is_same_day_running(self, chat_id: int, day: int, game_type: str) -> bool:
        """Check if game was already run today"""
        async with self.async_session() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            result = await session.execute(stmt)
            chat = result.scalar_one_or_none()
            
            if not chat:
                return False
            
            if game_type == "user_of_the_day":
                return chat.user_of_the_day_run_day == day
            elif game_type == "pidor_of_the_day":
                return chat.pidor_of_the_day_run_day == day
            
            return False
    
    async def get_winner(self, chat_id: int, game_type: str) -> Optional[str]:
        """Get today's winner"""
        async with self.async_session() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            result = await session.execute(stmt)
            chat = result.scalar_one_or_none()
            
            if not chat:
                return None
            
            if game_type == "user_of_the_day":
                return chat.user_of_the_day
            elif game_type == "pidor_of_the_day":
                return chat.pidor_of_the_day
            
            return None
    
    async def set_winner(
        self,
        chat_id: int,
        user_id: int,
        winner_name: str,
        day: int,
        game_type: str
    ):
        """Set winner and update counters"""
        async with self.async_session() as session:
            try:
                # Update chat with winner and day
                if game_type == "user_of_the_day":
                    stmt = (
                        update(Chat)
                        .where(Chat.chat_id == chat_id)
                        .values(
                            user_of_the_day=winner_name,
                            user_of_the_day_run_day=day
                        )
                    )
                    counter_field = ChatUser.user_day_counter
                elif game_type == "pidor_of_the_day":
                    stmt = (
                        update(Chat)
                        .where(Chat.chat_id == chat_id)
                        .values(
                            pidor_of_the_day=winner_name,
                            pidor_of_the_day_run_day=day
                        )
                    )
                    counter_field = ChatUser.pidor_counter
                else:
                    return
                
                await session.execute(stmt)
                
                # Update counter for user
                stmt = (
                    update(ChatUser)
                    .where(
                        and_(
                            ChatUser.chat_id == chat_id,
                            ChatUser.user_id == user_id
                        )
                    )
                    .values({counter_field: counter_field + 1})
                )
                await session.execute(stmt)
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error setting winner: {e}")


# Global database instance
db = Database()

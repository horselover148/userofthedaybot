"""Main bot file"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select

from bot.config import config
from bot.database import db
from bot.handlers import router
from bot.models import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)


async def check_and_populate_db():
    """Check if DB is empty and populate if needed"""
    try:
        from bot.populate_db import populate_database
        
        async with db.async_session() as session:
            stmt = select(User)
            result = await session.execute(stmt)
            existing_users = result.scalars().first()
            
            if not existing_users:
                logger.info("Database is empty. Running population script...")
                await populate_database()
            else:
                logger.info("Database already contains data. Skipping population.")
    except Exception as e:
        logger.error(f"Error checking/populating database: {e}")


async def main():
    """Main function to start the bot"""
    
    # Initialize database
    logger.info("Initializing database...")
    await db.init_db()
    logger.info("Database initialized")
    
    # Check and populate database if empty
    await check_and_populate_db()
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register router with handlers
    dp.include_router(router)
    
    # Start bot
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

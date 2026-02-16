"""Script to populate database with initial data"""

import asyncio
import logging
from sqlalchemy import select

from bot.config import config
from bot.database import Database
from bot.models import User, Chat, ChatUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Данные для заполнения
# Формат: user_id, username (без @), firstname
USERS_DATA = [
    (145778241, "RussianBeerHunter", "Имянуил Фамилевски"),
    (994433205, "voylur", "Артём"),
    (151191687, "gusar_off", "Ilya"),
    (340308835, "Mestr3z", "Владислав"),
    (421310117, "jimmyminds", "Вадим Стебницкий"),
    (261317318, "vesellluxa", "прогрессив лёха"),
    (672542484, "desomorphine187", "Филипп"),
    (573196430, "Toony_Hoodz", "Toony Hoodz"),
    (943135378, None, "Daniil Perederiy"),  # без username
    (2383188040, "rim1sta", "Kostya"),
    (643336974, "romanovh", "Игорь Романов"),
    (985398310, "ytoodmngd", "Anton"),
    (643546122, "lord0ftheflies", "Си-Джей"),  # первая запись
    (395691714, "Cobra2525", "Артём"),
    (344823448, "dfrip", "Ростислав"),
]

# Дополнительные записи с дублями (разные firstname для того же user)
# Формат: username, firstname, user_day_counter, pidor_counter, FAKE_user_id
DUPLICATE_USERS = [
    ("lord0ftheflies", "Филипп", 7, 9, 6435461220),  # фейковый ID для второй записи lord0ftheflies
    ("rim1sta", "Kostya", 5, 12, 23831880400),  # фейковый ID для второй записи rim1sta
]

# Результаты Красавчик Дня
USER_OF_THE_DAY_RESULTS = {
    "voylur": 44,
    "dfrip": 33,
    "gusar_off": 32,
    "Mestr3z": 30,
    "jimmyminds": 29,
    "vesellluxa": 28,
    "desomorphine187": 26,
    "Toony_Hoodz": 25,
    "Daniil Perederiy": 23,  # по firstname
    "rim1sta": 22,  # первая запись
    "romanovh": 20,
    "RussianBeerHunter": 20,
    "ytoodmngd": 13,
    "lord0ftheflies": 11,  # первая запись (Си-Джей)
    # "lord0ftheflies": 7,  # вторая запись (Филипп) - в DUPLICATE_USERS
    # "rim1sta": 5,  # вторая запись - в DUPLICATE_USERS
    "Cobra2525": 1,
}

# Результаты ПИДОР Дня
PIDOR_OF_THE_DAY_RESULTS = {
    "Toony_Hoodz": 34,
    "Daniil Perederiy": 33,  # по firstname
    "jimmyminds": 30,
    "vesellluxa": 29,
    "voylur": 28,
    "dfrip": 27,
    "desomorphine187": 27,
    "Mestr3z": 23,
    "ytoodmngd": 21,
    "gusar_off": 18,
    "rim1sta": 16,  # первая запись
    "RussianBeerHunter": 15,
    "romanovh": 13,
    "lord0ftheflies": 12,  # первая запись (Си-Джей)
    # "rim1sta": 12,  # вторая запись - в DUPLICATE_USERS
    # "lord0ftheflies": 9,  # вторая запись (Филипп) - в DUPLICATE_USERS
    "Cobra2525": 5,
}

# ID чата (замените на реальный ID вашего чата)
DEFAULT_CHAT_ID = -5050482476


async def populate_database():
    """Populate database with initial data"""
    
    db = Database()
    
    # Инициализировать БД (создать таблицы)
    await db.init_db()
    
    async with db.async_session() as session:
        # Проверить, есть ли уже данные
        stmt = select(User)
        result = await session.execute(stmt)
        existing_users = result.scalars().all()
        
        if existing_users:
            logger.info("Database already contains data. Skipping population.")
            return
        
        logger.info("Starting database population...")
        
        # Создать чат
        chat = Chat(chat_id=DEFAULT_CHAT_ID)
        session.add(chat)
        
        # Добавить пользователей
        for user_id, username, firstname in USERS_DATA:
            user = User(user_id=user_id, username=username, firstname=firstname)
            session.add(user)
            
            # Получить счётчики для этого пользователя
            # Ищем по username или firstname
            search_key = username if username else firstname
            user_counter = USER_OF_THE_DAY_RESULTS.get(search_key, 0)
            pidor_counter = PIDOR_OF_THE_DAY_RESULTS.get(search_key, 0)
            
            # Создать связь chat-user
            chat_user = ChatUser(
                chat_id=DEFAULT_CHAT_ID,
                user_id=user_id,
                user_day_counter=user_counter,
                pidor_counter=pidor_counter
            )
            session.add(chat_user)
            
            logger.info(
                f"Added user: {firstname} (@{username}) - "
                f"User: {user_counter}, Pidor: {pidor_counter}"
            )
        
        # Добавить дубликаты (те же username, но с фейковыми user_id для сохранения истории)
        for username, firstname, user_counter, pidor_counter, fake_user_id in DUPLICATE_USERS:
            # Создать фейкового пользователя с уникальным ID
            fake_user = User(user_id=fake_user_id, username=username, firstname=firstname)
            session.add(fake_user)
            
            # Создать связь chat-user для фейкового пользователя
            chat_user = ChatUser(
                chat_id=DEFAULT_CHAT_ID,
                user_id=fake_user_id,
                user_day_counter=user_counter,
                pidor_counter=pidor_counter
            )
            session.add(chat_user)
            logger.info(
                f"Added duplicate entry: {firstname} (@{username}) - "
                f"User: {user_counter}, Pidor: {pidor_counter} (fake_id: {fake_user_id})"
            )
        
        # Сохранить изменения
        await session.commit()
        logger.info("Database population completed successfully!")


if __name__ == "__main__":
    asyncio.run(populate_database())

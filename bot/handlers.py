"""Bot command handlers"""

import asyncio
import random
import logging
from datetime import datetime, date
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import db
from bot.messages import (
    MESSAGES_USER_OF_THE_DAY,
    MESSAGES_PIDOR_OF_THE_DAY,
    NO_PLAYERS,
    STAT_USER_HEADER,
    STAT_PIDOR_HEADER
)

logger = logging.getLogger(__name__)
router = Router()

MESSAGE_DELAY = 1.5  # seconds

# Хардкод: Разрешенные чаты
ALLOWED_CHATS = [-1645180577, -5050482476]

# Хардкод: Специальный период для RussianBeerHunter
SPECIAL_PIDOR_USERNAME = "RussianBeerHunter"
SPECIAL_PIDOR_START = date(2026, 2, 18)  # 18.02.2026
SPECIAL_PIDOR_END = date(2026, 2, 25)    # 25.02.2026


def get_today() -> int:
    """Get current day of year"""
    return datetime.now().timetuple().tm_yday


async def send_messages_with_delay(message: Message, messages: list, winner_name: str):
    """Send messages with delay"""
    # Send all messages except the first one (which contains winner)
    for msg in messages[1:]:
        await message.answer(msg)
        await asyncio.sleep(MESSAGE_DELAY)
    
    # Send final message with winner
    await message.answer(messages[0] + winner_name)


def is_chat_allowed(chat_id: int) -> bool:
    """Check if chat is allowed"""
    return chat_id in ALLOWED_CHATS


def is_special_pidor_period() -> bool:
    """Check if current date is in special period for RussianBeerHunter"""
    today = date.today()
    return SPECIAL_PIDOR_START <= today <= SPECIAL_PIDOR_END


@router.message(Command("reg"))
async def cmd_registration(message: Message):
    """Handle /reg command - register user in game"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    user = message.from_user
    success, msg = await db.registration(
        chat_id=message.chat.id,
        user_id=user.id,
        username=user.username,
        firstname=user.first_name
    )
    
    await message.answer(msg)


@router.message(Command("run"))
async def cmd_run_user_of_the_day(message: Message):
    """Handle /run command - run 'User of the Day' game"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await run_game(message, "user_of_the_day", MESSAGES_USER_OF_THE_DAY)


@router.message(Command("pidor"))
async def cmd_run_pidor_of_the_day(message: Message):
    """Handle /pidor command - run 'Pidor of the Day' game"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await run_game(message, "pidor_of_the_day", MESSAGES_PIDOR_OF_THE_DAY)


async def run_game(message: Message, game_type: str, messages: list):
    """Run game logic"""
    chat_id = message.chat.id
    today = get_today()
    
    # Check if game was already run today
    if await db.is_same_day_running(chat_id, today, game_type):
        winner = await db.get_winner(chat_id, game_type)
        await message.answer(messages[0] + (winner or "Неизвестно"))
        return
    
    # Get players
    players = await db.get_players(chat_id)
    
    if not players:
        await message.answer(NO_PLAYERS)
        return
    
    # ХАРДКОД: Специальный период для RussianBeerHunter (18.02.2026 - 25.02.2026)
    if game_type == "pidor_of_the_day" and is_special_pidor_period():
        # Найти RussianBeerHunter среди игроков
        special_user = None
        for player_data in players:
            user = player_data[0]
            if user.username == SPECIAL_PIDOR_USERNAME:
                special_user = user
                break
        
        if special_user:
            winner_user = special_user
            winner_name = special_user.get_stats_name()  # Используем формат "firstname (@username)"
            logger.info(f"Special period: {SPECIAL_PIDOR_USERNAME} is pidor of the day")
        else:
            # Если RussianBeerHunter не зарегистрирован, выбрать случайного
            logger.warning(f"{SPECIAL_PIDOR_USERNAME} not found in players, selecting random")
            winner_data = random.choice(players)
            winner_user = winner_data[0]
            winner_name = winner_user.get_stats_name() if game_type == "pidor_of_the_day" else winner_user.get_notification_name()
    else:
        # Select random winner
        winner_data = random.choice(players)
        winner_user = winner_data[0]
        # Для обоих игр используем формат "firstname (@username)"
        winner_name = winner_user.get_stats_name()
    
    # Save winner to database
    await db.set_winner(chat_id, winner_user.user_id, winner_name, today, game_type)
    
    # Send messages with delay
    await send_messages_with_delay(message, messages, winner_name)


@router.message(Command("stat_user"))
async def cmd_stat_user(message: Message):
    """Handle /stat_user command - show User of the Day statistics"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await send_statistics(message, "user", STAT_USER_HEADER)


@router.message(Command("stat_pidor"))
async def cmd_stat_pidor(message: Message):
    """Handle /stat_pidor command - show Pidor of the Day statistics"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await send_statistics(message, "pidor", STAT_PIDOR_HEADER)


@router.message(Command("pidorstats"))
async def cmd_pidorstats(message: Message):
    """Handle /pidorstats command - show Pidor of the Day statistics"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await send_statistics(message, "pidor", STAT_PIDOR_HEADER)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - show User of the Day statistics"""
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах")
        return
    
    # Проверка доступа к чату
    if not is_chat_allowed(message.chat.id):
        logger.info(f"Access denied for chat {message.chat.id}")
        return
    
    await send_statistics(message, "user", STAT_USER_HEADER)


async def send_statistics(message: Message, stat_type: str, header: str):
    """Send game statistics"""
    chat_id = message.chat.id
    players = await db.get_players(chat_id)
    
    if not players:
        await message.answer(NO_PLAYERS)
        return
    
    # Sort players by counter (descending)
    if stat_type == "user":
        sorted_players = sorted(players, key=lambda x: x[1], reverse=True)
    else:  # pidor
        sorted_players = sorted(players, key=lambda x: x[2], reverse=True)
    
    # Build statistics message
    stats = header
    for i, player_data in enumerate(sorted_players, 1):
        user = player_data[0]
        counter = player_data[1] if stat_type == "user" else player_data[2]
        # Используем только username или firstname (без имени + username)
        display_name = user.get_stats_name()
        stats += f"{i}) {display_name} - {counter} раз(а)\n"
    
    await message.answer(stats)

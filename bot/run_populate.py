"""Standalone script to manually populate database"""

import sys
import asyncio

# Добавить путь к модулям бота
sys.path.insert(0, '/app')

from bot.populate_db import populate_database

if __name__ == "__main__":
    print("Starting database population...")
    asyncio.run(populate_database())
    print("Done!")

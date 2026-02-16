"""Bot configuration"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration class"""
    
    # Bot settings
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # PostgreSQL settings
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "useroftheday_db")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    
    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


config = Config()

"""Конфигурация приложения из .env файла."""

import os
from functools import lru_cache

from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()


class Settings:
    """Настройки приложения."""

    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./instance/shop.db")


@lru_cache
def get_settings() -> Settings:
    """Получить настройки (кэшируется)."""
    return Settings()


settings = get_settings()


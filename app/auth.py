"""Авторизация администратора через cookie-сессию."""

import hashlib
import secrets
from typing import Optional

from fastapi import Cookie, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import settings

# Сериализатор для подписи cookie
_serializer = URLSafeTimedSerializer(settings.secret_key)

# Имя cookie для сессии
SESSION_COOKIE_NAME = "admin_session"
# Время жизни сессии (24 часа)
SESSION_MAX_AGE = 86400


def verify_password(username: str, password: str) -> bool:
    """Проверить логин и пароль администратора."""
    return (
        secrets.compare_digest(username, settings.admin_username)
        and secrets.compare_digest(password, settings.admin_password)
    )


def create_session_token(username: str) -> str:
    """Создать подписанный токен сессии."""
    return _serializer.dumps({"username": username})


def verify_session_token(token: str) -> Optional[str]:
    """
    Проверить токен сессии.
    
    Returns:
        username если токен валиден, иначе None
    """
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("username")
    except BadSignature:
        return None


def set_session_cookie(response: Response, username: str) -> None:
    """Установить cookie с сессией."""
    token = create_session_token(username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        # secure=True,  # Включить в продакшене с HTTPS
    )


def clear_session_cookie(response: Response) -> None:
    """Удалить cookie сессии."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)


def get_current_admin(request: Request) -> Optional[str]:
    """
    Получить текущего администратора из cookie.
    
    Returns:
        username если авторизован, иначе None
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return verify_session_token(token)


def require_admin(request: Request) -> str:
    """
    Dependency для защиты роутов админки.
    
    Raises:
        HTTPException 401 если не авторизован
    """
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"Location": "/admin/login"},
        )
    return admin


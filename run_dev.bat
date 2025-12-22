@echo off
cd /d "%~dp0"

REM Активируем виртуальное окружение, если есть
IF EXIST ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) ELSE (
    echo Виртуальное окружение .venv не найдено. Создаю...
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    pip install --upgrade pip
    pip install -r requirements.txt
)

echo Запуск сервера Uvicorn на порту 8002...
start "" http://127.0.0.1:8002/
uvicorn app.main:app --reload --port 8002

pause
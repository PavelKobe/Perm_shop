@echo off
setlocal

:: Порт можно передать первым аргументом, по умолчанию 8002
set PORT=%1
if "%PORT%"=="" set PORT=8002

echo Проверяю процессы, занявшие порт %PORT% ...
set PID=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":%PORT% " ^| findstr /I /V "CLOSE_WAIT TIME_WAIT"') do (
  set PID=%%a
  goto :found
)

:found
if defined PID (
  echo Найден процесс PID %PID% на порту %PORT%, пытаюсь завершить...
  taskkill /PID %PID% /F >nul 2>&1
  if errorlevel 1 (
    echo Не удалось завершить процесс PID %PID%.
  ) else (
    echo Процесс PID %PID% завершен.
  )
) else (
  echo Нет процессов, слушающих порт %PORT%.
)

echo Повторная проверка порта %PORT% ...
set STILL=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":%PORT% " ^| findstr /I /V "CLOSE_WAIT TIME_WAIT"') do (
  set STILL=%%a
  goto :stillbusy
)

:stillbusy
if defined STILL (
  echo Порт %PORT% все еще занят (PID %STILL%).
  exit /b 1
) else (
  echo Порт %PORT% свободен.
)

exit /b 0



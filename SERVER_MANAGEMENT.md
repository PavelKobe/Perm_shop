# Инструкция по управлению сервером

Руководство по быстрому деплою изменений и управлению продакшн сервером.

## 📋 Содержание

1. [Подключение к серверу](#подключение-к-серверу)
2. [Быстрый деплой изменений](#быстрый-деплой-изменений)
3. [Управление сервисами](#управление-сервисами)
4. [Работа с базой данных](#работа-с-базой-данных)
5. [Загрузка изображений](#загрузка-изображений)
6. [Просмотр логов](#просмотр-логов)
7. [Откат изменений](#откат-изменений)
8. [Полезные команды](#полезные-команды)
9. [Решение проблем](#решение-проблем)

---

## 🔌 Подключение к серверу

### Через SSH

```bash
# Подключение от root
ssh root@your-server-ip

# Или от пользователя shoeapp (если настроен SSH ключ)
ssh shoeapp@your-server-ip
```

### Через WinSCP (Windows)

1. Открой WinSCP
2. Хост: `your-server-ip`
3. Пользователь: `root` или `shoeapp`
4. Пароль: (твой пароль)
5. Подключись

**Путь к проекту на сервере:** `/home/shoeapp/Perm_shop/`

---

## 🚀 Быстрый деплой изменений

### Вариант 1: Автоматический деплой (рекомендуется)

**На локальной машине (после коммита в Git):**

```bash
# 1. Закоммить изменения
git add .
git commit -m "Описание изменений"
git push origin main

# 2. Подключиться к серверу и запустить деплой
ssh shoeapp@your-server-ip "bash /home/shoeapp/Perm_shop/deploy.sh"
```

**Или на сервере напрямую:**

```bash
# Подключись к серверу
ssh shoeapp@your-server-ip

# Запусти скрипт деплоя
bash /home/shoeapp/Perm_shop/deploy.sh
```

### Вариант 2: Ручной деплой

```bash
# 1. Подключись к серверу
ssh shoeapp@your-server-ip

# 2. Перейди в директорию проекта
cd /home/shoeapp/Perm_shop

# 3. Активируй виртуальное окружение
source .venv/bin/activate

# 4. Получи последние изменения из Git
git pull origin main

# 5. Обнови зависимости (если изменились requirements.txt)
pip install --upgrade pip
pip install -r requirements.txt

# 6. Перезапусти сервис
sudo systemctl restart shoeapp

# 7. Проверь статус
sudo systemctl status shoeapp
```

### Вариант 3: Деплой только кода (без обновления зависимостей)

```bash
ssh shoeapp@your-server-ip "cd /home/shoeapp/Perm_shop && source .venv/bin/activate && git pull origin main && sudo systemctl restart shoeapp"
```

---

## ⚙️ Управление сервисами

### ⚠️ Важно: Работа в фоне

**Да, можно закрывать Putty!** Приложение работает автоматически через systemd как сервис и не зависит от SSH сессии.

- Приложение запускается автоматически при загрузке сервера (если включен `systemctl enable shoeapp`)
- Работает в фоне независимо от открытых терминалов
- Можно безопасно закрывать Putty после деплоя
- Сайт будет доступен 24/7

**Проверка, что приложение работает:**
```bash
# Проверить статус (можно выполнить в любой момент)
sudo systemctl status shoeapp

# Должно быть: "Active: active (running)"
```

### FastAPI приложение (shoeapp)

```bash
# Проверить статус
sudo systemctl status shoeapp

# Запустить
sudo systemctl start shoeapp

# Остановить
sudo systemctl stop shoeapp

# Перезапустить
sudo systemctl restart shoeapp

# Перезагрузить конфигурацию (без остановки)
sudo systemctl reload shoeapp

# Включить автозапуск при загрузке сервера
sudo systemctl enable shoeapp

# Отключить автозапуск
sudo systemctl disable shoeapp

# Просмотр логов в реальном времени
sudo journalctl -u shoeapp -f

# Последние 100 строк логов
sudo journalctl -u shoeapp -n 100
```

### Nginx

```bash
# Проверить статус
sudo systemctl status nginx

# Перезапустить
sudo systemctl restart nginx

# Перезагрузить конфигурацию (без остановки)
sudo systemctl reload nginx

# Проверить конфигурацию перед применением
sudo nginx -t

# Просмотр логов
sudo tail -f /var/log/nginx/shoeapp_error.log
sudo tail -f /var/log/nginx/shoeapp_access.log
```

---

## 💾 Работа с базой данных

### Расположение базы данных

```bash
# Путь к БД
/home/shoeapp/Perm_shop/instance/shop.db
```

### Создание резервной копии

```bash
# Вручную
cp /home/shoeapp/Perm_shop/instance/shop.db /home/shoeapp/Perm_shop/instance/shop.db.backup.$(date +%Y%m%d_%H%M%S)

# Через скрипт (если настроен)
bash /home/shoeapp/Perm_shop/backup_db.sh
```

### Восстановление из резервной копии

```bash
# Останови приложение
sudo systemctl stop shoeapp

# Восстанови БД
cp /home/shoeapp/Perm_shop/instance/shop.db.backup.YYYYMMDD_HHMMSS /home/shoeapp/Perm_shop/instance/shop.db

# Запусти приложение
sudo systemctl start shoeapp
```

### Просмотр содержимого БД

```bash
# Установи sqlite3 (если нет)
sudo apt install -y sqlite3

# Открой БД
sqlite3 /home/shoeapp/Perm_shop/instance/shop.db

# Полезные команды SQLite:
.tables                    # Показать все таблицы
.schema products           # Показать структуру таблицы products
SELECT * FROM products;    # Показать все товары
.quit                      # Выйти
```

---

## 🖼️ Загрузка изображений

### Вариант 1: Через WinSCP (рекомендуется для Windows)

1. Подключись к серверу через WinSCP
2. Перейди в `/home/shoeapp/Perm_shop/static/images/products/`
3. Скопируй изображения в нужные папки:
   - `zimnyaya/sapogi/` - для зимних сапог
   - `demisezon/botinki/` - для демисезонных ботинок
   - и т.д.

### Вариант 2: Через rsync (если есть доступ из локальной сети)

```bash
# На локальной машине (Git Bash или WSL)
rsync -avz --progress static/images/products/ shoeapp@your-server-ip:/home/shoeapp/Perm_shop/static/images/products/
```

### Вариант 3: Через scp

```bash
# На локальной машине
scp -r static/images/products/* shoeapp@your-server-ip:/home/shoeapp/Perm_shop/static/images/products/
```

### Установка прав доступа после загрузки

```bash
# На сервере
sudo chown -R shoeapp:www-data /home/shoeapp/Perm_shop/static/images
sudo find /home/shoeapp/Perm_shop/static/images -type d -exec chmod 755 {} \;
sudo find /home/shoeapp/Perm_shop/static/images -type f -exec chmod 644 {} \;
```

---

## 📊 Просмотр логов

### Логи приложения

```bash
# В реальном времени
sudo journalctl -u shoeapp -f

# Последние 50 строк
sudo journalctl -u shoeapp -n 50

# За сегодня
sudo journalctl -u shoeapp --since today

# С определенного времени
sudo journalctl -u shoeapp --since "2024-12-25 10:00:00"

# Файловые логи (если настроены)
tail -f /home/shoeapp/Perm_shop/logs/app.log
tail -f /home/shoeapp/Perm_shop/logs/error.log
```

### Логи Nginx

```bash
# Ошибки
sudo tail -f /var/log/nginx/shoeapp_error.log

# Доступы
sudo tail -f /var/log/nginx/shoeapp_access.log

# Поиск ошибок
sudo grep -i error /var/log/nginx/shoeapp_error.log
```

### Системные логи

```bash
# Общие системные логи
sudo journalctl -f

# Логи за последний час
sudo journalctl --since "1 hour ago"
```

---

## ↩️ Откат изменений

### Откат кода через Git

```bash
# 1. Подключись к серверу
ssh shoeapp@your-server-ip

# 2. Перейди в директорию проекта
cd /home/shoeapp/Perm_shop

# 3. Посмотри историю коммитов
git log --oneline -10

# 4. Откатись к нужному коммиту
git reset --hard <commit-hash>

# ИЛИ откатись на N коммитов назад
git reset --hard HEAD~1

# 5. Перезапусти сервис
sudo systemctl restart shoeapp
```

### Откат конфигурации Nginx

```bash
# 1. Проверь историю изменений (если используешь Git для конфигов)
cd /etc/nginx/sites-available
git log shoeapp

# 2. Или используй резервную копию
sudo cp /etc/nginx/sites-available/shoeapp.backup /etc/nginx/sites-available/shoeapp

# 3. Проверь конфигурацию
sudo nginx -t

# 4. Перезагрузи Nginx
sudo systemctl reload nginx
```

---

## 🛠️ Полезные команды

### Проверка состояния системы

```bash
# Загрузка системы
uptime

# Использование диска
df -h

# Использование памяти
free -h

# Активные процессы
top
# или
htop  # если установлен

# Сетевые подключения
ss -tlnp | grep :80
ss -tlnp | grep :443
```

### Проверка работы сайта

```bash
# Проверка доступности
curl -I http://permplanetaobuv.ru
curl -I https://permplanetaobuv.ru

# Проверка health endpoint
curl http://permplanetaobuv.ru/health

# Проверка статических файлов
curl -I http://permplanetaobuv.ru/static/style.css
```

### Проверка прав доступа (одной командой)

```bash
# Проверить все права на проект и статические файлы
echo "=== Права на проект ===" && ls -ld /home/shoeapp/Perm_shop && \
echo "=== Права на static ===" && ls -ld /home/shoeapp/Perm_shop/static && \
echo "=== Права на файлы static ===" && ls -l /home/shoeapp/Perm_shop/static/ | head -5 && \
echo "=== Проверка доступа www-data ===" && sudo -u www-data test -r /home/shoeapp/Perm_shop/static/style.css && echo "✅ www-data может читать файлы" || echo "❌ www-data НЕ может читать файлы" && \
echo "=== Права на БД ===" && ls -l /home/shoeapp/Perm_shop/instance/shop.db 2>/dev/null || echo "БД не найдена"
```

**Или упрощенная версия:**
```bash
# Быстрая проверка прав
ls -ld /home/shoeapp/Perm_shop /home/shoeapp/Perm_shop/static && \
sudo -u www-data test -r /home/shoeapp/Perm_shop/static/style.css && echo "✅ Права OK" || echo "❌ Нужно исправить права"
```

**Если права неправильные, исправить одной командой:**
```bash
sudo chown -R shoeapp:www-data /home/shoeapp/Perm_shop/static && \
sudo find /home/shoeapp/Perm_shop/static -type d -exec chmod 755 {} \; && \
sudo find /home/shoeapp/Perm_shop/static -type f -exec chmod 644 {} \; && \
echo "✅ Права исправлены"
```

### Работа с Git

```bash
# Проверить статус
git status

# Посмотреть изменения
git diff

# Посмотреть последние коммиты
git log --oneline -10

# Проверить удаленные репозитории
git remote -v
```

### Работа с Python окружением

```bash
# Активировать виртуальное окружение
source /home/shoeapp/Perm_shop/.venv/bin/activate

# Проверить установленные пакеты
pip list

# Обновить pip
pip install --upgrade pip

# Установить зависимости
pip install -r requirements.txt
```

---

## 🔧 Решение проблем

### Сайт не открывается

```bash
# 1. Проверь статус сервисов
sudo systemctl status shoeapp
sudo systemctl status nginx

# 2. Проверь логи
sudo journalctl -u shoeapp -n 50
sudo tail -20 /var/log/nginx/shoeapp_error.log

# 3. Проверь порты
ss -tlnp | grep :80
ss -tlnp | grep :8002

# 4. Проверь конфигурацию Nginx
sudo nginx -t
```

### Ошибка 502 Bad Gateway

```bash
# 1. Проверь, запущено ли приложение
sudo systemctl status shoeapp

# 2. Проверь, слушает ли приложение порт 8002
ss -tlnp | grep :8002

# 3. Проверь логи приложения
sudo journalctl -u shoeapp -n 50

# 4. Перезапусти приложение
sudo systemctl restart shoeapp
```

### Ошибка 403 Forbidden (статические файлы)

```bash
# 1. Проверь права доступа
ls -la /home/shoeapp/Perm_shop/static/

# 2. Исправь права
sudo chown -R shoeapp:www-data /home/shoeapp/Perm_shop/static
sudo find /home/shoeapp/Perm_shop/static -type d -exec chmod 755 {} \;
sudo find /home/shoeapp/Perm_shop/static -type f -exec chmod 644 {} \;

# 3. Перезагрузи Nginx
sudo systemctl reload nginx
```

### Ошибка 500 Internal Server Error

```bash
# 1. Проверь логи приложения
sudo journalctl -u shoeapp -n 100

# 2. Проверь логи ошибок
tail -50 /home/shoeapp/Perm_shop/logs/error.log

# 3. Проверь базу данных
ls -la /home/shoeapp/Perm_shop/instance/shop.db

# 4. Проверь права на БД
sudo chown shoeapp:shoeapp /home/shoeapp/Perm_shop/instance/shop.db
sudo chmod 644 /home/shoeapp/Perm_shop/instance/shop.db
```

### Приложение не запускается

```bash
# 1. Проверь логи
sudo journalctl -u shoeapp -n 100

# 2. Попробуй запустить вручную
cd /home/shoeapp/Perm_shop
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8002

# 3. Проверь зависимости
pip install -r requirements.txt

# 4. Проверь переменные окружения
cat /home/shoeapp/Perm_shop/.env
```

### Nginx не перезапускается

```bash
# 1. Проверь конфигурацию
sudo nginx -t

# 2. Если есть ошибки, исправь их в
sudo nano /etc/nginx/sites-available/shoeapp

# 3. Проверь синтаксис снова
sudo nginx -t

# 4. Перезапусти
sudo systemctl restart nginx
```

---

## 📝 Чеклист быстрого деплоя

После добавления новой функции:

- [ ] Закоммитить изменения в Git
- [ ] Запушить в репозиторий (`git push origin main`)
- [ ] Подключиться к серверу
- [ ] Запустить деплой скрипт или выполнить ручной деплой
- [ ] Проверить статус сервиса (`sudo systemctl status shoeapp`)
- [ ] Проверить логи на ошибки (`sudo journalctl -u shoeapp -n 50`)
- [ ] Открыть сайт в браузере и проверить работу новой функции

---

## 🔐 Безопасность

### Регулярные обновления

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Обновить зависимости Python
cd /home/shoeapp/Perm_shop
source .venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### Резервное копирование

```bash
# Настроить автоматические бэкапы БД через cron
crontab -e

# Добавить строку (бэкап каждый день в 3:00)
0 3 * * * /home/shoeapp/Perm_shop/backup_db.sh
```

---

## 📞 Контакты и ресурсы

- **Путь к проекту:** `/home/shoeapp/Perm_shop/`
- **Конфигурация Nginx:** `/etc/nginx/sites-available/shoeapp`
- **Systemd сервис:** `/etc/systemd/system/shoeapp.service`
- **Логи приложения:** `sudo journalctl -u shoeapp`
- **Логи Nginx:** `/var/log/nginx/shoeapp_*.log`

---

**Последнее обновление:** 2024-12-25


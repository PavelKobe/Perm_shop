# Инструкция по развертыванию в продакшн

Пошаговое руководство по деплою сайта на VPS сервер.

## Предварительные требования

- VPS сервер с Ubuntu 22.04 LTS
- Домен, указывающий на IP сервера
- SSH доступ к серверу
- Git репозиторий с кодом проекта

---

## Этап 1: Подготовка сервера

### 1.1 Подключение и обновление

```bash
ssh root@your-server-ip

# Обновление системы
apt update && apt upgrade -y

# Установка базовых пакетов
apt install -y python3.11 python3.11-venv python3-pip nginx git ufw
```

### 1.2 Настройка firewall

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 1.3 Создание пользователя

```bash
adduser shoeapp --disabled-password
usermod -aG sudo shoeapp
su - shoeapp
```

---

## Этап 2: Деплой приложения

### 2.1 Клонирование репозитория

```bash
cd /home/shoeapp
git clone https://github.com/your-username/shoe_store_perm.git
cd shoe_store_perm
```

### 2.2 Настройка виртуального окружения

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Настройка переменных окружения

```bash
cp .env.production.example .env
nano .env  # Отредактировать пароли и настройки
```

**Важно:** Измените `ADMIN_PASSWORD` и `SECRET_KEY` на сильные значения!

### 2.4 Создание директории для логов

```bash
mkdir -p logs
chmod 755 logs
```

### 2.5 Тестовый запуск

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
# Проверить: http://your-server-ip:8002
# Нажать Ctrl+C для остановки
```

---

## Этап 3: Деплой изображений

### Вариант A: Через rsync (рекомендуется)

**На локальной машине (Windows с Git Bash или WSL):**

```bash
# Отредактировать deploy_images.sh: указать SERVER_HOST
bash deploy_images.sh
```

### Вариант B: Через SFTP (WinSCP, FileZilla)

1. Подключиться к серверу
2. Загрузить папку `static/images/products/` в `/home/shoeapp/shoe_store_perm/static/images/`

### 2.6 Установка прав доступа

```bash
chown -R shoeapp:shoeapp /home/shoeapp/shoe_store_perm/static/images
chmod -R 755 /home/shoeapp/shoe_store_perm/static/images
```

---

## Этап 4: Настройка systemd

### 4.1 Создание service файла

```bash
sudo nano /etc/systemd/system/shoeapp.service
```

Скопировать содержимое из `deploy/systemd.service`, заменив пути при необходимости.

### 4.2 Запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable shoeapp
sudo systemctl start shoeapp
sudo systemctl status shoeapp
```

---

## Этап 5: Настройка Nginx

### 5.1 Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/shoeapp
```

Скопировать содержимое из `deploy/nginx.conf`, заменив `your-domain.com` на свой домен.

### 5.2 Активация

```bash
sudo ln -s /etc/nginx/sites-available/shoeapp /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка
sudo systemctl restart nginx
```

---

## Этап 6: SSL сертификат

### 6.1 Установка Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 6.2 Получение сертификата

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot автоматически обновит конфигурацию Nginx и настроит автообновление.

---

## Этап 7: Настройка бэкапов

### 7.1 Установка скрипта

```bash
cp backup_db.sh /home/shoeapp/backup_db.sh
chmod +x /home/shoeapp/backup_db.sh
```

### 7.2 Настройка cron

```bash
crontab -e
# Добавить строку:
0 3 * * * /home/shoeapp/backup_db.sh
```

---

## Этап 8: Настройка ротации логов

```bash
sudo cp deploy/logrotate.conf /etc/logrotate.d/shoeapp
sudo chmod 644 /etc/logrotate.d/shoeapp
```

---

## Этап 9: Автоматизация деплоя

### 9.1 Установка скрипта деплоя

```bash
cp deploy.sh /home/shoeapp/deploy.sh
chmod +x /home/shoeapp/deploy.sh
```

### 9.2 Настройка SSH ключей (на локальной машине)

```bash
ssh-keygen -t ed25519
ssh-copy-id shoeapp@your-server-ip
```

### 9.3 Деплой одной командой

```bash
ssh shoeapp@your-server-ip "bash /home/shoeapp/deploy.sh"
```

---

## Проверка работоспособности

### Чеклист:

- [ ] Сайт открывается по домену: `https://your-domain.com`
- [ ] SSL сертификат работает (зеленый замочек)
- [ ] Админ-панель доступна: `https://your-domain.com/admin/login`
- [ ] Изображения товаров загружаются
- [ ] Модальные окна открываются
- [ ] Поиск и фильтры работают
- [ ] Health check работает: `https://your-domain.com/health`

### Проверка логов

```bash
# Логи приложения
tail -f /home/shoeapp/shoe_store_perm/logs/app.log

# Логи ошибок
tail -f /home/shoeapp/shoe_store_perm/logs/error.log

# Логи Nginx
sudo tail -f /var/log/nginx/shoeapp_access.log
sudo tail -f /var/log/nginx/shoeapp_error.log

# Статус сервиса
sudo systemctl status shoeapp
```

---

## Полезные команды

```bash
# Перезапуск приложения
sudo systemctl restart shoeapp

# Просмотр статуса
sudo systemctl status shoeapp

# Просмотр логов
sudo journalctl -u shoeapp -f

# Проверка конфигурации Nginx
sudo nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx
```

---

## Обновление приложения

После изменений в коде:

```bash
# На сервере
cd /home/shoeapp/shoe_store_perm
bash /home/shoeapp/deploy.sh

# Или с локальной машины
ssh shoeapp@your-server-ip "bash /home/shoeapp/deploy.sh"
```

---

## Обновление изображений

```bash
# С локальной машины
bash deploy_images.sh
```

---

## Мониторинг

Рекомендуется настроить внешний мониторинг:

- **UptimeRobot** (бесплатно): https://uptimerobot.com
- Настроить проверку `https://your-domain.com/health` каждые 5 минут

---

## Оценка стоимости

- **VPS:** 200-500₽/мес (Timeweb) или €4-6/мес (Hetzner)
- **Домен:** 500-1000₽/год
- **SSL:** Бесплатно (Let's Encrypt)
- **Итого:** ~300-600₽/мес

---

## Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u shoeapp -n 50`
2. Проверьте статус сервиса: `sudo systemctl status shoeapp`
3. Проверьте конфигурацию Nginx: `sudo nginx -t`


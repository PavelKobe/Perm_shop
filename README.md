# Женская кожаная обувь — ТЦ «Алмаз», Пермь

Сайт-визитка магазина женской кожаной обуви «Планета Обуви».

**Технологии:** FastAPI + Jinja2 + HTMX + SQLite

---

## 1. Быстрый старт (Development)

```powershell
cd C:\Users\p.kobelev\Perm_ecom\shoe_store_perm
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Запуск сервера

```powershell
# Через батник (рекомендуется):
run_dev.bat

# Или вручную:
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8002
uvicorn app.main:app --reload --log-level info --port 8002
```

Открыть: http://127.0.0.1:8002/

---

## 1.2. Развертывание в продакшн

Подробная инструкция по деплою на VPS сервер находится в файле **[DEPLOY.md](DEPLOY.md)**.

**Краткая сводка:**
- Подготовка проекта: `.gitignore`, `.env.production.example`, скрипты деплоя
- Настройка VPS: Ubuntu 22.04, Python 3.11, Nginx, SSL (Let's Encrypt)
- Автоматизация: systemd service, бэкапы через cron, скрипты деплоя
- Оценка стоимости: ~300-600₽/мес для малого бизнеса

---

## 1.1. Админ-панель

- URL входа: `http://127.0.0.1:8002/admin/login`
- Доступ: логин/пароль берутся из `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`). По умолчанию: `admin` / `admin123`.
- Сессия через cookie, страницы админки не индексируются.

### Быстрый сценарий
1) Открыть `/admin/login`, ввести логин/пароль.  
2) Товары → «Добавить товар». Заполнить: название, категория, подкатегория, цена.  
   - Если указать `Старая цена` > `Цена`, товар появится в «Скидки».  
   - Флаг «Новинка» отправляет товар в блок «Новинки».  
   - Флаг «Актуальный товар» выводит на главной в «Актуальные модели».  
   - Фото загрузится в `static/images/products/{category_slug}/{subcategory_slug}/{slug}.jpg`.  
3) Сохранить. Товар сразу виден в своём разделе и на соответствующих витринах.

### Акции
- Раздел «Акции»: создать/редактировать/удалять, задавать текст скидки и даты.

### Остановка dev-сервера / освобождение порта
- `stop_server.bat` — завершает процесс, занявший порт (по умолчанию 8002) и проверяет, что порт свободен. Можно указать порт: `stop_server.bat 8080`.

---

## 2. Структура проекта

```
shoe_store_perm/
├── app/
│   ├── main.py              # роуты FastAPI
│   ├── models.py            # SQLAlchemy модели
│   ├── database.py          # engine, seed_data
│   ├── seo.py               # sitemap.xml
│   └── templates/
│       ├── base.html        # layout, навигация, footer
│       ├── index.html       # главная
│       ├── category.html    # страница категории (подгруппы)
│       ├── subcategory.html # страница подгруппы (товары)
│       ├── product.html     # карточка товара
│       ├── promotions.html  # акции
│       ├── map.html         # карта + контакты
│       └── partials/
│           └── product_list.html
├── static/
│   ├── style.css
│   └── images/
│       ├── shop/            # фото магазина
│       └── products/        # фото товаров (по категориям)
│           ├── zimnyaya/
│           │   ├── sapogi/
│           │   ├── botinki/
│           │   ├── krossovki/
│           │   └── uggi/
│           ├── demisezon/
│           │   ├── sapogi/
│           │   ├── botinki/
│           │   └── krossovki/
│           └── letnyaya/
│               ├── tufli/
│               ├── krossovki/
│               ├── lofery/
│               ├── bosonozhki/
│               └── mokasiny/
└── instance/
    └── shop.db              # SQLite база
```

---

## 3. Структура базы данных

### Таблицы

| Таблица | Описание |
|---------|----------|
| `categories` | Основные категории: Зимняя, Демисезонная, Летняя |
| `subcategories` | Подгруппы: Сапоги, Ботинки, Угги, Туфли и т.д. |
| `products` | Товары |
| `promotions` | Акции |

### Модели (app/models.py)

```python
class Category(Base):
    id: int (PK)
    name: str              # "Зимняя обувь"
    slug: str              # "zimnyaya"
    icon: str              # "❄️"
    sort_order: int

class Subcategory(Base):
    id: int (PK)
    category_id: int (FK)  # → categories.id
    name: str              # "Сапоги"
    slug: str              # "sapogi"
    sort_order: int

class Product(Base):
    id: int (PK)
    subcategory_id: int (FK)  # → subcategories.id
    name: str
    slug: str
    description: text
    price: float
    old_price: float (nullable)
    sizes_json: str        # JSON: "[36, 37, 38, 39]"
    color: str
    image_url: str         # "/static/images/products/zimnyaya/sapogi/file.jpg"
    is_active: bool
    is_new: bool           # новинка
    is_featured: bool      # актуальный товар
    created_at: datetime
```

### Категории и подгруппы

| Категория (slug) | Подгруппы |
|------------------|-----------|
| zimnyaya | sapogi, botinki, krossovki, uggi |
| demisezon | sapogi, botinki, krossovki |
| letnyaya | tufli, krossovki, lofery, bosonozhki, mokasiny |

---

## 4. Роуты

| URL | Описание |
|-----|----------|
| `/` | Главная страница |
| `/category/{slug}` | Страница категории (zimnyaya, demisezon, letnyaya) |
| `/{category_slug}/{subcategory_slug}` | Страница подгруппы с товарами |
| `/product/{id}-{slug}` | Карточка товара |
| `/promotions` | Акции |
| `/map` | Карта и контакты |
| `/sitemap.xml` | SEO sitemap |
| `/robots.txt` | SEO robots |

### Примеры URL

- `/category/zimnyaya` — все подгруппы зимней обуви
- `/zimnyaya/sapogi` — зимние сапоги
- `/letnyaya/bosonozhki` — летние босоножки
- `/product/5-kozhanye-sapogi-frost-queen` — карточка товара

---

## 5. Как добавить товар

### 5.1. Через Python

```python
from app.database import db_session
from app.models import Product, Subcategory

with db_session() as db:
    # Найти подкатегорию
    subcat = db.query(Subcategory).filter(
        Subcategory.slug == "sapogi",
        Subcategory.category.has(slug="zimnyaya")
    ).first()

    # Создать товар
    product = Product(
        name="Новые зимние сапоги «Winter Star»",
        slug="novye-zimnie-sapogi-winter-star",
        description="Элегантные сапоги из натуральной кожи.",
        price=12500,
        old_price=14900,  # опционально
        sizes_json='[36, 37, 38, 39]',
        color="чёрный",
        image_url="/static/images/products/zimnyaya/sapogi/winter-star.jpg",
        subcategory_id=subcat.id,
        is_new=True,       # новинка
        is_featured=True,  # показывать на главной
    )
    db.add(product)
    db.commit()
    print(f"Товар #{product.id} создан")
```

### 5.2. Через SQLite-клиент

1. Открыть `instance/shop.db` в DBeaver / SQLite Browser
2. Найти `subcategory_id` нужной подгруппы
3. Вставить строку в `products`:
   - `name`, `slug`, `description`, `price`
   - `sizes_json` — JSON массив: `"[36, 37, 38]"`
   - `image_url` — путь к фото
   - `subcategory_id` — FK
   - `is_active = 1`

---

## 6. Как добавить фото товара

1. Положить файл в соответствующую папку:

```
static/images/products/{category_slug}/{subcategory_slug}/{filename}.jpg
```

Пример: `static/images/products/zimnyaya/sapogi/winter-star.jpg`

2. В БД указать путь:

```
/static/images/products/zimnyaya/sapogi/winter-star.jpg
```

### Рекомендации по фото

- Формат: JPG или PNG
- Соотношение: 1:1 (квадрат) — лучше всего для карточек
- Размер: 800×800 px минимум
- Фон: светлый, нейтральный

---

## 7. SEO

### Meta-теги

На каждой странице уникальные `<title>` и `<meta description>` с ключевыми словами:
- «Пермь»
- «кожаная обувь»
- «женская обувь»
- «ТЦ Алмаз»

### Микроразметка Schema.org

- `LocalBusiness` — на всех страницах (footer)
- `Product` — на странице товара
- `BreadcrumbList` — хлебные крошки
- `ItemList` — списки товаров

### sitemap.xml

Автоматически генерируется со всеми:
- категориями
- подгруппами
- товарами
- статическими страницами

Проверить: http://127.0.0.1:8002/sitemap.xml

---

## 8. Контакты магазина

Данные настраиваются в `app/templates/base.html` (footer) и `app/templates/map.html`:

- **Адрес:** г. Пермь, ул. Куйбышева, 37, ТЦ «Алмаз», цокольный этаж
- **Телефон:** +7 (902) 801-85-13
- **Часы работы:** ежедневно 10:00–21:00
- **Координаты:** 58.007726, 56.235221

---

## 9. Чистый старт БД

Если нужно пересоздать базу с нуля:

```python
from app.database import init_db

# Удалить старую БД и создать новую с seed-данными
init_db(force_recreate=True)
```

Или просто удалить файл `instance/shop.db` и перезапустить сервер.

---

## 10. FAQ

**Товар не появляется на сайте:**
- Проверь `is_active = 1` (True)
- Проверь `subcategory_id` — должен ссылаться на существующую подкатегорию

**Картинка не отображается:**
- Путь должен начинаться с `/static/...`
- Файл должен лежать в правильной папке
- Проверь регистр имени файла

**Товар не на главной в «Актуальных»:**
- Установи `is_featured = True`

**Товар не помечен как новинка:**
- Установи `is_new = True`

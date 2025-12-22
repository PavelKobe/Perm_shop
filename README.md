# Отдел женской кожаной обуви в ТЦ «Карнавал» (сайт‑визитка)

Серверный рендер на FastAPI + Jinja2 + SQLite. Страницы:
- Главная `/`
- Товары `/products`
- Акции `/promotions`
- Карта `/map`
- Карточка товара `/product/{id}-{slug}`

БД: `instance/shop.db` (SQLite).

---

## 1. Установка и запуск

cd C:\Users\p.kobelev\Perm_ecom\shoe_store_perm
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txtИнициализация (сидинг выполняется автоматически при старте, отдельный `init_db.py` не нужен).

### Запуск сервера

Рекомендуемый способ — через батник:

run_dev.batОн:
- активирует `.venv`,
- при необходимости ставит зависимости,
- запускает `uvicorn app.main:app --reload --port 8002`,
- открывает `http://127.0.0.1:8002/`.

Ручной запуск:

.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8002---

## 2. Где хранится что

- **Бэкенд**: `app/main.py`, `app/database.py`, `app/models.py`, `app/seo.py`
- **Шаблоны**: `app/templates/`
  - `base.html` — общий layout и меню
  - `index.html` — главная
  - `products.html` — список товаров (зима/демисезон)
  - `promotions.html` — акции
  - `map.html` — карта + контакты (LocalBusiness)
  - `product.html` — карточка товара
  - `partials/product_list.html` — сетка карточек для списков
- **Статика**:
  - `static/style.css` — стили
  - `static/images/products/` — фото товаров
- **База**:
  - `instance/shop.db` — SQLite
  - схема и сидинг — `app/database.py`
  - модели — `app/models.py`

---

## 3. Как добавить новый товар

### 3.1. Структура модели `Product`

`app/models.py`:

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    size = Column(String(32), nullable=True)
    color = Column(String(64), nullable=True)
    image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")`Category.slug` важные значения:
- `zhenskaya-zimnyaya-obuv` — зимняя женская обувь
- `zhenskaya-demisezonnyaya-obuv` — демисезонная женская обувь
- `obuv-so-skidkoy` — обувь со скидкой
- `novinki` — новинки

### 3.2. Добавление товара через Python-скрипт

Создай, например, `scripts/add_product.py` (или разово используй `python -i`):

from app.database import SessionLocal
from app.models import Product, Category

db = SessionLocal()

winter = db.query(Category).filter(Category.slug == "zhenskaya-zimnyaya-obuv").first()

product = Product(
    name="Новые зимние ботинки «Snow Line»",
    slug="novye-zimnie-botinki-snow-line",
    description="Зимние ботинки из натуральной кожи с мягким мехом.",
    price=9900,
    old_price=11900,
    size="38",
    color="черный",
    image_url="/static/images/products/novye-zimnie-botinki-snow-line.jpg",
    category_id=winter.id if winter else None,
)

db.add(product)
db.commit()
db.refresh(product)
print(product.id)
db.close()Запуск:

.\.venv\Scripts\activate
python -i
>>> from scripts.add_product import *  # или просто скопировать код в интерактивПосле этого:
- товар появится на `/products` в соответствующем блоке,
- карточка откроется по `/product/{id}-{slug}` (id тот, что вывел `print`).

### 3.3. Добавление товара через любой SQLite-клиент

1. Открой `instance/shop.db` в:
   - DBeaver / SQLite Browser / DataGrip / VSCode SQLite расширение.
2. В таблице `categories` посмотри `id` нужной категории (зима/демисезон/скидки/новинки).
3. Вставь строку в `products`:
   - `name`, `slug`, `description`, `price`, `old_price` (опционально),
   - `size`, `color` (опционально),
   - `image_url` — строка вида `/static/images/products/<имя_файла>.jpg`,
   - `is_active` = 1,
   - `category_id` = `id` из `categories`.

---

## 4. Как добавить фото товара

1. Подготовь JPG/PNG (желательно 3:4 или 4:5, чтобы красиво влезло).
2. Положи файл в:

static/images/products/<имя_файла>.jpg3. В `image_url` у товара укажи:

/static/images/products/<имя_файла>.jpgНапример:

image_url="/static/images/products/zimnie-botinki-oslo.jpg"Карточки:
- На странице `/products`: берется `product.image_url` и кладётся в `<img src="{{ product.image_url }}">`.
- На странице товара `/product/{id}-{slug}` — то же самое.

---

## 5. Как добавить/изменить координаты и данные магазина (страница «Карта»)

Страница `Карта`: `app/templates/map.html`.

Там уже есть микроразметка `LocalBusiness`:

<section
  class="section"
  itemscope
  itemtype="https://schema.org/LocalBusiness"
>
  <h1 itemprop="name">Отдел женской кожаной обуви в ТЦ «Карнавал»</h1>
  <p itemprop="description">
    Отдел по продаже женской кожаной обуви в торговом центре «Карнавал» в Перми. Зимняя и демисезонная обувь из
    натуральной кожи.
  </p>

  <div class="contact-grid">
    <div class="contact-info">
      <h2>Контакты</h2>
      <p>
        <span itemprop="address" itemscope itemtype="https://schema.org/PostalAddress">
          <span itemprop="addressLocality">г. Пермь</span>,
          <span itemprop="streetAddress">ул. Ленина, ТЦ «Карнавал»</span>
        </span>
      </p>
      <p>
        Телефон:
        <a href="tel:+73422000000" itemprop="telephone">+7 (342) 200-00-00</a>
      </p>
      <p>
        Часы работы:
        <span itemprop="openingHours" content="Mo-Su 10:00-21:00">ежедневно 10:00–21:00</span>
      </p>
    </div>

    <div class="map-wrapper" itemprop="geo" itemscope itemtype="https://schema.org/GeoCoordinates">
      <meta itemprop="latitude" content="57.948015" />
      <meta itemprop="longitude" content="56.234821" />
      <div class="map-embed">
        <iframe
          src="https://yandex.ru/map-widget/v1/?text=Карнавал, Пермь&amp;z=17&amp;l=map"
          width="100%"
          height="320"
          frameborder="0"
          loading="lazy"
        ></iframe>
      </div>
    </div>
  </div>
</section>### 5.1. Меняем адрес

Редактируй текст внутри `streetAddress` и `addressLocality`:
- `г. Пермь` → другой город (если нужно),
- `ул. Ленина, ТЦ «Карнавал»` → твой фактический адрес/этаж/секция.

### 5.2. Обновляем телефон

В `href` и `itemprop="telephone"`:

<a href="tel:+7XXXXXXXXXX" itemprop="telephone">+7 (...) ...-..-..</a>### 5.3. Меняем часы работы

- Машинно-читаемый формат в `content`:
  - Примеры: `Mo-Fr 10:00-20:00`, `Mo-Su 10:00-21:00`.
- Человеческий текст — внутри тега.

---

## 6. Как поменять карту и координаты

1. Зайди в конструктор Яндекс.Карт.
2. Найди адрес «г. Пермь, ул. Ленина, 50» или свой реальный.
3. Сгенерируй iframe-код.
4. Замени `src` внутри `<iframe>` в `map.html` на выданный Яндексом.

Координаты (для микроразметки):

<meta itemprop="latitude" content="58.0105" />
<meta itemprop="longitude" content="56.2502" />- Поменяй на фактические (их можно посмотреть в Яндекс.Картах — ПКМ по точке → «Что здесь?» и взять широту/долготу).

---

## 7. Фото отдела / обложка на главной

Сейчас на главной (`index.html` и `products.html`) в блоке `.hero-photo` просто:

<div class="hero-photo">
  <div class="hero-photo-placeholder"></div>
</div>Чтобы показать реальное фото отдела:

1. Положи фото, например:

static/images/shop/front.jpg2. В `index.html` (и при желании в `products.html`) замени `hero-photo-placeholder` на `<img>`:

<div class="hero-photo">
  <img
    src="/static/images/shop/front.jpg"
    alt="Отдел женской кожаной обуви в ТЦ «Карнавал»"
    class="hero-photo-img"
  />
</div>3. Добавь немного стилей в `static/style.css`, если хочешь:

.hero-photo-img {
  width: 100%;
  border-radius: 16px;
  object-fit: cover;
}---

## 8. FAQ по изменениям

- **Товар не появился на `/products`**:
  - проверь `is_active = 1`,
  - `category_id` должен ссылаться на одну из категорий (зима/демисезон/скидка/новинки),
  - перезапусти `uvicorn` (на dev он и так подхватывает изменения, но для БД не нужно — сразу видно).
- **Картинка не показывается**:
  - путь в БД должен начинаться с `/static/...`,
  - файл физически лежит в `static/images/products/`,
  - проверь регистр имени файла (Windows не чувствителен, но лучше единообразно).
- **Карта не обновилась**:
  - проверь, что `src` iframe реально ведёт на Яндекс, без дополнительных экранирований,
  - иногда кэш — попробуй в инкогнито.

Этого достаточно, чтобы без админки и API руками поддерживать сайт‑визитку: добавлять/править товары, фото и координаты/карту.
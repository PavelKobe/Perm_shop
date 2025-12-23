from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = INSTANCE_DIR / "shop.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db(force_recreate: bool = False) -> None:
    """Инициализация БД. force_recreate=True удалит старую БД и создаст заново."""
    from .models import Category, Subcategory, Product, Promotion  # noqa: F401

    if force_recreate and DB_PATH.exists():
        DB_PATH.unlink()

    # Проверяем, нужно ли пересоздать схему (если таблица subcategories не существует)
    needs_recreate = False
    if DB_PATH.exists():
        with engine.begin() as conn:
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='subcategories'")
            if result.fetchone() is None:
                needs_recreate = True

    if needs_recreate:
        # Удаляем старую БД и пересоздаём
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    with db_session() as db:
        seed_initial_data(db)


def seed_initial_data(db: Session) -> None:
    """Сид с категориями, подгруппами и демо-товарами."""
    from datetime import date
    from .models import Category, Subcategory, Product, Promotion

    # Если категории уже есть — не пересоздаём
    if db.query(Category).count() > 0:
        return

    # === КАТЕГОРИИ ===
    categories_data = [
        {"name": "Зимняя обувь", "slug": "zimnyaya", "icon": "❄️", "sort_order": 1},
        {"name": "Демисезонная обувь", "slug": "demisezon", "icon": "🍂", "sort_order": 2},
        {"name": "Летняя обувь", "slug": "letnyaya", "icon": "☀️", "sort_order": 3},
    ]

    categories = {}
    for cat_data in categories_data:
        cat = Category(**cat_data)
        db.add(cat)
        db.flush()
        categories[cat.slug] = cat

    # === ПОДГРУППЫ ===
    subcategories_data = [
        # Зимняя
        {"name": "Сапоги", "slug": "sapogi", "category_slug": "zimnyaya", "sort_order": 1},
        {"name": "Ботинки", "slug": "botinki", "category_slug": "zimnyaya", "sort_order": 2},
        {"name": "Кроссовки", "slug": "krossovki", "category_slug": "zimnyaya", "sort_order": 3},
        {"name": "Угги", "slug": "uggi", "category_slug": "zimnyaya", "sort_order": 4},
        # Демисезонная
        {"name": "Сапоги", "slug": "sapogi", "category_slug": "demisezon", "sort_order": 1},
        {"name": "Ботинки", "slug": "botinki", "category_slug": "demisezon", "sort_order": 2},
        {"name": "Кроссовки", "slug": "krossovki", "category_slug": "demisezon", "sort_order": 3},
        # Летняя
        {"name": "Туфли", "slug": "tufli", "category_slug": "letnyaya", "sort_order": 1},
        {"name": "Кроссовки и кеды", "slug": "krossovki", "category_slug": "letnyaya", "sort_order": 2},
        {"name": "Лоферы", "slug": "lofery", "category_slug": "letnyaya", "sort_order": 3},
        {"name": "Босоножки", "slug": "bosonozhki", "category_slug": "letnyaya", "sort_order": 4},
        {"name": "Мокасины и балетки", "slug": "mokasiny", "category_slug": "letnyaya", "sort_order": 5},
    ]

    subcategories = {}
    for sub_data in subcategories_data:
        cat_slug = sub_data.pop("category_slug")
        sub = Subcategory(category_id=categories[cat_slug].id, **sub_data)
        db.add(sub)
        db.flush()
        # Ключ = category_slug + subcategory_slug для уникальности
        subcategories[f"{cat_slug}/{sub.slug}"] = sub

    # === ДЕМО-ТОВАРЫ ===
    products_data = [
        # Зимняя → Сапоги
        {
            "name": "Высокие зимние сапоги «Nordic»",
            "slug": "vysokie-zimnie-sapogi-nordic",
            "description": "Высокие сапоги из гладкой кожи с утеплённой подкладкой, вдохновлённые скандинавским стилем.",
            "price": 11900, "old_price": 13400,
            "sizes_json": "[36, 37, 38, 39, 40]", "color": "шоколадный",
            "image_url": "/static/images/products/zimnyaya/sapogi/vysokie-zimnie-sapogi-nordic.jpg",
            "subcategory_key": "zimnyaya/sapogi", "is_featured": True,
        },
        {
            "name": "Кожаные сапоги «Frost Queen»",
            "slug": "kozhanye-sapogi-frost-queen",
            "description": "Элегантные зимние сапоги на устойчивом каблуке с натуральным мехом внутри.",
            "price": 12500, "old_price": None,
            "sizes_json": "[37, 38, 39]", "color": "чёрный",
            "image_url": "/static/images/products/zimnyaya/sapogi/kozhanye-sapogi-frost-queen.jpg",
            "subcategory_key": "zimnyaya/sapogi", "is_new": True,
        },
        # Зимняя → Ботинки
        {
            "name": "Зимние кожаные ботинки на меху",
            "slug": "zimnie-kozhanye-botinki-na-mekhu",
            "description": "Тёплые женские ботинки из натуральной кожи с мехом, устойчивой подошвой и хорошим сцеплением на льду.",
            "price": 8900, "old_price": None,
            "sizes_json": "[36, 37, 38, 39]", "color": "чёрный",
            "image_url": "/static/images/products/zimnyaya/botinki/zimnie-kozhanye-botinki-na-mekhu.jpg",
            "subcategory_key": "zimnyaya/botinki", "is_featured": True,
        },
        {
            "name": "Зимние ботинки на шнуровке «Oslo»",
            "slug": "zimnie-botinki-oslo",
            "description": "Универсальные кожаные ботинки на шнуровке с теплой подкладкой и рельефной подошвой.",
            "price": 9800, "old_price": None,
            "sizes_json": "[37, 38, 39, 40]", "color": "тёмный графит",
            "image_url": "/static/images/products/zimnyaya/botinki/zimnie-botinki-oslo.jpg",
            "subcategory_key": "zimnyaya/botinki",
        },
        # Зимняя → Угги
        {
            "name": "Угги из натуральной овчины",
            "slug": "uggi-iz-naturalnoy-ovchiny",
            "description": "Классические угги из натуральной овчины — максимальное тепло и комфорт.",
            "price": 7500, "old_price": 8900,
            "sizes_json": "[36, 37, 38, 39, 40]", "color": "песочный",
            "image_url": "/static/images/products/zimnyaya/uggi/uggi-iz-naturalnoy-ovchiny.jpg",
            "subcategory_key": "zimnyaya/uggi",
        },
        # Демисезонная → Сапоги
        {
            "name": "Демисезонные сапоги «City Elegance»",
            "slug": "demisezonnye-sapogi-city-elegance",
            "description": "Стильные демисезонные сапоги из мягкой кожи на низком каблуке.",
            "price": 10500, "old_price": None,
            "sizes_json": "[36, 37, 38, 39]", "color": "коричневый",
            "image_url": "/static/images/products/demisezon/sapogi/demisezonnye-sapogi-city-elegance.jpg",
            "subcategory_key": "demisezon/sapogi", "is_new": True,
        },
        # Демисезонная → Ботинки
        {
            "name": "Демисезонные ботинки «City Walk»",
            "slug": "demisezonnye-botinki-city-walk",
            "description": "Городские ботинки из мягкой кожи на низком каблуке для повседневной носки.",
            "price": 8600, "old_price": None,
            "sizes_json": "[36, 37, 38, 39]", "color": "чёрный",
            "image_url": "/static/images/products/demisezon/botinki/demisezonnye-botinki-city-walk.jpg",
            "subcategory_key": "demisezon/botinki", "is_featured": True,
        },
        {
            "name": "Кожаные ботильоны «Autumn»",
            "slug": "kozhanye-botilony-autumn",
            "description": "Элегантные ботильоны из гладкой кожи на среднем каблуке.",
            "price": 9200, "old_price": 10500,
            "sizes_json": "[37, 38, 39]", "color": "бордовый",
            "image_url": "/static/images/products/demisezon/botinki/kozhanye-botilony-autumn.jpg",
            "subcategory_key": "demisezon/botinki",
        },
        # Демисезонная → Кроссовки
        {
            "name": "Кожаные кеды «Soft Line»",
            "slug": "kozhanye-kedy-soft-line",
            "description": "Лёгкие демисезонные кеды из мягкой кожи с минималистичным дизайном.",
            "price": 7900, "old_price": 8900,
            "sizes_json": "[36, 37, 38, 39, 40]", "color": "молочный",
            "image_url": "/static/images/products/demisezon/krossovki/kozhanye-kedy-soft-line.jpg",
            "subcategory_key": "demisezon/krossovki",
        },
        # Летняя → Туфли
        {
            "name": "Кожаные лодочки «Classic»",
            "slug": "kozhanye-lodochki-classic",
            "description": "Классические лодочки из натуральной кожи на среднем каблуке.",
            "price": 6900, "old_price": 7900,
            "sizes_json": "[36, 37, 38, 39]", "color": "чёрный",
            "image_url": "/static/images/products/letnyaya/tufli/kozhanye-lodochki-classic.jpg",
            "subcategory_key": "letnyaya/tufli",
        },
        # Летняя → Лоферы
        {
            "name": "Демисезонные кожаные лоферы",
            "slug": "demisezonnye-kozhanye-lofery",
            "description": "Универсальные кожаные лоферы под джинсы и платье.",
            "price": 7400, "old_price": 8200,
            "sizes_json": "[36, 37, 38, 39]", "color": "капучино",
            "image_url": "/static/images/products/letnyaya/lofery/demisezonnye-kozhanye-lofery.jpg",
            "subcategory_key": "letnyaya/lofery", "is_featured": True,
        },
        # Летняя → Босоножки
        {
            "name": "Кожаные босоножки «Summer Breeze»",
            "slug": "kozhanye-bosonozhki-summer-breeze",
            "description": "Лёгкие босоножки из натуральной кожи с удобной колодкой.",
            "price": 5900, "old_price": None,
            "sizes_json": "[36, 37, 38, 39, 40]", "color": "бежевый",
            "image_url": "/static/images/products/letnyaya/bosonozhki/kozhanye-bosonozhki-summer-breeze.jpg",
            "subcategory_key": "letnyaya/bosonozhki", "is_new": True,
        },
        # Летняя → Мокасины и балетки
        {
            "name": "Кожаные балетки «Comfort»",
            "slug": "kozhanye-baletki-comfort",
            "description": "Мягкие балетки из натуральной кожи на плоской подошве.",
            "price": 4900, "old_price": 5900,
            "sizes_json": "[36, 37, 38, 39]", "color": "пудровый",
            "image_url": "/static/images/products/letnyaya/mokasiny/kozhanye-baletki-comfort.jpg",
            "subcategory_key": "letnyaya/mokasiny",
        },
    ]

    for prod_data in products_data:
        subcat_key = prod_data.pop("subcategory_key")
        is_new = prod_data.pop("is_new", False)
        is_featured = prod_data.pop("is_featured", False)
        product = Product(
            subcategory_id=subcategories[subcat_key].id,
            is_new=is_new,
            is_featured=is_featured,
            **prod_data
        )
        db.add(product)

    # === АКЦИИ ===
    promotions = [
        Promotion(
            title="Скидка на вторую пару",
            slug="skidka-na-vtoruyu-paru",
            description="При покупке двух пар демисезонной обуви — скидка 20% на вторую.",
            discount_text="-20% на вторую пару",
            start_date=date.today(),
            end_date=None,
            is_active=True,
        ),
        Promotion(
            title="Зимняя распродажа",
            slug="zimnyaya-rasprodazha",
            description="Скидки до 30% на зимнюю коллекцию прошлого сезона.",
            discount_text="до -30%",
            start_date=date.today(),
            end_date=None,
            is_active=True,
        ),
    ]
    db.add_all(promotions)

    db.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

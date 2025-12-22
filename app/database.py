from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterator
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

NEW_DB_PATH = INSTANCE_DIR / "shop.db"
OLD_DB_PATH = BASE_DIR / "shoe_store.db"

# Мягкая миграция: если старый файл БД существует, а новый ещё нет — переносим
if OLD_DB_PATH.exists() and not NEW_DB_PATH.exists():
    shutil.move(str(OLD_DB_PATH), str(NEW_DB_PATH))

SQLALCHEMY_DATABASE_URL = f"sqlite:///{NEW_DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    from .models import Category, Product  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_product_columns()

    with db_session() as db:
        seed_initial_data(db)


def _ensure_product_columns() -> None:
    # Лёгкая миграция для SQLite: добавляем size/color, если их ещё нет
    with engine.begin() as conn:
        result = conn.exec_driver_sql("PRAGMA table_info('products')")
        existing_cols = {row[1] for row in result}
        if "size" not in existing_cols:
            conn.exec_driver_sql("ALTER TABLE products ADD COLUMN size VARCHAR(32)")
        if "color" not in existing_cols:
            conn.exec_driver_sql("ALTER TABLE products ADD COLUMN color VARCHAR(64)")


def seed_initial_data(db: Session) -> None:
    from datetime import date

    from .models import Category, Product, Promotion

    if db.query(Category).count() == 0:
        categories = [
            Category(name="Главная", slug="glavnaya"),
            Category(name="Женская зимняя обувь", slug="zhenskaya-zimnyaya-obuv"),
            Category(name="Женская демисезонная обувь", slug="zhenskaya-demisezonnyaya-obuv"),
            Category(name="Обувь со скидкой", slug="obuv-so-skidkoy"),
            Category(name="Новинки", slug="novinki"),
        ]
        db.add_all(categories)
        db.commit()

    # Простые демо-товары, если их ещё нет
    if db.query(Product).count() == 0:
        winter = db.query(Category).filter(Category.slug == "zhenskaya-zimnyaya-obuv").first()
        demi = db.query(Category).filter(Category.slug == "zhenskaya-demisezonnyaya-obuv").first()
        sale = db.query(Category).filter(Category.slug == "obuv-so-skidkoy").first()
        new_cat = db.query(Category).filter(Category.slug == "novinki").first()

        demo_products = [
            Product(
                name="Зимние кожаные ботинки на меху",
                slug="zimnie-kozhanye-botinki-na-mekhu",
                description="Тёплые женские ботинки из натуральной кожи с мехом, устойчивой подошвой и хорошим сцеплением на льду.",
                price=8900,
                old_price=None,
                size="37",
                color="черный",
                image_url="/static/images/products/zimnie-kozhanye-botinki-na-mekhu.jpg",
                category_id=winter.id if winter else None,
            ),
            Product(
                name="Высокие зимние сапоги «Nordic»",
                slug="vysokie-zimnie-sapogi-nordic",
                description="Высокие сапоги из гладкой кожи с утеплённой подкладкой, вдохновлённые скандинавским стилем.",
                price=11900,
                old_price=13400,
                size="38",
                color="шоколадный",
                image_url="/static/images/products/vysokie-zimnie-sapogi-nordic.jpg",
                category_id=winter.id if winter else None,
            ),
            Product(
                name="Зимние ботинки на шнуровке «Oslo»",
                slug="zimnie-botinki-oslo",
                description="Универсальные кожаные ботинки на шнуровке с теплой подкладкой и рельефной подошвой.",
                price=9800,
                old_price=None,
                size="39",
                color="темный графит",
                image_url="/static/images/products/zimnie-botinki-oslo.jpg",
                category_id=winter.id if winter else None,
            ),
            Product(
                name="Демисезонные кожаные лоферы",
                slug="demisezonnye-kozhanye-lofery",
                description="Универсальные кожаные лоферы под джинсы и платье.",
                price=7400,
                old_price=8200,
                size="38",
                color="капучино",
                image_url="/static/images/products/demisezonnye-kozhanye-lofery.jpg",
                category_id=demi.id if demi else None,
            ),
            Product(
                name="Демисезонные ботинки «City Walk»",
                slug="demisezonnye-botinki-city-walk",
                description="Городские ботинки из мягкой кожи на низком каблуке для повседневной носки.",
                price=8600,
                old_price=None,
                size="37",
                color="чёрный",
                image_url="/static/images/products/demisezonnye-botinki-city-walk.jpg",
                category_id=demi.id if demi else None,
            ),
            Product(
                name="Кожаные кеды «Soft Line»",
                slug="kozhanye-kedy-soft-line",
                description="Лёгкие демисезонные кеды из мягкой кожи с минималистичным дизайном.",
                price=7900,
                old_price=8900,
                size="39",
                color="молочный",
                image_url="/static/images/products/kozhanye-kedy-soft-line.jpg",
                category_id=demi.id if demi else None,
            ),
            Product(
                name="Кожаные ботильоны со скидкой",
                slug="kozhanye-botilony-so-skidkoy",
                description="Стильные ботильоны из гладкой кожи из прошлой коллекции по выгодной цене.",
                price=6900,
                old_price=9900,
                size="39",
                color="бордовый",
                image_url="/static/images/products/kozhanye-botilony-so-skidkoy.jpg",
                category_id=sale.id if sale else None,
            ),
            Product(
                name="Кожаные лодочки «Classic Sale»",
                slug="kozhanye-lodochki-classic-sale",
                description="Классические лодочки из натуральной кожи, ограниченная партия со скидкой.",
                price=5400,
                old_price=7900,
                size="37",
                color="чёрный",
                image_url="/static/images/products/kozhanye-lodochki-classic-sale.jpg",
                category_id=sale.id if sale else None,
            ),
            Product(
                name="Новые кожаные сапоги",
                slug="novye-kozhanye-sapogi",
                description="Высокие сапоги из мягкой кожи — новинка сезона.",
                price=11500,
                old_price=None,
                size="37",
                color="темно-коричневый",
                image_url="/static/images/products/novye-kozhanye-sapogi.jpg",
                category_id=new_cat.id if new_cat else None,
            ),
            Product(
                name="Кожаные ботинки «Urban Nova»",
                slug="kozhanye-botinki-urban-nova",
                description="Современные кожаные ботинки с аккуратным силуэтом, идеально для города.",
                price=10200,
                old_price=None,
                size="38",
                color="карамель",
                image_url="/static/images/products/kozhanye-botinki-urban-nova.jpg",
                category_id=new_cat.id if new_cat else None,
            ),
        ]
        db.add_all(demo_products)
        db.commit()

    # Базовая акция
    if db.query(Promotion).count() == 0:
        promo = Promotion(
            title="Скидка на вторую пару",
            slug="skidka-na-vtoruyu-paru",
            description="При покупке двух пар демисезонной обуви — скидка 20% на вторую.",
            discount_text="-20% на вторую пару демисезонной обуви",
            start_date=date.today(),
            end_date=None,
            is_active=True,
        )
        db.add(promo)
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

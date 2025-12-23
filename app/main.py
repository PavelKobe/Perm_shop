import json
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from .database import get_db, init_db
from .models import Category, Subcategory, Product, Promotion
from .seo import generate_sitemap_xml


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Женская кожаная обувь в Перми — ТЦ «Алмаз»")

static_dir = BASE_DIR.parent / "static"
templates_dir = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# Jinja2 фильтр для парсинга JSON размеров
def parse_sizes(sizes_json: str | None) -> List[int]:
    if not sizes_json:
        return []
    try:
        return json.loads(sizes_json)
    except (json.JSONDecodeError, TypeError):
        return []


templates.env.filters["parse_sizes"] = parse_sizes


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# =============================================================================
# ГЛАВНАЯ
# =============================================================================
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    categories = (
        db.query(Category)
        .options(joinedload(Category.subcategories))
        .order_by(Category.sort_order)
        .all()
    )

    # Актуальные товары (is_featured) и новинки (is_new)
    featured_products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.is_featured.is_(True))
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )

    new_products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.is_new.is_(True))
        .order_by(Product.created_at.desc())
        .limit(4)
        .all()
    )

    # Активные акции для баннера
    promotions = (
        db.query(Promotion)
        .filter(Promotion.is_active.is_(True))
        .order_by(Promotion.start_date.desc())
        .limit(1)
        .all()
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": categories,
            "featured_products": featured_products,
            "new_products": new_products,
            "promotions": promotions,
            "page_title": "Женская кожаная обувь в Перми — ТЦ «Алмаз»",
            "meta_description": "Магазин женской кожаной обуви в Перми. Зимняя, демисезонная и летняя обувь из натуральной кожи. ТЦ «Алмаз», ул. Куйбышева, 37.",
        },
    )


# =============================================================================
# СТРАНИЦА КАТЕГОРИИ (список подгрупп)
# =============================================================================
@app.get("/category/{slug}", response_class=HTMLResponse)
def read_category(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    category = (
        db.query(Category)
        .options(joinedload(Category.subcategories))
        .filter(Category.slug == slug)
        .first()
    )

    if category is None:
        categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "categories": categories,
                "featured_products": [],
                "new_products": [],
                "page_title": "Категория не найдена — ТЦ «Алмаз»",
            },
            status_code=404,
        )

    # Все категории для навигации
    all_categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()

    # Хлебные крошки
    breadcrumbs = [
        {"name": "Главная", "url": "/"},
        {"name": category.name, "url": f"/category/{category.slug}"},
    ]

    return templates.TemplateResponse(
        "category.html",
        {
            "request": request,
            "categories": all_categories,
            "category": category,
            "breadcrumbs": breadcrumbs,
            "page_title": f"{category.name} из кожи — купить в Перми | ТЦ «Алмаз»",
            "meta_description": f"{category.name} из натуральной кожи в Перми. Большой выбор моделей в ТЦ «Алмаз». Примерка на месте.",
        },
    )


# =============================================================================
# СТРАНИЦА ПОДГРУППЫ (сетка товаров)
# =============================================================================
@app.get("/{category_slug}/{subcategory_slug}", response_class=HTMLResponse)
def read_subcategory(
    category_slug: str,
    subcategory_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    category = db.query(Category).filter(Category.slug == category_slug).first()
    if category is None:
        return _not_found_response(request, db)

    subcategory = (
        db.query(Subcategory)
        .filter(Subcategory.category_id == category.id, Subcategory.slug == subcategory_slug)
        .first()
    )
    if subcategory is None:
        return _not_found_response(request, db)

    # Все категории для навигации
    all_categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()

    # Товары подгруппы
    products = (
        db.query(Product)
        .filter(Product.subcategory_id == subcategory.id, Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
        .all()
    )

    # Хлебные крошки
    breadcrumbs = [
        {"name": "Главная", "url": "/"},
        {"name": category.name, "url": f"/category/{category.slug}"},
        {"name": subcategory.name, "url": f"/{category.slug}/{subcategory.slug}"},
    ]

    # Формируем название для SEO
    season_map = {
        "zimnyaya": "Зимние",
        "demisezon": "Демисезонные",
        "letnyaya": "Летние",
    }
    season_prefix = season_map.get(category.slug, "")
    seo_title = f"{season_prefix} {subcategory.name.lower()} из кожи — Пермь | ТЦ «Алмаз»"

    return templates.TemplateResponse(
        "subcategory.html",
        {
            "request": request,
            "categories": all_categories,
            "category": category,
            "subcategory": subcategory,
            "products": products,
            "breadcrumbs": breadcrumbs,
            "page_title": seo_title,
            "meta_description": f"{season_prefix} {subcategory.name.lower()} из натуральной кожи. Купить в Перми, ТЦ «Алмаз». Примерка на месте.",
        },
    )


# =============================================================================
# СТРАНИЦА ТОВАРА
# =============================================================================
@app.get("/product/{product_id}-{slug}", response_class=HTMLResponse)
def read_product(
    product_id: int,
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    product = (
        db.query(Product)
        .options(joinedload(Product.subcategory).joinedload(Subcategory.category))
        .filter(Product.id == product_id, Product.slug == slug, Product.is_active.is_(True))
        .first()
    )

    if product is None:
        return _not_found_response(request, db)

    # Все категории для навигации
    all_categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()

    # Хлебные крошки
    breadcrumbs = [{"name": "Главная", "url": "/"}]
    if product.subcategory and product.subcategory.category:
        cat = product.subcategory.category
        subcat = product.subcategory
        breadcrumbs.append({"name": cat.name, "url": f"/category/{cat.slug}"})
        breadcrumbs.append({"name": subcat.name, "url": f"/{cat.slug}/{subcat.slug}"})
    breadcrumbs.append({"name": product.name, "url": f"/product/{product.id}-{product.slug}"})

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "categories": all_categories,
            "product": product,
            "breadcrumbs": breadcrumbs,
            "page_title": f"{product.name} — {int(product.price)} ₽ | ТЦ «Алмаз», Пермь",
            "meta_description": product.description[:160] if product.description else f"{product.name} из натуральной кожи. Купить в Перми.",
        },
    )


# =============================================================================
# АКЦИИ
# =============================================================================
@app.get("/promotions", response_class=HTMLResponse)
def promotions_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    all_categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()

    promotions: List[Promotion] = (
        db.query(Promotion)
        .filter(Promotion.is_active.is_(True))
        .order_by(Promotion.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "promotions.html",
        {
            "request": request,
            "categories": all_categories,
            "promotions": promotions,
            "page_title": "Акции и скидки — женская кожаная обувь | ТЦ «Алмаз», Пермь",
            "meta_description": "Актуальные акции и скидки на женскую кожаную обувь в Перми. ТЦ «Алмаз».",
        },
    )


# =============================================================================
# КАРТА
# =============================================================================
@app.get("/map", response_class=HTMLResponse)
def map_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    all_categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()

    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "categories": all_categories,
            "page_title": "Как нас найти — ТЦ «Алмаз», Куйбышева 37, Пермь",
            "meta_description": "Адрес магазина женской кожаной обуви в Перми: ТЦ «Алмаз», ул. Куйбышева, 37, цокольный этаж. Карта проезда.",
        },
    )


# =============================================================================
# HTMX: ТОВАРЫ ПО ПОДГРУППЕ
# =============================================================================
@app.get("/hx/products/{subcategory_slug}", response_class=HTMLResponse)
def hx_products_by_subcategory(
    subcategory_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    subcategory = db.query(Subcategory).filter(Subcategory.slug == subcategory_slug).first()

    if subcategory:
        products = (
            db.query(Product)
            .filter(Product.subcategory_id == subcategory.id, Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
            .all()
        )
    else:
        products = []

    return templates.TemplateResponse(
        "partials/product_list.html",
        {"request": request, "products": products},
    )


@app.get("/hx/products/featured", response_class=HTMLResponse)
def hx_featured_products(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.is_featured.is_(True))
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "partials/product_list.html",
        {"request": request, "products": products},
    )


@app.get("/hx/products/new", response_class=HTMLResponse)
def hx_new_products(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.is_new.is_(True))
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "partials/product_list.html",
        {"request": request, "products": products},
    )


@app.get("/hx/products/sale", response_class=HTMLResponse)
def hx_sale_products(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.old_price.isnot(None))
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "partials/product_list.html",
        {"request": request, "products": products},
    )


# =============================================================================
# SEO: ROBOTS.TXT, SITEMAP.XML
# =============================================================================
@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt(request: Request) -> str:
    base_url = str(request.base_url).rstrip("/")
    return "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {base_url}/sitemap.xml",
    ])


@app.get("/sitemap.xml")
def sitemap_xml(request: Request, db: Session = Depends(get_db)) -> Response:
    xml_body = generate_sitemap_xml(request, db)
    return Response(content=xml_body, media_type="application/xml")


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =============================================================================
def _not_found_response(request: Request, db: Session) -> HTMLResponse:
    categories = db.query(Category).options(joinedload(Category.subcategories)).order_by(Category.sort_order).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": categories,
            "featured_products": [],
            "new_products": [],
            "page_title": "Страница не найдена — ТЦ «Алмаз»",
        },
        status_code=404,
    )

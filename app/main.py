from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import Category, Product, Promotion
from .seo import generate_sitemap_xml


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Отдел женской кожаной обуви в ТЦ «Карнавал» в Перми")

static_dir = BASE_DIR.parent / "static"
templates_dir = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    categories = db.query(Category).all()
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": categories,
            "products": products,
            "page_title": "Отдел женской кожаной обуви в ТЦ «Карнавал» в Перми",
        },
    )


@app.get("/category/{slug}", response_class=HTMLResponse)
def read_category(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    category = db.query(Category).filter(Category.slug == slug).first()
    if category is None:
        return templates.TemplateResponse(
            "index.html",
            {
            "request": request,
            "categories": db.query(Category).all(),
            "products": [],
            "page_title": "Отдел женской кожаной обуви в ТЦ «Карнавал» в Перми",
            },
            status_code=404,
        )

    size = request.query_params.get("size")
    color = request.query_params.get("color")

    query = (
        db.query(Product)
        .filter(Product.category_id == category.id, Product.is_active.is_(True))
    )
    if size:
        query = query.filter(Product.size == size)
    if color:
        query = query.filter(Product.color == color)

    products = query.order_by(Product.created_at.desc()).all()

    # Список доступных значений для фильтров
    available_sizes = sorted(
        {p.size for p in db.query(Product).filter(Product.category_id == category.id, Product.is_active.is_(True)) if p.size}
    )
    available_colors = sorted(
        {p.color for p in db.query(Product).filter(Product.category_id == category.id, Product.is_active.is_(True)) if p.color}
    )

    return templates.TemplateResponse(
        "category.html",
        {
            "request": request,
            "categories": db.query(Category).all(),
            "category": category,
            "products": products,
            "active_size": size or "",
            "active_color": color or "",
            "available_sizes": available_sizes,
            "available_colors": available_colors,
            "page_title": f"{category.name} — отдел женской кожаной обуви в ТЦ «Карнавал» в Перми",
        },
    )


@app.get("/product/{product_id}-{slug}", response_class=HTMLResponse)
def read_product(
    product_id: int,
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.slug == slug, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        return templates.TemplateResponse(
            "index.html",
            {
            "request": request,
            "categories": db.query(Category).all(),
            "products": [],
            "page_title": "Товар не найден — отдел женской кожаной обуви в ТЦ «Карнавал» в Перми",
            },
            status_code=404,
        )

    breadcrumbs = [
        {"name": "Главная", "url": "/"},
        {"name": product.category.name if product.category else "Каталог", "url": f"/category/{product.category.slug}" if product.category else "/"},
        {"name": product.name, "url": f"/product/{product.id}-{product.slug}"},
    ]

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product,
            "breadcrumbs": breadcrumbs,
            "page_title": f"{product.name} — отдел женской кожаной обуви в ТЦ «Карнавал» в Перми",
        },
    )


@app.get("/hx/products/{slug}", response_class=HTMLResponse)
def hx_products_by_category(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    category = db.query(Category).filter(Category.slug == slug).first()
    size = request.query_params.get("size")
    color = request.query_params.get("color")

    query = db.query(Product).filter(Product.is_active.is_(True))
    if category:
        query = query.filter(Product.category_id == category.id)
    if size:
        query = query.filter(Product.size == size)
    if color:
        query = query.filter(Product.color == color)

    products = query.order_by(Product.created_at.desc()).all()

    return templates.TemplateResponse(
        "partials/product_list.html",
        {
            "request": request,
            "products": products,
        },
    )


@app.get("/hx/category/{slug}/filter", response_class=HTMLResponse)
def hx_category_filter(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    category = db.query(Category).filter(Category.slug == slug).first()
    if category is None:
        products: list[Product] = []
    else:
        size = request.query_params.get("size")
        color = request.query_params.get("color")

        query = db.query(Product).filter(
            Product.category_id == category.id,
            Product.is_active.is_(True),
        )
        if size:
            query = query.filter(Product.size == size)
        if color:
            query = query.filter(Product.color == color)

        products = query.order_by(Product.created_at.desc()).all()

    return templates.TemplateResponse(
        "partials/product_list.html",
        {
            "request": request,
            "products": products,
        },
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt(request: Request) -> str:
    base_url = str(request.base_url).rstrip("/")
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {base_url}/sitemap.xml",
        ]
    )


@app.get("/sitemap.xml")
def sitemap_xml(request: Request, db: Session = Depends(get_db)) -> Response:
    xml_body = generate_sitemap_xml(request, db)
    return Response(content=xml_body, media_type="application/xml")


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    winter_category = db.query(Category).filter(Category.slug == "zhenskaya-zimnyaya-obuv").first()
    demiseason_category = db.query(Category).filter(Category.slug == "zhenskaya-demisezonnyaya-obuv").first()

    winter_products: List[Product] = []
    demiseason_products: List[Product] = []

    if winter_category:
        winter_products = (
            db.query(Product)
            .filter(Product.category_id == winter_category.id, Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
            .all()
        )
    if demiseason_category:
        demiseason_products = (
            db.query(Product)
            .filter(Product.category_id == demiseason_category.id, Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
            .all()
        )

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "winter_products": winter_products,
            "demiseason_products": demiseason_products,
            "page_title": "Женская кожаная обувь — зимняя и демисезонная",
        },
    )


@app.get("/promotions", response_class=HTMLResponse)
def promotions_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
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
            "promotions": promotions,
            "page_title": "Акции отдела женской обуви в ТЦ «Карнавал»",
        },
    )


@app.get("/map", response_class=HTMLResponse)
def map_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "page_title": "Как нас найти — ТЦ «Карнавал», Пермь",
        },
    )



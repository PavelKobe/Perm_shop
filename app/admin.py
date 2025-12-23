"""Админ-панель для управления товарами и акциями."""

import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from .auth import (
    clear_session_cookie,
    get_current_admin,
    require_admin,
    set_session_cookie,
    verify_password,
)
from .database import get_db
from .models import Category, Product, Promotion, Subcategory

router = APIRouter(prefix="/admin", tags=["admin"])

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Добавляем фильтр from_json для шаблонов
def _from_json(value: str | None) -> list | dict:
    """Парсинг JSON."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

templates.env.filters["from_json"] = _from_json

# Путь для загрузки фото товаров
UPLOAD_DIR = BASE_DIR.parent / "static" / "images" / "products"


def slugify(text: str) -> str:
    """Преобразовать текст в slug."""
    # Транслитерация русских букв
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    text = text.lower()
    result = []
    for char in text:
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isalnum():
            result.append(char)
        elif char in ' -_':
            result.append('-')
    slug = ''.join(result)
    # Убираем множественные дефисы
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def save_uploaded_image(
    file: UploadFile,
    category_slug: str,
    subcategory_slug: str,
    product_slug: str,
) -> str:
    """
    Сохранить загруженное изображение.
    
    Returns:
        URL изображения относительно static
    """
    # Создаём директорию если не существует
    upload_path = UPLOAD_DIR / category_slug / subcategory_slug
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # Генерируем имя файла
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    filename = f"{product_slug}{ext}"
    
    # Сохраняем файл
    file_path = upload_path / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Возвращаем URL
    return f"/static/images/products/{category_slug}/{subcategory_slug}/{filename}"


def image_exists(image_url: str | None) -> bool:
    """Проверить существует ли файл изображения."""
    if not image_url:
        return False
    image_path = BASE_DIR.parent / image_url.lstrip("/")
    return image_path.exists()


# =============================================================================
# АВТОРИЗАЦИЯ
# =============================================================================

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Страница входа."""
    # Если уже авторизован - редирект на дашборд
    if get_current_admin(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": None},
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> RedirectResponse:
    """Обработка входа."""
    if not verify_password(username, password):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=401,
        )
    
    response = RedirectResponse(url="/admin", status_code=302)
    set_session_cookie(response, username)
    return response


@router.get("/logout")
def logout() -> RedirectResponse:
    """Выход из админки."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    clear_session_cookie(response)
    return response


# =============================================================================
# ДАШБОРД
# =============================================================================

@router.get("", response_class=HTMLResponse)
def dashboard(
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Главная страница админки."""
    # Статистика
    stats = {
        "products_count": db.query(Product).filter(Product.is_active.is_(True)).count(),
        "new_count": db.query(Product).filter(
            Product.is_active.is_(True), Product.is_new.is_(True)
        ).count(),
        "sale_count": db.query(Product).filter(
            Product.is_active.is_(True),
            Product.old_price.isnot(None),
            Product.old_price > Product.price,
        ).count(),
        "promotions_count": db.query(Promotion).filter(Promotion.is_active.is_(True)).count(),
        "categories_count": db.query(Category).count(),
    }
    
    # Последние товары
    recent_products = (
        db.query(Product)
        .options(joinedload(Product.subcategory).joinedload(Subcategory.category))
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "recent_products": recent_products,
        },
    )


# =============================================================================
# ТОВАРЫ
# =============================================================================

@router.get("/products", response_class=HTMLResponse)
def products_list(
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    search: Optional[str] = None,
    show_deleted: Optional[str] = None,
) -> HTMLResponse:
    """Список товаров."""
    query = db.query(Product).options(
        joinedload(Product.subcategory).joinedload(Subcategory.category)
    )
    
    # По умолчанию показываем только активные товары
    if not show_deleted:
        query = query.filter(Product.is_active.is_(True))
    
    if category_id:
        query = query.join(Subcategory).filter(Subcategory.category_id == category_id)
    if subcategory_id:
        query = query.filter(Product.subcategory_id == subcategory_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    products = query.order_by(Product.created_at.desc()).all()
    categories = db.query(Category).options(joinedload(Category.subcategories)).all()
    
    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "admin": admin,
            "products": products,
            "categories": categories,
            "selected_category_id": category_id,
            "selected_subcategory_id": subcategory_id,
            "search": search or "",
            "show_deleted": bool(show_deleted),
        },
    )


@router.get("/products/add", response_class=HTMLResponse)
def product_add_form(
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Форма добавления товара."""
    categories = db.query(Category).options(joinedload(Category.subcategories)).all()
    
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "admin": admin,
            "product": None,
            "categories": categories,
            "has_image": False,
            "form_action": "/admin/products/add",
            "form_title": "Добавить товар",
        },
    )


@router.post("/products/add")
def product_add(
    request: Request,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    name: str = Form(...),
    subcategory_id: int = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    old_price: Optional[float] = Form(None),
    sizes: list[str] = Form(default=[]),
    color: str = Form(""),
    is_new: bool = Form(False),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    image: UploadFile = File(None),
) -> RedirectResponse:
    """Создание товара."""
    # Получаем подкатегорию и категорию
    subcategory = db.query(Subcategory).options(
        joinedload(Subcategory.category)
    ).filter(Subcategory.id == subcategory_id).first()
    
    if not subcategory:
        raise HTTPException(status_code=400, detail="Подкатегория не найдена")
    
    # Генерируем slug
    slug = slugify(name)
    
    # Обрабатываем размеры
    sizes_json = json.dumps([int(s) for s in sizes if s.isdigit()]) if sizes else None
    
    # Обрабатываем старую цену
    if old_price is not None and old_price <= 0:
        old_price = None
    
    # Сохраняем изображение если есть
    image_url = None
    if image and image.filename:
        image_url = save_uploaded_image(
            image,
            subcategory.category.slug,
            subcategory.slug,
            slug,
        )
    
    # Создаём товар
    product = Product(
        name=name,
        slug=slug,
        description=description or None,
        price=price,
        old_price=old_price,
        sizes_json=sizes_json,
        color=color or None,
        image_url=image_url,
        is_new=is_new,
        is_featured=is_featured,
        is_active=is_active,
        subcategory_id=subcategory_id,
    )
    
    db.add(product)
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)


@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
def product_edit_form(
    product_id: int,
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Форма редактирования товара."""
    product = (
        db.query(Product)
        .options(joinedload(Product.subcategory).joinedload(Subcategory.category))
        .filter(Product.id == product_id)
        .first()
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    categories = (
        db.query(Category)
        .options(joinedload(Category.subcategories))
        .order_by(Category.sort_order)
        .all()
    )
    
    # Проверяем существует ли файл изображения
    has_image = image_exists(product.image_url) if product.image_url else False
    
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "admin": admin,
            "product": product,
            "categories": categories,
            "has_image": has_image,
            "form_action": f"/admin/products/edit/{product_id}",
            "form_title": "Редактировать товар",
        },
    )


@router.post("/products/edit/{product_id}")
def product_edit(
    product_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    name: str = Form(...),
    subcategory_id: int = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    old_price: Optional[float] = Form(None),
    sizes: list[str] = Form(default=[]),
    color: str = Form(""),
    is_new: bool = Form(False),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    image: UploadFile = File(None),
) -> RedirectResponse:
    """Обновление товара."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Получаем подкатегорию
    subcategory = db.query(Subcategory).options(
        joinedload(Subcategory.category)
    ).filter(Subcategory.id == subcategory_id).first()
    
    if not subcategory:
        raise HTTPException(status_code=400, detail="Подкатегория не найдена")
    
    # Обновляем поля
    product.name = name
    product.slug = slugify(name)
    product.description = description or None
    product.price = price
    product.old_price = old_price if old_price and old_price > 0 else None
    product.sizes_json = json.dumps([int(s) for s in sizes if s.isdigit()]) if sizes else None
    product.color = color or None
    product.is_new = is_new
    product.is_featured = is_featured
    product.is_active = is_active
    product.subcategory_id = subcategory_id
    
    # Обновляем изображение если загружено новое
    if image and image.filename:
        product.image_url = save_uploaded_image(
            image,
            subcategory.category.slug,
            subcategory.slug,
            product.slug,
        )
    
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)


@router.post("/products/delete/{product_id}")
def product_delete(
    product_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> RedirectResponse:
    """Логическое удаление товара (soft delete)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Логическое удаление - просто деактивируем
    product.is_active = False
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)


@router.post("/products/restore/{product_id}")
def product_restore(
    product_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> RedirectResponse:
    """Восстановление удалённого товара."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product.is_active = True
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)


@router.post("/products/hard-delete/{product_id}")
def product_hard_delete(
    product_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> RedirectResponse:
    """Полное удаление товара из БД (необратимо)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Удаляем файл изображения если есть
    if product.image_url:
        image_path = BASE_DIR.parent / product.image_url.lstrip("/")
        if image_path.exists():
            image_path.unlink()
    
    db.delete(product)
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)


# =============================================================================
# АКЦИИ
# =============================================================================

@router.get("/promotions", response_class=HTMLResponse)
def promotions_list(
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Список акций."""
    promotions = db.query(Promotion).order_by(Promotion.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "admin/promotions.html",
        {
            "request": request,
            "admin": admin,
            "promotions": promotions,
        },
    )


@router.get("/promotions/add", response_class=HTMLResponse)
def promotion_add_form(
    request: Request,
    admin: str = Depends(require_admin),
) -> HTMLResponse:
    """Форма добавления акции."""
    return templates.TemplateResponse(
        "admin/promotion_form.html",
        {
            "request": request,
            "admin": admin,
            "promotion": None,
            "form_action": "/admin/promotions/add",
            "form_title": "Добавить акцию",
        },
    )


@router.post("/promotions/add")
def promotion_add(
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    title: str = Form(...),
    description: str = Form(""),
    discount_text: str = Form(""),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),
) -> RedirectResponse:
    """Создание акции."""
    slug = slugify(title)
    
    # Парсим даты
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    promotion = Promotion(
        title=title,
        slug=slug,
        description=description or None,
        discount_text=discount_text or None,
        start_date=start,
        end_date=end,
        is_active=is_active,
    )
    
    db.add(promotion)
    db.commit()
    
    return RedirectResponse(url="/admin/promotions", status_code=302)


@router.get("/promotions/edit/{promotion_id}", response_class=HTMLResponse)
def promotion_edit_form(
    promotion_id: int,
    request: Request,
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Форма редактирования акции."""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    
    return templates.TemplateResponse(
        "admin/promotion_form.html",
        {
            "request": request,
            "admin": admin,
            "promotion": promotion,
            "form_action": f"/admin/promotions/edit/{promotion_id}",
            "form_title": "Редактировать акцию",
        },
    )


@router.post("/promotions/edit/{promotion_id}")
def promotion_edit(
    promotion_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    title: str = Form(...),
    description: str = Form(""),
    discount_text: str = Form(""),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),
) -> RedirectResponse:
    """Обновление акции."""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    
    promotion.title = title
    promotion.slug = slugify(title)
    promotion.description = description or None
    promotion.discount_text = discount_text or None
    promotion.start_date = date.fromisoformat(start_date) if start_date else None
    promotion.end_date = date.fromisoformat(end_date) if end_date else None
    promotion.is_active = is_active
    
    db.commit()
    
    return RedirectResponse(url="/admin/promotions", status_code=302)


@router.post("/promotions/delete/{promotion_id}")
def promotion_delete(
    promotion_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> RedirectResponse:
    """Удаление акции."""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    
    db.delete(promotion)
    db.commit()
    
    return RedirectResponse(url="/admin/promotions", status_code=302)


# =============================================================================
# API для динамической подгрузки подкатегорий
# =============================================================================

@router.get("/api/subcategories/{category_id}")
def get_subcategories(
    category_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
) -> list[dict]:
    """Получить подкатегории для категории (для AJAX)."""
    subcategories = (
        db.query(Subcategory)
        .filter(Subcategory.category_id == category_id)
        .order_by(Subcategory.sort_order)
        .all()
    )
    return [{"id": s.id, "name": s.name} for s in subcategories]


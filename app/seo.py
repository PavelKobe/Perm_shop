from datetime import datetime
from typing import Iterable, List

from fastapi import Request
from sqlalchemy.orm import Session

from .models import Category, Product


def _build_url(base_url: str, path: str) -> str:
    if base_url.endswith("/"):
        base = base_url[:-1]
    else:
        base = base_url
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def _format_lastmod(dt) -> str:
    if not dt:
        return ""
    # ISO 8601 without microseconds, e.g. 2025-01-01T12:00:00+00:00
    if isinstance(dt, datetime):
        return dt.replace(microsecond=0).isoformat()
    return str(dt)


def generate_sitemap_entries(
    *,
    base_url: str,
    categories: Iterable[Category],
    products: Iterable[Product],
) -> List[dict]:
    entries: List[dict] = []

    # Главная
    entries.append({"loc": _build_url(base_url, "/"), "changefreq": "daily", "priority": "1.0"})

    # Категории
    for cat in categories:
        entries.append(
            {
                "loc": _build_url(base_url, f"/category/{cat.slug}"),
                "changefreq": "daily",
                "priority": "0.8",
            }
        )

    # Товары
    for product in products:
        entries.append(
            {
                "loc": _build_url(base_url, f"/product/{product.id}-{product.slug}"),
                "lastmod": _format_lastmod(product.created_at),
                "changefreq": "weekly",
                "priority": "0.7",
            }
        )

    return entries


def generate_sitemap_xml(request: Request, db: Session) -> str:
    base_url = str(request.base_url).rstrip("/")

    categories = db.query(Category).all()
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
        .all()
    )

    entries = generate_sitemap_entries(
        base_url=base_url,
        categories=categories,
        products=products,
    )

    parts: List[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for item in entries:
        parts.append("  <url>")
        parts.append(f"    <loc>{item['loc']}</loc>")
        if item.get("lastmod"):
            parts.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        if item.get("changefreq"):
            parts.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        if item.get("priority"):
            parts.append(f"    <priority>{item['priority']}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    return "\n".join(parts)



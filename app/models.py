from datetime import datetime, date

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Category(Base):
    """Основные категории: Зимняя, Демисезонная, Летняя обувь"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    icon = Column(String(32), nullable=True)  # emoji или иконка
    sort_order = Column(Integer, default=0, nullable=False)

    subcategories = relationship("Subcategory", back_populates="category", order_by="Subcategory.sort_order")


class Subcategory(Base):
    """Подгруппы: Сапоги, Ботинки, Кроссовки, Угги и т.д."""
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="subcategories")

    products = relationship("Product", back_populates="subcategory", order_by="Product.created_at.desc()")


class Product(Base):
    """Товар — привязан к подкатегории"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)
    sizes_json = Column(String(255), nullable=True)  # JSON: "[36, 37, 38, 39]"
    color = Column(String(64), nullable=True)
    image_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_new = Column(Boolean, default=False, nullable=False)  # новинка
    is_featured = Column(Boolean, default=False, nullable=False)  # актуальный товар
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    subcategory = relationship("Subcategory", back_populates="products")


class Promotion(Base):
    """Акции и спецпредложения"""
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    discount_text = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint(
            "discount_price IS NULL OR discount_price <= price",
            name="ck_products_discount_not_above_price",
        ),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_non_negative"),
    )

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False)
    discount_price = Column(Numeric(10, 2), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0, server_default="0")
    image_url = Column(String(255), nullable=True)
    brand = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    # deleting a product also deletes its stock history
    transactions = relationship(
        "InventoryTransaction", back_populates="product", cascade="all, delete-orphan"
    )

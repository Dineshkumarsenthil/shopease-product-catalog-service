from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category_id: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    sku: str = Field(min_length=2, max_length=50)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    discount_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=255)
    brand: str | None = Field(default=None, max_length=100)
    is_active: bool = True

    @model_validator(mode="after")
    def check_discount(self):
        if self.discount_price is not None and self.discount_price > self.price:
            raise ValueError("discount_price cannot be greater than price")
        return self


class ProductCreate(ProductBase):
    # Opening stock. Later changes go through the inventory APIs.
    stock_quantity: int = Field(default=0, ge=0)


class ProductUpdate(ProductBase):
    pass


class ProductPatch(BaseModel):
    """Every field is optional, only the fields that are sent get changed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    sku: str | None = Field(default=None, min_length=2, max_length=50)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    discount_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=255)
    brand: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    sku: str
    price: Decimal
    discount_price: Decimal | None
    stock_quantity: int
    image_url: str | None
    brand: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductResponse]

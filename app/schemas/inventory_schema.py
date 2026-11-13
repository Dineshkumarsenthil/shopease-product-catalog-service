from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockChange(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    quantity: int = Field(gt=0, description="Must be greater than zero")
    remarks: str | None = Field(default=None, max_length=255)


class StockResponse(BaseModel):
    product_id: int
    name: str
    sku: str
    stock_quantity: int
    low_stock_threshold: int
    is_low_stock: bool


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    transaction_type: str
    quantity: int
    previous_stock: int
    updated_stock: int
    remarks: str | None
    created_at: datetime


class LowStockProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    stock_quantity: int

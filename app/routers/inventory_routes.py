from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, require_admin
from app.database.connection import get_db
from app.schemas.inventory_schema import (
    LowStockProduct, StockChange, StockResponse, TransactionResponse,
)
from app.services import inventory_service

# All inventory APIs are for administrators only
router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


# This route must stay above "/{product_id}", otherwise "low-stock" is read as a product id
@router.get("/low-stock", response_model=list[LowStockProduct])
def low_stock_products(
    threshold: int | None = Query(None, ge=0, description="Defaults to LOW_STOCK_THRESHOLD"),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return inventory_service.get_low_stock_products(db, threshold)


@router.get("/{product_id}", response_model=StockResponse)
def get_stock(
    product_id: int, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    return inventory_service.get_stock(db, product_id)


@router.post(
    "/{product_id}/stock-in",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def stock_in(
    product_id: int,
    data: StockChange,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return inventory_service.change_stock(db, product_id, data.quantity, "IN", data.remarks)


@router.post(
    "/{product_id}/stock-out",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def stock_out(
    product_id: int,
    data: StockChange,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return inventory_service.change_stock(db, product_id, data.quantity, "OUT", data.remarks)


@router.get("/{product_id}/history", response_model=list[TransactionResponse])
def stock_history(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return inventory_service.get_history(db, product_id, skip, limit)

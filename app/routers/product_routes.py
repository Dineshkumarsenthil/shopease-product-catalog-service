from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user, require_admin
from app.database.connection import get_db
from app.schemas.product_schema import (
    ProductCreate, ProductListResponse, ProductPatch, ProductResponse, ProductUpdate,
)
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    return product_service.create_product(db, data)


@router.get("/", response_model=ProductListResponse)
def list_products(
    search: str | None = Query(None, min_length=1, max_length=100, description="Name or SKU"),
    category_id: int | None = Query(None, ge=1),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    in_stock: bool | None = Query(None, description="true = available, false = out of stock"),
    include_inactive: bool = Query(False, description="Admins only"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Literal["id", "name", "price", "stock_quantity", "created_at"] = "id",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return product_service.list_products(
        db,
        show_inactive=user.is_admin and include_inactive,
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return product_service.get_product(db, product_id, show_inactive=user.is_admin)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return product_service.update_product(db, product_id, data)


@router.patch("/{product_id}", response_model=ProductResponse)
def patch_product(
    product_id: int,
    data: ProductPatch,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return product_service.patch_product(db, product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    product_service.delete_product(db, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

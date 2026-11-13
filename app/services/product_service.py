from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.inventory_model import InventoryTransaction
from app.models.product_model import Product
from app.schemas.product_schema import ProductCreate, ProductPatch, ProductUpdate

# columns the customer is allowed to sort by
SORT_COLUMNS = {
    "id": Product.id,
    "name": Product.name,
    "price": Product.price,
    "stock_quantity": Product.stock_quantity,
    "created_at": Product.created_at,
}


def _check_category_exists(db: Session, category_id: int):
    if db.get(Category, category_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")


def _check_sku_is_free(db: Session, sku: str, ignore_id: int | None = None):
    query = db.query(Product).filter(Product.sku == sku)
    if ignore_id is not None:
        query = query.filter(Product.id != ignore_id)
    if query.first():
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    _check_category_exists(db, data.category_id)
    _check_sku_is_free(db, data.sku)

    product = Product(**data.model_dump())
    db.add(product)

    try:
        db.flush()  # gives the product an id without committing yet

        # If the product starts with stock, record it in the history too
        if product.stock_quantity > 0:
            db.add(
                InventoryTransaction(
                    product_id=product.id,
                    transaction_type="IN",
                    quantity=product.stock_quantity,
                    previous_stock=0,
                    updated_stock=product.stock_quantity,
                    remarks="Initial stock",
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")

    db.refresh(product)
    return product


def list_products(
    db: Session,
    show_inactive: bool,
    search: str | None,
    category_id: int | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    in_stock: bool | None,
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
) -> dict:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_price cannot be greater than max_price")

    query = db.query(Product)

    # Customers only see active products that belong to an active category
    if not show_inactive:
        query = query.join(Category).filter(
            Product.is_active.is_(True), Category.is_active.is_(True)
        )

    if search:
        pattern = f"%{search}%"
        query = query.filter(Product.name.like(pattern) | Product.sku.like(pattern))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock_quantity > 0)
    elif in_stock is False:
        query = query.filter(Product.stock_quantity == 0)

    total = query.count()

    sort_column = SORT_COLUMNS[sort_by]
    sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()

    # the extra Product.id keeps the order stable between pages
    items = (
        query.order_by(sort_column, Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_product(db: Session, product_id: int, show_inactive: bool) -> Product:
    product = get_product_or_404(db, product_id)
    if not show_inactive and not (product.is_active and product.category.is_active):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def _apply_changes(db: Session, product: Product, changes: dict) -> Product:
    """Shared by PUT and PATCH."""
    if "category_id" in changes:
        _check_category_exists(db, changes["category_id"])
    if "sku" in changes:
        _check_sku_is_free(db, changes["sku"], ignore_id=product.id)

    # The discount must still be valid after the change
    new_price = changes.get("price", product.price)
    new_discount = changes.get("discount_price", product.discount_price)
    if new_discount is not None and new_discount > new_price:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "discount_price cannot be greater than price"
        )

    for field, value in changes.items():
        setattr(product, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")

    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product_or_404(db, product_id)
    return _apply_changes(db, product, data.model_dump())


def patch_product(db: Session, product_id: int, data: ProductPatch) -> Product:
    product = get_product_or_404(db, product_id)
    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields were sent to update")

    # discount_price may be set to null (removes the discount), the rest may not
    for field in ("category_id", "name", "sku", "price", "is_active"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"{field} cannot be null"
            )

    return _apply_changes(db, product, changes)


def delete_product(db: Session, product_id: int) -> None:
    product = get_product_or_404(db, product_id)
    db.delete(product)  # its stock history is deleted along with it
    db.commit()

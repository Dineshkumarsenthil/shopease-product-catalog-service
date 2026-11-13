from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inventory_model import InventoryTransaction
from app.models.product_model import Product
from app.schemas.inventory_schema import StockResponse
from app.services.product_service import get_product_or_404


def get_stock(db: Session, product_id: int) -> StockResponse:
    product = get_product_or_404(db, product_id)
    threshold = settings.low_stock_threshold
    return StockResponse(
        product_id=product.id,
        name=product.name,
        sku=product.sku,
        stock_quantity=product.stock_quantity,
        low_stock_threshold=threshold,
        is_low_stock=product.stock_quantity <= threshold,
    )


def change_stock(
    db: Session, product_id: int, quantity: int, transaction_type: str, remarks: str | None
) -> InventoryTransaction:
    """
    Increase ("IN") or decrease ("OUT") the stock of a product.

    The product row is locked with SELECT ... FOR UPDATE, so if two requests
    try to change the same product at the same time, the second one waits
    until the first has finished. That keeps the stock number correct.

    The stock update and the history row are saved in one transaction:
    either both are saved or neither is.
    """
    try:
        product = (
            db.query(Product).filter(Product.id == product_id).with_for_update().first()
        )
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

        previous_stock = product.stock_quantity

        if transaction_type == "OUT":
            if quantity > previous_stock:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Insufficient stock. Available: {previous_stock}, requested: {quantity}",
                )
            updated_stock = previous_stock - quantity
        else:
            updated_stock = previous_stock + quantity

        product.stock_quantity = updated_stock

        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_stock=previous_stock,
            updated_stock=updated_stock,
            remarks=remarks,
        )
        db.add(transaction)
        db.commit()

    except HTTPException:
        db.rollback()  # also releases the row lock
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not update the stock. Nothing was changed.",
        )

    db.refresh(transaction)
    return transaction


def get_history(db: Session, product_id: int, skip: int, limit: int) -> list[InventoryTransaction]:
    get_product_or_404(db, product_id)
    return (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_low_stock_products(db: Session, threshold: int | None) -> list[Product]:
    if threshold is None:
        threshold = settings.low_stock_threshold
    return (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.stock_quantity <= threshold)
        .order_by(Product.stock_quantity, Product.id)
        .all()
    )

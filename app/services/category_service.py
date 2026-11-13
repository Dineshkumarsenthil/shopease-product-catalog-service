from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.product_model import Product
from app.schemas.category_schema import CategoryCreate, CategoryUpdate


def get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


def _check_name_is_free(db: Session, name: str, ignore_id: int | None = None):
    query = db.query(Category).filter(Category.name == name)
    if ignore_id is not None:
        query = query.filter(Category.id != ignore_id)
    if query.first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Category name already exists")


def create_category(db: Session, data: CategoryCreate) -> Category:
    _check_name_is_free(db, data.name)
    category = Category(**data.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Category name already exists")
    db.refresh(category)
    return category


def list_categories(db: Session, show_inactive: bool) -> list[Category]:
    query = db.query(Category)
    if not show_inactive:
        query = query.filter(Category.is_active.is_(True))
    return query.order_by(Category.name).all()


def get_category(db: Session, category_id: int, show_inactive: bool) -> Category:
    category = get_category_or_404(db, category_id)
    # customers cannot see inactive categories
    if not category.is_active and not show_inactive:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category_or_404(db, category_id)
    _check_name_is_free(db, data.name, ignore_id=category_id)

    for field, value in data.model_dump().items():
        setattr(category, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Category name already exists")
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category_or_404(db, category_id)

    # Rule: a category that still has products cannot be deleted.
    # Move or delete its products first (or just deactivate the category).
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot delete: category still has {product_count} product(s). "
            "Move or delete them first, or deactivate the category instead.",
        )

    db.delete(category)
    db.commit()

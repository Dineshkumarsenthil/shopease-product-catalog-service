from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user, require_admin
from app.database.connection import get_db
from app.schemas.category_schema import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    return category_service.create_category(db, data)


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    include_inactive: bool = Query(False, description="Admins only"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    show_inactive = user.is_admin and include_inactive
    return category_service.list_categories(db, show_inactive)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return category_service.get_category(db, category_id, show_inactive=user.is_admin)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    return category_service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    category_service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

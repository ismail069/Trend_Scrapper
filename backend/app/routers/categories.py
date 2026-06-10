from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_repository
from app.models import ApiMessage, Category, CategoryCreate, CategoryUpdate
from app.services.supabase_service import DataRepository

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[Category])
def list_categories(
    repository: DataRepository = Depends(get_repository),
) -> list[Category]:
    return repository.list_categories()


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    repository: DataRepository = Depends(get_repository),
) -> Category:
    return repository.create_category(payload.name)


@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    repository: DataRepository = Depends(get_repository),
) -> Category:
    return repository.update_category(category_id, payload.name)


@router.delete("/{category_id}", response_model=ApiMessage)
def delete_category(
    category_id: UUID,
    repository: DataRepository = Depends(get_repository),
) -> ApiMessage:
    repository.delete_category(category_id)
    return ApiMessage(message="Category deleted.")


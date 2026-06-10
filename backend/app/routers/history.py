from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_repository
from app.models import ApiMessage, HistoryRecord
from app.services.supabase_service import DataRepository

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[HistoryRecord])
def list_history(
    repository: DataRepository = Depends(get_repository),
) -> list[HistoryRecord]:
    return repository.list_history()


@router.get("/{history_id}", response_model=HistoryRecord)
def get_history(
    history_id: UUID,
    repository: DataRepository = Depends(get_repository),
) -> HistoryRecord:
    return repository.get_history(history_id)


@router.delete("/{history_id}", response_model=ApiMessage)
def delete_history(
    history_id: UUID,
    repository: DataRepository = Depends(get_repository),
) -> ApiMessage:
    repository.delete_history(history_id)
    return ApiMessage(message="History item deleted.")


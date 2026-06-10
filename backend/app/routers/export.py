from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models import ExportRequest
from app.services.export_service import build_docx, build_pdf

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/pdf")
def export_pdf(payload: ExportRequest) -> StreamingResponse:
    return StreamingResponse(
        build_pdf(payload),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="feed-tren-scrapper.pdf"'},
    )


@router.post("/docx")
def export_docx(payload: ExportRequest) -> StreamingResponse:
    return StreamingResponse(
        build_docx(payload),
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={"Content-Disposition": 'attachment; filename="feed-tren-scrapper.docx"'},
    )


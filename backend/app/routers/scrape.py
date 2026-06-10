from fastapi import APIRouter, Depends

from app.dependencies import get_repository, get_scraper_service
from app.models import ScrapeRequest, ScrapeResponse
from app.services.scraper_service import FeedScraperService
from app.services.supabase_service import DataRepository

router = APIRouter(prefix="/api", tags=["scrape"])


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_feed(
    payload: ScrapeRequest,
    scraper: FeedScraperService = Depends(get_scraper_service),
    repository: DataRepository = Depends(get_repository),
) -> ScrapeResponse:
    results, warnings, mode = await scraper.scrape(
        payload.prompt,
        payload.category,
        payload.days,
    )
    history = repository.save_history(
        payload.prompt,
        payload.category,
        results,
        warnings,
    )
    return ScrapeResponse(
        history=history,
        mode=mode,
        message=(
            f"Found {len(results)} recent item(s)."
            if results
            else "Search completed with no recent items."
        ),
    )


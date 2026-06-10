from functools import lru_cache

from app.config import get_settings
from app.services.openai_service import OpenAIService
from app.services.scraper_service import FeedScraperService
from app.services.supabase_service import DataRepository


@lru_cache
def get_repository() -> DataRepository:
    return DataRepository(get_settings())


@lru_cache
def get_openai_service() -> OpenAIService:
    return OpenAIService(get_settings())


@lru_cache
def get_scraper_service() -> FeedScraperService:
    return FeedScraperService(get_settings(), get_openai_service())


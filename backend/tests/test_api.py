from datetime import UTC, datetime

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_repository
from app.main import app
from app.models import ExportRequest, FeedResult, ResearchPlan
from app.services.export_service import build_docx, build_pdf
from app.services.openai_service import OpenAIService
from app.services.scraper_service import FeedScraperService

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_default_categories_exist() -> None:
    response = client.get("/api/categories")
    assert response.status_code == 200
    names = {category["name"] for category in response.json()}
    assert {"Default", "Trending"}.issubset(names)


def test_category_lifecycle() -> None:
    created = client.post("/api/categories", json={"name": "Technology"})
    assert created.status_code == 201
    category = created.json()

    updated = client.put(
        f"/api/categories/{category['id']}",
        json={"name": "AI Tools"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "AI Tools"

    deleted = client.delete(f"/api/categories/{category['id']}")
    assert deleted.status_code == 200


def test_export_generation() -> None:
    payload = ExportRequest(
        prompt="AI agents",
        category="Trending",
        searched_at=datetime.now(UTC),
        results=[
            FeedResult(
                title="Test result",
                summary="Verified export test.",
                category="Trending",
                relevance_score=0.9,
            )
        ],
    )
    assert len(build_pdf(payload).getvalue()) > 1000
    assert len(build_docx(payload).getvalue()) > 1000


def test_rss_date_parser() -> None:
    parsed = FeedScraperService._parse_rss_date("Wed, 10 Jun 2026 10:00:00 GMT")
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.tzinfo is not None


def test_generic_news_prompt_detection() -> None:
    assert FeedScraperService._is_generic_news_prompt(
        "What is the trending news?"
    )
    assert not FeedScraperService._is_generic_news_prompt("Trending AI news")


def test_optional_source_warning_hidden_when_results_exist() -> None:
    openai_service = OpenAIService(Settings())
    openai_service.build_plan = AsyncMock(
        return_value=(ResearchPlan(queries=["AI"], keywords=["ai"]), "local")
    )
    openai_service.rank_results = AsyncMock(
        side_effect=lambda prompt, results: (results, False)
    )
    scraper = FeedScraperService(Settings(), openai_service)
    scraper._search_hacker_news = AsyncMock(
        return_value=[
            FeedResult(
                title="Recent AI report",
                summary="A recent public feed item.",
                category="Trending",
            )
        ]
    )
    scraper._search_reddit = AsyncMock(side_effect=RuntimeError("blocked"))
    scraper._search_google_news = AsyncMock(return_value=[])

    import asyncio

    results, warnings, _ = asyncio.run(scraper.scrape("AI", "Trending", 30))
    assert results
    assert warnings == []


def teardown_module() -> None:
    get_repository.cache_clear()

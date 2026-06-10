import asyncio
import logging
import re
from datetime import UTC, datetime, timedelta
from html import unescape
from urllib.parse import quote_plus

import httpx

from app.config import Settings
from app.models import FeedResult, ResearchPlan
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
TAG_RE = re.compile(r"<[^>]+>")


class FeedScraperService:
    def __init__(self, settings: Settings, openai_service: OpenAIService):
        self.settings = settings
        self.openai = openai_service

    async def scrape(
        self, prompt: str, category: str, days: int
    ) -> tuple[list[FeedResult], list[str], str]:
        plan, planning_mode = await self.openai.build_plan(prompt)
        since = datetime.now(UTC) - timedelta(days=days)
        warnings: list[str] = []

        async with httpx.AsyncClient(
            timeout=12,
            follow_redirects=True,
            headers={"User-Agent": "FeedTrenScrapper/1.0"},
        ) as client:
            tasks = [
                self._search_hacker_news(client, plan, category, since),
                self._search_reddit(client, plan, category, since),
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[FeedResult] = []
        source_names = ("Hacker News", "Reddit")
        for source_name, response in zip(source_names, responses, strict=True):
            if isinstance(response, Exception):
                logger.warning("%s adapter failed: %s", source_name, response)
                warnings.append(f"{source_name} could not be reached.")
            else:
                results.extend(response)

        results = self._deduplicate_and_score(results, prompt, plan)
        results, ai_ranked = await self.openai.rank_results(prompt, results[:20])

        if not results and self.settings.enable_mock_results:
            results = self._demo_results(prompt, category)
            warnings.append("Showing clearly labeled demo data because live sources returned no items.")
        elif not results:
            warnings.append("No recent public items were returned by the configured sources.")

        mode = "openai-ranked" if ai_ranked else f"{planning_mode}-ranked"
        return results[:20], warnings, mode

    async def _search_hacker_news(
        self,
        client: httpx.AsyncClient,
        plan: ResearchPlan,
        category: str,
        since: datetime,
    ) -> list[FeedResult]:
        query = " OR ".join(plan.queries[:3])
        response = await client.get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{int(since.timestamp())}",
                "hitsPerPage": 12,
            },
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", []):
            title = hit.get("title") or hit.get("story_title")
            if not title:
                continue
            object_id = hit.get("objectID")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            points = hit.get("points") or 0
            comments = hit.get("num_comments") or 0
            items.append(
                FeedResult(
                    id=f"hn-{object_id}",
                    title=title,
                    summary=f"Hacker News discussion with {points} points and {comments} comments.",
                    source_url=url,
                    source_name="Hacker News",
                    published_at=hit.get("created_at"),
                    category=category,
                )
            )
        return items

    async def _search_reddit(
        self,
        client: httpx.AsyncClient,
        plan: ResearchPlan,
        category: str,
        since: datetime,
    ) -> list[FeedResult]:
        response = await client.get(
            "https://www.reddit.com/search.json",
            params={
                "q": plan.queries[0],
                "sort": "new",
                "t": "month",
                "limit": 12,
                "raw_json": 1,
            },
        )
        response.raise_for_status()
        items = []
        for child in response.json().get("data", {}).get("children", []):
            data = child.get("data", {})
            created = datetime.fromtimestamp(data.get("created_utc", 0), tz=UTC)
            if created < since:
                continue
            body = data.get("selftext") or ""
            clean_body = unescape(TAG_RE.sub("", body)).strip()
            summary = clean_body[:320] or (
                f"Reddit post with {data.get('score', 0)} points and "
                f"{data.get('num_comments', 0)} comments."
            )
            items.append(
                FeedResult(
                    id=f"reddit-{data.get('id')}",
                    title=data.get("title") or "Untitled Reddit post",
                    summary=summary,
                    source_url=f"https://www.reddit.com{data.get('permalink', '')}",
                    source_name=f"Reddit / r/{data.get('subreddit', 'unknown')}",
                    published_at=created,
                    category=category,
                )
            )
        return items

    def _deduplicate_and_score(
        self,
        results: list[FeedResult],
        prompt: str,
        plan: ResearchPlan,
    ) -> list[FeedResult]:
        terms = {
            word.lower()
            for word in [*prompt.split(), *plan.keywords]
            if len(word) > 2
        }
        seen: set[str] = set()
        ranked: list[FeedResult] = []
        now = datetime.now(UTC)
        for item in results:
            key = re.sub(r"\W+", "", item.title.lower())
            if not key or key in seen:
                continue
            seen.add(key)
            haystack = f"{item.title} {item.summary}".lower()
            keyword_score = sum(term in haystack for term in terms) / max(len(terms), 1)
            age_days = (now - item.published_at).days if item.published_at else 30
            recency_score = max(0, 1 - (age_days / 30))
            score = min(1, (keyword_score * 0.75) + (recency_score * 0.25))
            ranked.append(item.model_copy(update={"relevance_score": round(score, 2)}))
        ranked.sort(key=lambda item: item.relevance_score or 0, reverse=True)
        return ranked

    def _demo_results(self, prompt: str, category: str) -> list[FeedResult]:
        now = datetime.now(UTC)
        return [
            FeedResult(
                id="demo-1",
                title=f"Demo result for {prompt}",
                summary=(
                    "This is demo data, not a live scraped claim. Disable ENABLE_MOCK_RESULTS "
                    "or connect additional adapters before production use."
                ),
                source_url=f"https://example.com/?topic={quote_plus(prompt)}",
                source_name="Demo data",
                published_at=now,
                category=category,
                relevance_score=0.5,
            )
        ]


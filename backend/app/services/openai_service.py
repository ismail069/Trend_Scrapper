import json
import logging

from openai import AsyncOpenAI

from app.config import Settings
from app.models import FeedResult, RankedFeed, ResearchPlan

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, settings: Settings):
        self.model = settings.openai_model
        self.client = (
            AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    async def build_plan(self, prompt: str) -> tuple[ResearchPlan, str]:
        fallback = ResearchPlan(
            queries=[prompt],
            keywords=[word.lower() for word in prompt.split() if len(word) > 2][:8],
        )
        if not self.client:
            return fallback, "local"

        try:
            response = await self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Create concise search instructions for recent public feed "
                            "research. Return up to four queries and useful ranking keywords. "
                            "Do not invent findings."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Topic: {prompt}\nWindow: the last 30 days",
                    },
                ],
                text_format=ResearchPlan,
            )
            return response.output_parsed or fallback, "openai"
        except Exception as exc:
            logger.warning("OpenAI planning failed: %s", exc)
            return fallback, "local"

    async def rank_results(
        self, prompt: str, results: list[FeedResult]
    ) -> tuple[list[FeedResult], bool]:
        if not self.client or not results:
            return results, False

        candidates = [
            {
                "candidate_id": result.id,
                "title": result.title,
                "summary": result.summary[:600],
                "source": result.source_name,
                "published_at": (
                    result.published_at.isoformat() if result.published_at else None
                ),
            }
            for result in results[:20]
        ]
        try:
            response = await self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Rank recent feed candidates for the user's topic. Preserve facts, "
                            "write a short neutral summary based only on candidate text, and "
                            "return each candidate_id at most once. Never fabricate a source."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Topic: {prompt}\nCandidates:\n{json.dumps(candidates)}",
                    },
                ],
                text_format=RankedFeed,
            )
            ranked = response.output_parsed
            if not ranked:
                return results, False

            by_id = {item.id: item for item in results}
            enriched: list[FeedResult] = []
            for item in ranked.results:
                candidate = by_id.pop(item.candidate_id, None)
                if candidate:
                    enriched.append(
                        candidate.model_copy(
                            update={
                                "summary": item.summary,
                                "relevance_score": item.relevance_score,
                            }
                        )
                    )
            enriched.extend(by_id.values())
            enriched.sort(
                key=lambda item: item.relevance_score or 0,
                reverse=True,
            )
            return enriched, True
        except Exception as exc:
            logger.warning("OpenAI ranking failed: %s", exc)
            return results, False


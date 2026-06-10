from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=40)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Category name cannot be empty.")
        return normalized


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FeedResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    summary: str
    source_url: HttpUrl | None = None
    source_name: str | None = None
    published_at: datetime | None = None
    category: str
    relevance_score: float | None = Field(default=None, ge=0, le=1)


class ScrapeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    category: str = Field(default="Default", min_length=1, max_length=40)
    days: int = Field(default=30, ge=1, le=30)

    @field_validator("prompt", "category")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


class HistoryRecord(BaseModel):
    id: UUID
    prompt: str
    category: str
    searched_at: datetime
    result_count: int
    results: list[FeedResult]
    warnings: list[str] = Field(default_factory=list)


class ScrapeResponse(BaseModel):
    history: HistoryRecord
    mode: str
    message: str


class ExportRequest(BaseModel):
    prompt: str
    category: str
    searched_at: datetime
    results: list[FeedResult]


class ResearchPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=4)
    keywords: list[str] = Field(default_factory=list, max_length=12)


class RankedResult(BaseModel):
    candidate_id: str
    summary: str
    relevance_score: float = Field(ge=0, le=1)


class RankedFeed(BaseModel):
    results: list[RankedResult]


class ApiMessage(BaseModel):
    message: str
    data: Any | None = None


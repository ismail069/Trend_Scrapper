from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from supabase import Client, create_client

from app.config import Settings
from app.models import Category, FeedResult, HistoryRecord

DEFAULT_CATEGORIES = ("Default", "Trending")


class DataRepository:
    def __init__(self, settings: Settings):
        self.client: Client | None = None
        if settings.supabase_configured:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
            )
        self._lock = Lock()
        self._categories: dict[UUID, Category] = {}
        self._history: dict[UUID, HistoryRecord] = {}
        if not self.client:
            for name in DEFAULT_CATEGORIES:
                self._memory_create_category(name)

    @property
    def storage_mode(self) -> str:
        return "supabase" if self.client else "memory"

    def list_categories(self) -> list[Category]:
        if not self.client:
            return sorted(self._categories.values(), key=lambda item: item.name.lower())
        rows = self.client.table("categories").select("*").order("name").execute().data
        return [Category.model_validate(row) for row in rows]

    def create_category(self, name: str) -> Category:
        if not self.client:
            if any(item.name.lower() == name.lower() for item in self._categories.values()):
                raise HTTPException(status_code=409, detail="Category already exists.")
            return self._memory_create_category(name)
        try:
            row = self.client.table("categories").insert({"name": name}).execute().data[0]
            return Category.model_validate(row)
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Category already exists.") from exc

    def update_category(self, category_id: UUID, name: str) -> Category:
        if not self.client:
            current = self._categories.get(category_id)
            if not current:
                raise HTTPException(status_code=404, detail="Category not found.")
            if any(
                item.id != category_id and item.name.lower() == name.lower()
                for item in self._categories.values()
            ):
                raise HTTPException(status_code=409, detail="Category already exists.")
            updated = current.model_copy(
                update={"name": name, "updated_at": datetime.now(UTC)}
            )
            self._categories[category_id] = updated
            for history_id, record in list(self._history.items()):
                if record.category == current.name:
                    results = [
                        result.model_copy(update={"category": name})
                        for result in record.results
                    ]
                    self._history[history_id] = record.model_copy(
                        update={"category": name, "results": results}
                    )
            return updated
        rows = (
            self.client.table("categories")
            .update({"name": name})
            .eq("id", str(category_id))
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Category not found.")
        return Category.model_validate(rows[0])

    def delete_category(self, category_id: UUID) -> None:
        if not self.client:
            category = self._categories.get(category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")
            if category.name in DEFAULT_CATEGORIES:
                raise HTTPException(status_code=400, detail="Default categories cannot be deleted.")
            if any(item.category == category.name for item in self._history.values()):
                raise HTTPException(
                    status_code=409,
                    detail="Reassign or delete history items using this category first.",
                )
            del self._categories[category_id]
            return

        category_rows = (
            self.client.table("categories")
            .select("name")
            .eq("id", str(category_id))
            .execute()
            .data
        )
        if not category_rows:
            raise HTTPException(status_code=404, detail="Category not found.")
        if category_rows[0]["name"] in DEFAULT_CATEGORIES:
            raise HTTPException(status_code=400, detail="Default categories cannot be deleted.")
        used = (
            self.client.table("search_history")
            .select("id", count="exact")
            .eq("category_id", str(category_id))
            .limit(1)
            .execute()
        )
        if used.count:
            raise HTTPException(
                status_code=409,
                detail="Reassign or delete history items using this category first.",
            )
        self.client.table("categories").delete().eq("id", str(category_id)).execute()

    def save_history(
        self,
        prompt: str,
        category_name: str,
        results: list[FeedResult],
        warnings: list[str],
    ) -> HistoryRecord:
        if not self.client:
            record = HistoryRecord(
                id=uuid4(),
                prompt=prompt,
                category=category_name,
                searched_at=datetime.now(UTC),
                result_count=len(results),
                results=results,
                warnings=warnings,
            )
            with self._lock:
                self._history[record.id] = record
            return record

        categories = (
            self.client.table("categories")
            .select("id,name")
            .ilike("name", category_name)
            .limit(1)
            .execute()
            .data
        )
        if not categories:
            category = self.create_category(category_name)
            category_id = category.id
        else:
            category_id = categories[0]["id"]
        payload = {
            "prompt": prompt,
            "category_id": str(category_id),
            "result_count": len(results),
            "result_payload": [result.model_dump(mode="json") for result in results],
            "warnings": warnings,
        }
        row = self.client.table("search_history").insert(payload).execute().data[0]
        row["category"] = category_name
        row["results"] = row.pop("result_payload")
        return HistoryRecord.model_validate(row)

    def list_history(self) -> list[HistoryRecord]:
        if not self.client:
            return sorted(
                self._history.values(),
                key=lambda item: item.searched_at,
                reverse=True,
            )
        rows = (
            self.client.table("search_history")
            .select("*,categories(name)")
            .order("searched_at", desc=True)
            .execute()
            .data
        )
        return [self._history_from_row(row) for row in rows]

    def get_history(self, history_id: UUID) -> HistoryRecord:
        if not self.client:
            record = self._history.get(history_id)
            if not record:
                raise HTTPException(status_code=404, detail="History item not found.")
            return record
        rows = (
            self.client.table("search_history")
            .select("*,categories(name)")
            .eq("id", str(history_id))
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="History item not found.")
        return self._history_from_row(rows[0])

    def delete_history(self, history_id: UUID) -> None:
        if not self.client:
            if self._history.pop(history_id, None) is None:
                raise HTTPException(status_code=404, detail="History item not found.")
            return
        rows = (
            self.client.table("search_history")
            .delete()
            .eq("id", str(history_id))
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="History item not found.")

    def _memory_create_category(self, name: str) -> Category:
        now = datetime.now(UTC)
        category = Category(id=uuid4(), name=name, created_at=now, updated_at=now)
        self._categories[category.id] = category
        return category

    @staticmethod
    def _history_from_row(row: dict) -> HistoryRecord:
        normalized = dict(row)
        normalized["category"] = normalized.pop("categories")["name"]
        normalized["results"] = [
            {**result, "category": normalized["category"]}
            for result in normalized.pop("result_payload")
        ]
        return HistoryRecord.model_validate(normalized)

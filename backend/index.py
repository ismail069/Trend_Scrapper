from app.main import app


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "app": "Feed Tren Scrapper API",
        "status": "ok",
        "health": "/api/health",
        "docs": "/docs",
    }


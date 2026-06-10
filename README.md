# Feed Tren Scrapper

Feed Tren Scrapper is a mobile-first React and FastAPI app for researching public feed signals from the last 30 days. It saves searches by category, reopens historical result sets, and exports the active research to PDF or DOCX.

The architecture borrows the useful parts of the `last30days-skill` concept: understand a topic before searching, query multiple public sources, rank social signals, preserve source links, and clearly report degraded source coverage.

## 1. Project overview

The app includes:

- A one-hand-friendly prompt and category interface.
- Real public adapters for Hacker News Algolia and Reddit public search.
- OpenAI-assisted search planning, summarization, and relevance ranking.
- A local ranking fallback when OpenAI is not configured or fails.
- Supabase category and history persistence.
- In-memory backend fallback for local development without Supabase.
- Browser `localStorage` persistence for categories, history, and selection.
- Server-generated PDF and DOCX reports.
- Explicit warnings when a live source is unavailable.

Live scraping is limited to the included Hacker News and Reddit adapters. Additional networks such as X, YouTube, TikTok, or general web search require their own approved APIs and should be added as new adapter methods in `backend/app/services/scraper_service.py`. The app does not claim those sources are currently searched.

## 2. Folder structure

```text
Tren Scrapper/
├── backend/
│   ├── app/
│   │   ├── routers/              # Scrape, history, category, export routes
│   │   ├── services/             # OpenAI, source adapters, storage, exports
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   └── models.py
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── .env.example
│   └── package.json
├── supabase/
│   └── schema.sql
└── README.md
```

## 3. Supabase schema

Run [`supabase/schema.sql`](supabase/schema.sql) in the Supabase SQL editor or with the Supabase CLI. It creates:

- `categories`: unique category names and timestamps.
- `search_history`: prompt, category foreign key, search time, result count, JSON result payload, and warnings.
- `ON DELETE RESTRICT` on category references so used categories cannot be deleted.
- `updated_at` triggers.
- Default `Default` and `Trending` rows.
- RLS with no anonymous policies. The backend service-role client is the only database writer.

Do not put the Supabase service-role key in the React app. The publishable key is not a replacement for the backend service-role key.

## 4. Backend implementation

### Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/scrape` | Plan, search, rank, save, and return recent results |
| `GET` | `/api/history` | List saved searches |
| `GET` | `/api/history/{id}` | Read one saved search |
| `DELETE` | `/api/history/{id}` | Delete one saved search |
| `GET` | `/api/categories` | List categories |
| `POST` | `/api/categories` | Create a category |
| `PUT` | `/api/categories/{id}` | Rename a category |
| `DELETE` | `/api/categories/{id}` | Delete an unused custom category |
| `POST` | `/api/export/pdf` | Generate a PDF report |
| `POST` | `/api/export/docx` | Generate a DOCX report |
| `GET` | `/api/health` | Report API and storage status |

### Install

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Fill in `backend/.env`:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5-mini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FRONTEND_ORIGIN=http://localhost:5173
ENABLE_MOCK_RESULTS=false
```

`ENABLE_MOCK_RESULTS=false` is the production-safe default. When set to `true`, a no-results search may return a single item visibly labeled `Demo data`; it is never presented as a live finding.

### OpenAI behavior

`OpenAIService` uses the Responses API with Pydantic structured output:

1. Convert the user topic into up to four search queries and ranking keywords.
2. Search live adapters independently and tolerate individual source failures.
3. Ask the model to rank and summarize only the returned candidates.
4. Preserve original IDs, dates, and source URLs.
5. Fall back to local keyword and recency scoring if the API is unavailable.

The model is configurable through `OPENAI_MODEL`; no model name or API key is shipped to the browser.

## 5. Frontend implementation

The frontend uses React functional components and hooks only. `useLocalStorage` persists:

- `fts.categories`
- `fts.history`
- `fts.selectedCategory`

Remote API data is merged into local state on startup. The UI remains useful for reopening locally cached searches when backend sync is unavailable.

Install:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The default API URL is `http://localhost:8000`. Set `VITE_API_URL` when the backend is hosted elsewhere.

## 6. Export implementation

The frontend sends the active prompt, category, search timestamp, and result list to `/api/export/pdf` or `/api/export/docx`. The API returns a binary attachment:

- PDF is generated by ReportLab.
- DOCX is generated by `python-docx`.
- Both include app name, search metadata, result titles, summaries, source names, URLs, and publication dates.

The browser creates a temporary object URL and immediately downloads the returned blob. Export generation stays on the backend, so document libraries and formatting logic are not added to the mobile bundle.

## 7. Run instructions

Start the API:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Start React in another terminal:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. API documentation is available at `http://localhost:8000/docs`.

Run checks:

```powershell
cd backend
pytest

cd ..\frontend
npm run build
```

### Deploy to Vercel

Create two Vercel projects from the same GitHub repository.

Backend project:

- Root Directory: `backend`
- Framework Preset: `FastAPI`
- Environment variables: `OPENAI_API_KEY`, `OPENAI_MODEL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `FRONTEND_ORIGIN`, and `ENABLE_MOCK_RESULTS`
- Verify the deployment at `/api/health` or `/docs`

Frontend project:

- Root Directory: `frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment variable: `VITE_API_URL=https://your-backend-project.vercel.app`

Deploy the backend first. After the frontend is deployed, set the backend
`FRONTEND_ORIGIN` to the exact frontend production origin, without a trailing
slash, and redeploy the backend.

Do not deploy the repository root as a single Vercel project. The repository is
a monorepo, so a root deployment cannot infer whether it should build the Vite
frontend or the FastAPI backend.

## 8. Notes and assumptions

- No authentication is included, as requested.
- The backend must be protected before exposing it publicly because its endpoints can consume OpenAI credits.
- Supabase is optional during local development. Without both Supabase variables, the API uses process-memory storage and reports `"storage": "memory"` from `/api/health`.
- Browser history still persists across refreshes through `localStorage`; backend memory history does not survive a server restart.
- Reddit may rate-limit or reject traffic from some hosting providers. That failure is returned as a warning while other adapters continue.
- The current source layer is intentionally small and transparent. Add new live integrations as adapters; do not ask the model to fabricate feed items.
- Never commit `.env`. Credentials shared in chat or logs should be rotated before a production launch.

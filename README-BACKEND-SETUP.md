# SkillSwap – Frontend / Backend split

## Project structure

- `frontend/` – existing HTML, CSS, JavaScript and images (preserved)
- `backend/` – FastAPI REST API and SQLite database
- `frontend/js/api.js` – browser API helper for connecting to FastAPI

## Run backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:JWT_SECRET = "replace-this-with-a-long-random-secret"
$env:FRONTEND_ORIGIN = "http://localhost:5500"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8001/docs

## Run frontend

Open a second PowerShell window:

```powershell
cd frontend
py -m http.server 5500 --bind 127.0.0.1
```

Frontend: http://127.0.0.1:5500

## Important current scope

The frontend includes a landing page, API-backed registration and login forms, and a static marketplace. The login form sends credentials to the API on port 8001; the marketplace's sample courses and exchange listings are not loaded from the API, and its course checkout remains a separate Java demo with no real charges.

The backend is a development starter, not production-ready. Before public deployment, add database migrations, stricter upload content inspection, rate limiting, secure secret management, HTTPS, automated tests, and a fully specified mutual-consent exchange workflow. The repeat-once rule also needs a dedicated repeat endpoint and persistent original-exchange linkage before production.

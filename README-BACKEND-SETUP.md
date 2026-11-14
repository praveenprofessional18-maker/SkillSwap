# SkillSwap setup (Windows PowerShell)

For the full feature and API reference, see [README.md](./README.md).

## Install

From the repository root, use Python 3.12:

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Set a private `JWT_SECRET` of at least 32 characters in `.env`. Keep this file out of source control.

## Start the backend

In the first PowerShell window:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file ..\.env
```

The API is at <http://127.0.0.1:8000>, health check at <http://127.0.0.1:8000/api/health>, and API documentation at <http://127.0.0.1:8000/docs>.

## Start the frontend

In a second PowerShell window:

```powershell
Set-Location frontend
py -m http.server 5500
```

Open <http://localhost:5500>. Registration is at `register.html`; after login, the new authenticated dashboard at `dashboard.html` is the landing page.

## Run tests

From the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use a temporary SQLite database and do not modify the local development database.

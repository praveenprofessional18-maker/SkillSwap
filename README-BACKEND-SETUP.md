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
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
Swagger: http://127.0.0.1:8000/docs

## Run frontend

Open a second PowerShell window:

```powershell
cd frontend
py -m http.server 5500
```

Frontend: http://localhost:5500

Add this script before `</body>` in `frontend/index.html` if you want pages to call the API:

```html
<script src="js/api.js"></script>
```

Example:

```javascript
const posts = await window.SkillSwapAPI.posts();
console.log(posts);
```

## Important current scope

The uploaded frontend is currently a static landing page with category filters and sample course cards. It does not yet contain registration, login, dashboard, post creation, or exchange forms. The API helper is provided, but the UI must be extended to expose those features.

The backend is a development starter, not production-ready. Before public deployment, add database migrations, stricter upload content inspection, rate limiting, secure secret management, HTTPS, automated tests, and a fully specified mutual-consent exchange workflow. The repeat-once rule also needs a dedicated repeat endpoint and persistent original-exchange linkage before production.

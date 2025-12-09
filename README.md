# FastAPI Calculator (Login + BREAD + Web UI) + Pytest + CI + Docker Hub CD

## Why your earlier errors happened (fixed here)
- **`ModuleNotFoundError: No module named 'app'`** → happens when pytest runs from the wrong directory / PYTHONPATH missing.  
  ✅ Fixed by adding `tests/conftest.py` that inserts project root into `sys.path`.
- **bcrypt/passlib Windows issues** (`bcrypt.__about__` + 72-byte limit)  
  ✅ This project uses **Passlib `pbkdf2_sha256`** (pure Python), not bcrypt.
- **TestClient requires httpx**  
  ✅ `httpx` is included in `requirements.txt`.

---

## Run in VS Code on Windows

1) **Open the project folder** (the folder that contains `app/`, `tests/`, `requirements.txt`)

2) Create + activate venv:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Install:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

4) Start server:
```powershell
uvicorn app.main:app --reload
```

Open:
- **Calculator UI:** http://127.0.0.1:8000/
- **Swagger docs:** http://127.0.0.1:8000/docs

### Demo login
- username: `demo`
- password: `Test123!`

> If you ran older versions and have an `app.db` file, delete it once before running.

---

## Run integration tests + coverage
From the project root:
```powershell
pytest --cov=app --cov-report=term-missing --cov-fail-under=100
```

---

## Manual checks via OpenAPI (/docs)

### 1) Login
- POST `/users/login`
- Use form fields:
  - username: `demo`
  - password: `Test123!`
- Copy `access_token`

### 2) Authorize
Click **Authorize** (top right) and paste:
```
Bearer <your_access_token>
```

### 3) Use calculations BREAD endpoints
- POST `/calculations/` (add)
- GET `/calculations/` (browse)
- GET `/calculations/{id}` (read)
- PUT `/calculations/{id}` (edit)
- DELETE `/calculations/{id}` (delete)

---

## Docker (local)
Build + run:
```powershell
docker compose up --build
```
Open http://127.0.0.1:8000

---

## CI + Docker Hub deployment (GitHub Actions)

### CI
`.github/workflows/ci.yml` runs pytest + coverage on every push/PR.

### Docker Hub CD
`.github/workflows/dockerhub.yml` builds + pushes an image **only if secrets exist**.


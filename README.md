# Login Management Service (Minako)

Three REST endpoints:
- `POST /auth/login` → `{ access_token, refresh_token }`
- `POST /auth/refresh` → `{ access_token }`
- `POST /auth/logout` → `{ "message": "successfully logout" }`
- Health: `GET /health` → `{ "status":"ok" }`

## Run (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET="super-secret-key"
python app.py  # or: uvicorn app:app --reload --port 8000
```

## Test
```bash
pytest -q
```

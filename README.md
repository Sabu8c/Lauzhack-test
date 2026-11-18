# Lauzhack Test App

Minimal end-to-end stack to validate deployment: **static frontend on Vercel → Python API on Railway → Postgres on Supabase.**

## Layout

```
frontend/   static HTML/CSS/JS (no build step) -> Vercel
api/        FastAPI + psycopg (Python 3.11)    -> Railway
db/         schema.sql + seed.sql              -> Supabase
```

## Contract (frozen — agents must not change it)

Table `items` (Supabase Postgres, schema `public`):

| column       | type          | notes                          |
|--------------|---------------|--------------------------------|
| id           | bigserial PK  |                                |
| name         | text not null | 1..120 chars                   |
| created_at   | timestamptz   | default now()                  |

API (base URL = Railway public URL):

| method | path          | body              | response                       |
|--------|---------------|-------------------|--------------------------------|
| GET    | `/health`     | –                 | `{"status":"ok","db":true}`    |
| GET    | `/items`      | –                 | `{"items":[{id,name,created_at}]}` |
| POST   | `/items`      | `{"name":"..."}`  | `201 {"item":{id,name,created_at}}` |

- CORS: allow origin from env `ALLOWED_ORIGIN` (the Vercel URL), plus `*` fallback.
- Env: `DATABASE_URL` (Supabase pooler URI, sslmode=require), `ALLOWED_ORIGIN`.
- Frontend reads API base from `window.API_BASE` set in `frontend/config.js`.

## Local run

```
cd api && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
uvicorn main:app --reload   # http://127.0.0.1:8000
python3 -m http.server 5173 --directory frontend   # http://127.0.0.1:5173
```

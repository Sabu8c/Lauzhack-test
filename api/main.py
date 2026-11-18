import os
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel, Field

app = FastAPI(title="Lauzhack API")

# CORS setup
allowed_origins_env = os.getenv("ALLOWED_ORIGIN", "*")
if allowed_origins_env == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def get_supabase_headers(prefer: Optional[str] = None) -> Dict[str, str]:
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def ping_db() -> bool:
    try:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if not supabase_url:
            return False
        url = f"{supabase_url}/rest/v1/items?select=id&limit=1"
        headers = get_supabase_headers()
        res = httpx.get(url, headers=headers, timeout=5.0)
        return res.status_code == 200
    except Exception:
        return False


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


@app.get("/health")
def health():
    return {"status": "ok", "db": ping_db()}


@app.get("/items")
def get_items():
    try:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")
        url = f"{supabase_url}/rest/v1/items?select=id,name,created_at&order=id"
        headers = get_supabase_headers()
        res = httpx.get(url, headers=headers, timeout=10.0)
        res.raise_for_status()
        return {"items": res.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/items", status_code=201)
def create_item(payload: ItemCreate):
    try:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")
        url = f"{supabase_url}/rest/v1/items?select=id,name,created_at&order=id"
        headers = get_supabase_headers(prefer="return=representation")
        res = httpx.post(url, json={"name": payload.name}, headers=headers, timeout=10.0)
        res.raise_for_status()
        data = res.json()
        item = data[0] if isinstance(data, list) else data
        return {"item": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

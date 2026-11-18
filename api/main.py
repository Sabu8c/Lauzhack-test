import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row

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


def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(db_url, row_factory=dict_row)


def ping_db() -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return True
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
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, created_at FROM public.items ORDER BY id ASC;"
                )
                rows = cur.fetchall()
                items = [
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "created_at": (
                            row["created_at"].isoformat()
                            if hasattr(row["created_at"], "isoformat")
                            else str(row["created_at"])
                        ),
                    }
                    for row in rows
                ]
                return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/items", status_code=201)
def create_item(payload: ItemCreate):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.items (name) VALUES (%s) RETURNING id, name, created_at;",
                    (payload.name,),
                )
                row = cur.fetchone()
                conn.commit()
                return {
                    "item": {
                        "id": row["id"],
                        "name": row["name"],
                        "created_at": (
                            row["created_at"].isoformat()
                            if hasattr(row["created_at"], "isoformat")
                            else str(row["created_at"])
                        ),
                    }
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

# API Service

## Environment Variables
- `SUPABASE_URL`: Supabase project URL (e.g. `https://xyz.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `ALLOWED_ORIGIN`: Allowed CORS origins, comma-separated (default: `*`)
- `PORT`: Port to listen on (default: 8000)

## Run Locally
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
uvicorn main:app --reload

## Endpoints
curl -s http://localhost:8000/health
curl -s http://localhost:8000/items
curl -s -X POST http://localhost:8000/items -H "Content-Type: application/json" -d '{"name":"first item"}'

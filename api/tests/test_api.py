import os
import pytest
from fastapi.testclient import TestClient
import httpx
import main
from main import app

client = TestClient(app)

DUMMY_URL = "https://example.supabase.co"
DUMMY_KEY = "test-service-role-key"


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", DUMMY_URL)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", DUMMY_KEY)


def test_health_db_disconnected(monkeypatch):
    def mock_get(url, *args, **kwargs):
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", mock_get)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": False}


def test_health_db_connected(monkeypatch):
    def mock_get(url, *args, **kwargs):
        assert url == f"{DUMMY_URL}/rest/v1/items?select=id&limit=1"
        assert kwargs["headers"]["apikey"] == DUMMY_KEY
        assert kwargs["headers"]["Authorization"] == f"Bearer {DUMMY_KEY}"
        return httpx.Response(200, json=[{"id": 1}], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", mock_get)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}


def test_get_items(monkeypatch):
    recorded_calls = []

    def mock_get(url, *args, **kwargs):
        recorded_calls.append((url, kwargs))
        return httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "name": "first item",
                    "created_at": "2026-01-01T12:00:00+00:00",
                },
                {
                    "id": 2,
                    "name": "second item",
                    "created_at": "2026-01-01T13:00:00+00:00",
                },
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    response = client.get("/items")
    assert response.status_code == 200
    assert len(recorded_calls) == 1
    call_url, call_kwargs = recorded_calls[0]
    assert call_url == f"{DUMMY_URL}/rest/v1/items?select=id,name,created_at&order=id"
    assert call_kwargs["headers"]["apikey"] == DUMMY_KEY
    assert call_kwargs["headers"]["Authorization"] == f"Bearer {DUMMY_KEY}"

    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["items"][0] == {
        "id": 1,
        "name": "first item",
        "created_at": "2026-01-01T12:00:00+00:00",
    }
    assert data["items"][1] == {
        "id": 2,
        "name": "second item",
        "created_at": "2026-01-01T13:00:00+00:00",
    }


def test_get_items_error(monkeypatch):
    def mock_get(url, *args, **kwargs):
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", mock_get)
    response = client.get("/items")
    assert response.status_code == 500


def test_post_item_success(monkeypatch):
    recorded_calls = []

    def mock_post(url, *args, **kwargs):
        recorded_calls.append((url, kwargs))
        return httpx.Response(
            201,
            json=[
                {
                    "id": 42,
                    "name": "new item",
                    "created_at": "2026-01-01T12:00:00+00:00",
                }
            ],
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    response = client.post("/items", json={"name": "new item"})
    assert response.status_code == 201
    assert len(recorded_calls) == 1
    call_url, call_kwargs = recorded_calls[0]
    assert call_url == f"{DUMMY_URL}/rest/v1/items?select=id,name,created_at&order=id"
    assert call_kwargs["headers"]["apikey"] == DUMMY_KEY
    assert call_kwargs["headers"]["Authorization"] == f"Bearer {DUMMY_KEY}"
    assert call_kwargs["headers"]["Prefer"] == "return=representation"
    assert call_kwargs["json"] == {"name": "new item"}

    assert response.json() == {
        "item": {
            "id": 42,
            "name": "new item",
            "created_at": "2026-01-01T12:00:00+00:00",
        }
    }


def test_post_item_error(monkeypatch):
    def mock_post(url, *args, **kwargs):
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", mock_post)
    response = client.post("/items", json={"name": "new item"})
    assert response.status_code == 500


@pytest.mark.parametrize("name", ["a", "a" * 120])
def test_post_item_boundary_valid_names(monkeypatch, name):
    def mock_post(url, *args, **kwargs):
        return httpx.Response(
            201,
            json=[
                {
                    "id": 1,
                    "name": name,
                    "created_at": "2026-01-01T12:00:00+00:00",
                }
            ],
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    response = client.post("/items", json={"name": name})
    assert response.status_code == 201
    assert response.json()["item"]["name"] == name


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"name": ""},
        {"name": "a" * 121},
        {},
        {"wrong_key": "abc"},
    ],
)
def test_post_item_invalid_name(invalid_payload):
    response = client.post("/items", json=invalid_payload)
    assert response.status_code == 422


def test_post_item_invalid_json():
    response = client.post(
        "/items",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in (400, 422)


def test_cors_options():
    response = client.options(
        "/items",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("*", "http://example.com")

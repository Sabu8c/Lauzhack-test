from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
import main
from main import app

client = TestClient(app)


class MockCursor:
    def __init__(self, fetchall_data=None, fetchone_data=None):
        self.fetchall_data = fetchall_data or []
        self.fetchone_data = fetchone_data
        self.executed_queries = []

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def fetchall(self):
        return self.fetchall_data

    def fetchone(self):
        return self.fetchone_data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_health_db_disconnected(monkeypatch):
    monkeypatch.setattr(main, "ping_db", lambda: False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": False}


def test_health_db_connected(monkeypatch):
    monkeypatch.setattr(main, "ping_db", lambda: True)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}


def test_get_items(monkeypatch):
    mock_cursor = MockCursor(
        fetchall_data=[
            {
                "id": 1,
                "name": "first item",
                "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            },
            {
                "id": 2,
                "name": "second item",
                "created_at": "2026-01-01T13:00:00+00:00",
            },
        ]
    )
    monkeypatch.setattr(main, "get_db_connection", lambda: MockConnection(mock_cursor))

    response = client.get("/items")
    assert response.status_code == 200
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


def test_post_item_success(monkeypatch):
    mock_cursor = MockCursor(
        fetchone_data={
            "id": 42,
            "name": "new item",
            "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    )
    mock_conn = MockConnection(mock_cursor)
    monkeypatch.setattr(main, "get_db_connection", lambda: mock_conn)

    response = client.post("/items", json={"name": "new item"})
    assert response.status_code == 201
    assert response.json() == {
        "item": {
            "id": 42,
            "name": "new item",
            "created_at": "2026-01-01T12:00:00+00:00",
        }
    }
    assert mock_conn.committed is True


@pytest.mark.parametrize("name", ["a", "a" * 120])
def test_post_item_boundary_valid_names(monkeypatch, name):
    mock_cursor = MockCursor(
        fetchone_data={
            "id": 1,
            "name": name,
            "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    )
    monkeypatch.setattr(main, "get_db_connection", lambda: MockConnection(mock_cursor))

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

import pytest

from app.core.config import settings

from .conftest import SAMPLE_TEXT

KEY = "test-secret-key"

PROTECTED = [
    ("get", "/documents"),
    ("delete", "/documents/some-id"),
    ("get", "/summary-list"),
    ("post", "/summaries/some-id/edit"),
    ("get", "/audio-list"),
    ("get", "/audios/some-id/download"),
    ("get", "/search?q=test"),
    ("get", "/v1/models"),
    ("post", "/api/testing/reset-db"),
]


@pytest.fixture()
def api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", KEY)
    return KEY


@pytest.mark.parametrize("method,path", PROTECTED)
def test_routes_reject_missing_key(client, api_key, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


@pytest.mark.parametrize("method,path", PROTECTED)
def test_routes_reject_wrong_key(client, api_key, method, path):
    response = getattr(client, method)(path, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_valid_key_allows_list_and_delete(client, api_key):
    headers = {"X-API-Key": api_key}
    uploaded = client.post(
        "/documents/upload",
        files={"file": ("doc.txt", SAMPLE_TEXT, "text/plain")},
        headers=headers,
    )
    assert uploaded.status_code == 200, uploaded.text
    doc_id = uploaded.json()["id"]

    assert client.delete(f"/documents/{doc_id}").status_code == 401

    listed = client.get("/documents", headers=headers)
    assert listed.status_code == 200
    assert [d["id"] for d in listed.json()["data"]] == [doc_id]

    assert client.delete(f"/documents/{doc_id}", headers=headers).status_code == 200


def test_production_without_key_fails_closed(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")
    monkeypatch.setattr(settings, "ENV", "PRODUCTION")
    assert client.get("/documents").status_code == 503
    assert client.delete("/documents/some-id").status_code == 503


def test_cors_preflight_allows_api_key_header(client, api_key):
    response = client.options(
        "/documents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()

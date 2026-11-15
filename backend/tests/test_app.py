import threading

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_unhandled_errors_return_500_error_payload(client):
    from app.main import app

    @app.get("/v1/_boom")
    async def boom():
        raise RuntimeError("kaboom")

    try:
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            response = raw_client.get("/v1/_boom")
    finally:
        app.router.routes = [
            r for r in app.router.routes if getattr(r, "path", "") != "/v1/_boom"
        ]

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "kaboom" not in response.text


def test_services_are_cached_singletons():
    from app.dependencies import get_audio_service, get_summarization_service

    assert get_summarization_service() is get_summarization_service()
    assert get_audio_service() is get_audio_service()


def test_summarization_runs_off_the_event_loop(client, upload):
    from app.dependencies import get_summarization_service
    from app.main import app

    calls = []

    class RecordingSummarizer:
        def summarize_text(self, text, format_type="short_text"):
            calls.append(threading.current_thread().name)
            return "A recorded summary for the test.", 0.1, 10

        def get_model_name(self):
            return "recording"

    document_id = upload()
    app.dependency_overrides[get_summarization_service] = RecordingSummarizer

    response = client.post(
        f"/documents/{document_id}/summarize", json={"summary_type": "short_text"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["llm_model"] == "recording"
    assert calls and "AnyIO worker thread" in calls[0]


def test_cors_allows_only_used_methods(client):
    headers = {"Origin": "http://localhost:5173"}

    allowed = client.options(
        "/documents/x",
        headers={**headers, "Access-Control-Request-Method": "DELETE"},
    )
    rejected = client.options(
        "/documents/x",
        headers={**headers, "Access-Control-Request-Method": "PUT"},
    )

    assert allowed.status_code == 200
    assert rejected.status_code == 400


def test_database_url_is_required(monkeypatch):
    from app.core.config import Settings

    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_debug_defaults_to_false(monkeypatch):
    from app.core.config import Settings

    monkeypatch.delenv("DEBUG", raising=False)
    assert Settings(_env_file=None, DATABASE_URL="postgresql://x/y").DEBUG is False


def test_summary_mutations_return_updated_summary(client, upload):
    document_id = upload()
    created = client.post(f"/documents/{document_id}/summarize", json={}).json()

    edited = client.post(
        f"/summaries/{created['id']}/edit", json={"edited_text": "Edited text here"}
    )
    approved = client.post(
        f"/summaries/{created['id']}/approval",
        json={"status": "approved", "custom_name": "Renamed"},
    )
    regenerated = client.post(f"/summaries/{created['id']}/regenerate", json={})

    assert edited.status_code == 200
    assert edited.json()["message"] == "Summary edited successfully"
    assert edited.json()["summary_text"] == "Edited text here"
    assert edited.json()["llm_model"] == "human-edited"
    assert approved.json()["approval_status"] == "approved"
    assert approved.json()["document_filename"] == "Renamed"
    assert regenerated.json()["message"] == "Summary regenerated successfully"
    assert regenerated.json()["approval_status"] == "pending"
    assert regenerated.json()["custom_name"] == "Renamed"


def test_upload_over_size_limit_returns_413(client, monkeypatch):
    from starlette.datastructures import UploadFile

    from app.core.config import settings
    from app.routers import documents

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 2 * 1024 * 1024)
    reads = []
    original_read = UploadFile.read

    async def tracking_read(self, size=-1):
        reads.append(size)
        return await original_read(self, size)

    monkeypatch.setattr(UploadFile, "read", tracking_read)

    oversized = b"a" * (5 * 1024 * 1024)
    response = client.post(
        "/documents/upload", files={"file": ("big.txt", oversized, "text/plain")}
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max 2 MB."
    assert reads and all(0 < size <= documents.UPLOAD_CHUNK_SIZE for size in reads)
    assert len(reads) == 3
    assert client.get("/documents").json()["total"] == 0

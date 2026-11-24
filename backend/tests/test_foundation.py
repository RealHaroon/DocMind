from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_settings_can_be_updated() -> None:
    payload = {
        "provider": "groq",
        "gemini_model": "gemini-test",
        "groq_model": "groq-test",
        "rag_top_k": 7,
        "theme": "light",
    }
    with TestClient(app) as client:
        response = client.put("/api/settings", json=payload)

    assert response.status_code == 200
    assert response.json()["provider"] == "groq"
    assert response.json()["rag_top_k"] == 7
    assert "api_key" not in response.text


def pytest_sessionfinish() -> None:
    path = Path(get_settings().database_url.removeprefix("sqlite:///"))
    path.unlink(missing_ok=True)


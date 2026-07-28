from fastapi.testclient import TestClient

from app.interface.api.app import create_app


def test_liveness_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

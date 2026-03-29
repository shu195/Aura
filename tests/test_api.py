from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def auth_headers(username: str = "admin", password: str = "admin123") -> dict[str, str]:
    token_res = client.post("/v1/auth/token", json={"username": username, "password": password})
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_conversation_turn() -> None:
    payload = {
        "user_id": "u1",
        "session_id": "s1",
        "message": {
            "role": "user",
            "content": "I feel stressed and stuck today",
            "modality": "text",
            "metadata": {},
        },
    }
    response = client.post("/v1/conversation/turn", json=payload, headers=auth_headers())
    body = response.json()

    assert response.status_code == 200
    assert body["user_id"] == "u1"
    assert "response_text" in body
    assert body["safety"]["allowed"] is True


def test_consent_opt_out_blocks_personalized_processing() -> None:
    update_payload = {
        "user_id": "u_opt_out",
        "gpc_enabled": True,
        "one_click_opt_out": True,
        "voice_enabled": True,
        "vision_enabled": False,
    }
    client.post("/v1/consent/update", json=update_payload, headers=auth_headers())

    message_payload = {
        "user_id": "u_opt_out",
        "session_id": "s_opt_out",
        "message": {
            "role": "user",
            "content": "Help me plan my week",
            "modality": "text",
            "metadata": {},
        },
    }
    response = client.post("/v1/conversation/turn", json=message_payload, headers=auth_headers())
    assert response.status_code == 200
    assert "privacy controls" in response.json()["response_text"].lower()


def test_purge_endpoint_returns_receipt() -> None:
    store_payload = {
        "user_id": "u2",
        "session_id": "s2",
        "role": "user",
        "content": "temporary memory",
        "retention_days": 30,
        "purpose": "wellness",
        "created_at": "2026-03-29T00:00:00Z",
    }
    client.post("/v1/memory/store", json=store_payload, headers=auth_headers())

    response = client.post(
        "/v1/memory/purge", json={"user_id": "u2", "reason": "user_request"}, headers=auth_headers()
    )
    body = response.json()

    assert response.status_code == 200
    assert body["deleted_records"] >= 1
    assert body["receipt_id"].startswith("purge-u2-")


def test_protected_routes_require_auth() -> None:
    payload = {
        "user_id": "u401",
        "session_id": "s401",
        "message": {
            "role": "user",
            "content": "hello",
            "modality": "text",
            "metadata": {},
        },
    }
    response = client.post("/v1/conversation/turn", json=payload)
    assert response.status_code == 401


def test_insufficient_scope_for_observability() -> None:
    token_res = client.post("/v1/auth/token", json={"username": "analyst", "password": "analyst123"})
    token = token_res.json()["access_token"]
    response = client.get("/v1/observability/events", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

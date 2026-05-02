from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4


BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app import app  # noqa: E402


def _post_chat(client, message: str, session_id: str) -> dict:
    response = client.post(
        "/api/chat",
        json={
            "message": message,
            "session_id": session_id,
        },
    )
    assert response.status_code == 200
    payload = response.get_json() or {}
    assert "reply" in payload
    return payload


def test_vague_message_requests_more_information() -> None:
    client = app.test_client()
    payload = _post_chat(client, "I have a rash", str(uuid4()))

    assert payload["needs_more_info"] is True
    assert payload["follow_up_questions"]
    assert payload["predicted_disease"] is None or isinstance(
        payload["predicted_disease"], str
    )


def test_detailed_symptom_message_returns_prediction() -> None:
    client = app.test_client()
    payload = _post_chat(
        client,
        "Its on my arms, very itchy and red for 2 weeks",
        str(uuid4()),
    )

    assert payload["predicted_disease"]
    assert 0.0 <= float(payload["confidence"]) <= 1.0
    assert payload["confidence_level"] in {"high", "medium", "low", "none"}


def test_treatment_followup_preserves_session_context() -> None:
    client = app.test_client()
    session_id = str(uuid4())

    first = _post_chat(
        client,
        "I have thick silvery scales on my elbows and knees, been there for months",
        session_id,
    )
    follow_up = _post_chat(client, "What treatment should I use?", session_id)

    assert first["predicted_disease"]
    assert follow_up["predicted_disease"] == first["predicted_disease"]
    assert isinstance(follow_up["recommended_treatments"], list)
    assert "treat" in follow_up["reply"].lower() or "common" in follow_up["reply"].lower()


def test_greeting_starts_assistant_conversation() -> None:
    client = app.test_client()
    payload = _post_chat(client, "Hello!", str(uuid4()))
    reply = payload["reply"].lower()

    assert "hello" in reply or "symptom" in reply or "describe" in reply
    assert payload["session_id"]

from datetime import datetime
from pathlib import Path
import importlib.util
import json
import pytest

spec = importlib.util.spec_from_file_location(
    "professor_news_telegram",
    Path(__file__).parents[1] / "send-professor-news-update-to-telegram.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_successful_send_updates_lecturer_news_history(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    history_path.write_text(json.dumps({
        "lecturers": {}
    }), encoding="utf-8")
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    monkeypatch.setattr(
        mod,
        "notification_timestamp",
        lambda: "2026-10-03T11:11:24+00:00"
    )
    message_id = mod.send_notification(
        "Mario Rossi",
        "lecturer-1",
        "https://example.test/lecturer",
        "https://example.test/commit",
        history_path,
        "token",
        "chat"
    )

    history = json.loads(history_path.read_text())
    assert message_id == 42
    assert calls[0][0] == "sendMessage"
    assert history["lecturers"]["lecturer-1"] == {
        "name": "Mario Rossi",
        "notifications": {
            "news": {
                "sent_at": "2026-10-03T11:11:24+00:00",
                "telegram_message_id": 42
            }
        }
    }
    assert datetime.fromisoformat(
        history["lecturers"]["lecturer-1"]["notifications"]["news"]["sent_at"]
    ).tzinfo is not None


def test_repeated_send_replaces_only_latest_news_notification(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    history_path.write_text(json.dumps({
        "courses": {},
        "lecturers": {
            "lecturer-1": {
                "name": "Old Name",
                "notifications": {
                    "news": {
                        "sent_at": "2026-10-01T08:00:00+00:00",
                        "telegram_message_id": 10
                    }
                }
            },
            "lecturer-2": {
                "name": "Other Lecturer",
                "notifications": {
                    "news": {
                        "sent_at": "2026-10-02T08:00:00+00:00",
                        "telegram_message_id": 20
                    }
                }
            }
        }
    }), encoding="utf-8")

    monkeypatch.setattr(mod, "call_telegram", lambda *args: {"message_id": 43})
    monkeypatch.setattr(
        mod,
        "notification_timestamp",
        lambda: "2026-10-03T12:00:00+00:00"
    )
    mod.send_notification(
        "Mario Rossi",
        "lecturer-1",
        "file",
        "commit",
        history_path,
        "token",
        "chat"
    )

    history = json.loads(history_path.read_text())
    assert history["lecturers"]["lecturer-1"]["name"] == "Mario Rossi"
    assert history["lecturers"]["lecturer-1"]["notifications"]["news"]["telegram_message_id"] == 43
    assert history["lecturers"]["lecturer-2"]["notifications"]["news"]["telegram_message_id"] == 20


def test_failed_send_does_not_update_history(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    original = {"lecturers": {}}
    history_path.write_text(json.dumps(original), encoding="utf-8")

    def fail_call(*args):
        raise requests_error

    requests_error = mod.requests.RequestException("send failed")
    monkeypatch.setattr(mod, "call_telegram", fail_call)

    with pytest.raises(mod.requests.RequestException):
        mod.send_notification(
            "Mario Rossi",
            "lecturer-1",
            "file",
            "commit",
            history_path,
            "token",
            "chat"
        )

    assert json.loads(history_path.read_text()) == original


def test_edit_updates_message_without_touching_history(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    original = {"lecturers": {}}
    history_path.write_text(json.dumps(original), encoding="utf-8")
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    mod.edit_notification(
        "Mario Rossi",
        "file",
        "final-commit",
        42,
        "token",
        "chat"
    )

    assert calls == [("editMessageText", {
        "chat_id": "chat",
        "message_id": 42,
        "text": mod.format_message("Mario Rossi", "file", "final-commit"),
        "parse_mode": "HTML"
    })]
    assert json.loads(history_path.read_text()) == original


class FakeResponse:
    def __init__(self, status_code, result, text=""):
        self.status_code = status_code
        self.result = result
        self.text = text

    def json(self):
        return self.result

    def raise_for_status(self):
        raise mod.requests.RequestException(self.text)


def test_successful_telegram_request_preserves_console_output(monkeypatch, capsys):
    response = FakeResponse(200, {"ok": True, "result": {"message_id": 42}})
    monkeypatch.setattr(mod.requests, "post", lambda *args, **kwargs: response)

    result = mod.call_telegram("sendMessage", "token", {"chat_id": "chat"})

    assert result == {"message_id": 42}
    assert capsys.readouterr().out == "Message sent successfully!\n"


def test_failed_telegram_request_preserves_console_output(monkeypatch, capsys):
    response = FakeResponse(500, {}, "server error")
    monkeypatch.setattr(mod.requests, "post", lambda *args, **kwargs: response)

    with pytest.raises(mod.requests.RequestException):
        mod.call_telegram("sendMessage", "token", {"chat_id": "chat"})

    assert capsys.readouterr().out == "Failed to send message: server error\n"


def test_send_mode_writes_message_id_without_extra_output(tmp_path, monkeypatch, capsys):
    message_id_path = tmp_path / "message-id.txt"
    monkeypatch.setattr(mod, "send_notification", lambda *args: 42)
    monkeypatch.setattr(mod.sys, "argv", [
        "send-professor-news-update-to-telegram.py",
        "send",
        "Mario Rossi",
        "file",
        "commit",
        "lecturer-1",
        "history.json",
        "token",
        "chat",
        str(message_id_path)
    ])

    mod.main()

    assert message_id_path.read_text(encoding="utf-8") == "42"
    assert capsys.readouterr().out == ""

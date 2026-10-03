from pathlib import Path
import importlib.util
import json
from datetime import datetime

spec = importlib.util.spec_from_file_location(
    "telegram_notifications",
    Path(__file__).parents[1] / "send-course-announcement-update-to-telegram.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def event(course_name, course_id, language, url):
    return {
        "fingerprint": "same-content",
        "title": "Shared announcement",
        "course_name": course_name,
        "course_id": course_id,
        "language": language,
        "url": url
    }


def write_events(path, events):
    path.write_text("".join(json.dumps(item) + "\n" for item in events), encoding="utf-8")


def test_simultaneous_courses_are_sent_in_one_message(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text("{}\n", encoding="utf-8")
    write_events(events_path, [
        event("Informatica", "33503", "it", "https://example.test/33503#announcement-1"),
        event("ACSAI", "33502", "en", "https://example.test/33502#announcement-2")
    ])
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    assert len(calls) == 1
    assert calls[0][0] == "sendMessage"
    assert "Informatica (33503) [IT]" in calls[0][1]["text"]
    assert "ACSAI (33502) [EN]" in calls[0][1]["text"]
    assert json.loads(registry_path.read_text())["same-content"]["message_id"] == 42
    history = json.loads(history_path.read_text())
    assert history["courses"]["33503"]["notifications"]["announcements"]["telegram_message_id"] == 42
    sent_at = history["courses"]["33503"]["notifications"]["announcements"]["sent_at"]
    assert sent_at.endswith("+00:00")
    assert datetime.fromisoformat(sent_at).tzinfo is not None


def test_later_course_edits_existing_message(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text(json.dumps({
        "same-content": {
            "title": "Shared announcement",
            "message_id": 42,
            "courses": [{
                "name": "Informatica",
                "id": "33503",
                "language": "it",
                "url": "https://example.test/33503#announcement-1"
            }]
        }
    }), encoding="utf-8")
    write_events(events_path, [event("ACSAI", "33502", "en", "https://example.test/33502#announcement-2")])
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    assert len(calls) == 1
    assert calls[0][0] == "editMessageText"
    assert calls[0][1]["message_id"] == 42
    assert "Informatica (33503) [IT]" in calls[0][1]["text"]
    assert "ACSAI (33502) [EN]" in calls[0][1]["text"]


def test_duplicate_course_is_not_added_twice(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text("{}\n", encoding="utf-8")
    duplicate = event("Informatica", "33503", "it", "https://example.test/33503#announcement-1")
    write_events(events_path, [duplicate, duplicate])
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    assert calls[0][1]["text"].count("Informatica (33503) [IT]") == 1



def test_only_new_course_history_is_updated_when_message_is_edited(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text(json.dumps({
        "same-content": {
            "title": "Shared announcement",
            "message_id": 42,
            "courses": [{
                "name": "Informatica",
                "id": "33503",
                "language": "it",
                "url": "https://example.test/33503#announcement-1"
            }]
        }
    }), encoding="utf-8")
    history_path.write_text(json.dumps({
        "courses": {
            "33503": {
                "name": "Informatica",
                "notifications": {
                    "announcements": {
                        "sent_at": "2026-09-30T08:00:00+00:00",
                        "telegram_message_id": 42
                    }
                }
            }
        }
    }), encoding="utf-8")
    write_events(events_path, [event("ACSAI", "33502", "en", "https://example.test/33502#announcement-2")])

    monkeypatch.setattr(mod, "call_telegram", lambda method, token, payload: {"message_id": 42})
    monkeypatch.setattr(mod, "notification_timestamp", lambda: "2026-10-03T11:11:24+00:00")
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    history = json.loads(history_path.read_text())
    old_course = history["courses"]["33503"]["notifications"]["announcements"]
    new_course = history["courses"]["33502"]["notifications"]["announcements"]
    assert old_course["sent_at"] == "2026-09-30T08:00:00+00:00"
    assert new_course == {
        "sent_at": "2026-10-03T11:11:24+00:00",
        "telegram_message_id": 42
    }


def test_history_is_not_updated_when_no_telegram_request_is_made(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    course = {
        "name": "Informatica",
        "id": "33503",
        "language": "it",
        "url": "https://example.test/33503#announcement-1"
    }
    registry_path.write_text(json.dumps({
        "same-content": {
            "title": "Shared announcement",
            "message_id": 42,
            "courses": [course]
        }
    }), encoding="utf-8")
    original_history = {"courses": {}}
    history_path.write_text(json.dumps(original_history), encoding="utf-8")
    write_events(events_path, [event("Informatica", "33503", "it", course["url"])])

    calls = []
    monkeypatch.setattr(mod, "call_telegram", lambda *args: calls.append(args))
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    assert calls == []
    assert json.loads(history_path.read_text()) == original_history



def test_history_is_not_written_when_telegram_send_fails(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text("{}\n", encoding="utf-8")
    original_history = {"courses": {}}
    history_path.write_text(json.dumps(original_history), encoding="utf-8")
    write_events(events_path, [event(
        "Informatica",
        "33503",
        "it",
        "https://example.test/33503#announcement-1"
    )])

    def fail_call(method, token, payload):
        raise mod.TelegramAPIError("send failed")

    monkeypatch.setattr(mod, "call_telegram", fail_call)

    try:
        mod.notify(events_path, registry_path, history_path, "token", "chat")
    except mod.TelegramAPIError:
        pass
    else:
        raise AssertionError("TelegramAPIError was not raised")

    assert json.loads(history_path.read_text()) == original_history


def test_fallback_send_updates_history_for_all_courses(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    history_path = tmp_path / "history.json"
    registry_path.write_text(json.dumps({
        "same-content": {
            "title": "Shared announcement",
            "message_id": 42,
            "courses": [{
                "name": "Informatica",
                "id": "33503",
                "language": "it",
                "url": "https://example.test/33503#announcement-1"
            }]
        }
    }), encoding="utf-8")
    history_path.write_text(json.dumps({"courses": {}}), encoding="utf-8")
    write_events(events_path, [event(
        "ACSAI",
        "33502",
        "en",
        "https://example.test/33502#announcement-2"
    )])
    calls = []

    def fake_call(method, token, payload):
        calls.append(method)
        if method == "editMessageText":
            raise mod.TelegramAPIError("message cannot be edited")
        return {"message_id": 99}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    monkeypatch.setattr(mod, "notification_timestamp", lambda: "2026-10-03T11:11:24+00:00")
    mod.notify(events_path, registry_path, history_path, "token", "chat")

    history = json.loads(history_path.read_text())
    assert calls == ["editMessageText", "sendMessage"]
    assert history["courses"]["33502"]["notifications"]["announcements"]["telegram_message_id"] == 99
    assert history["courses"]["33503"]["notifications"]["announcements"]["telegram_message_id"] == 99

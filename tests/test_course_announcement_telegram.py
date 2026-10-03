from pathlib import Path
import importlib.util
import json

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
    mod.notify(events_path, registry_path, "token", "chat")

    assert len(calls) == 1
    assert calls[0][0] == "sendMessage"
    assert "Informatica (33503) [IT]" in calls[0][1]["text"]
    assert "ACSAI (33502) [EN]" in calls[0][1]["text"]
    assert json.loads(registry_path.read_text())["same-content"]["message_id"] == 42


def test_later_course_edits_existing_message(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
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
    mod.notify(events_path, registry_path, "token", "chat")

    assert len(calls) == 1
    assert calls[0][0] == "editMessageText"
    assert calls[0][1]["message_id"] == 42
    assert "Informatica (33503) [IT]" in calls[0][1]["text"]
    assert "ACSAI (33502) [EN]" in calls[0][1]["text"]


def test_duplicate_course_is_not_added_twice(tmp_path, monkeypatch):
    events_path = tmp_path / "events.jsonl"
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}\n", encoding="utf-8")
    duplicate = event("Informatica", "33503", "it", "https://example.test/33503#announcement-1")
    write_events(events_path, [duplicate, duplicate])
    calls = []

    def fake_call(method, token, payload):
        calls.append((method, payload.copy()))
        return {"message_id": 42}

    monkeypatch.setattr(mod, "call_telegram", fake_call)
    mod.notify(events_path, registry_path, "token", "chat")

    assert calls[0][1]["text"].count("Informatica (33503) [IT]") == 1

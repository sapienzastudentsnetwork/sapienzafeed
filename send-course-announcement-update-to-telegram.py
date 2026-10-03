import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import requests


class TelegramAPIError(requests.RequestException):
    pass


def load_registry(path):
    registry_path = Path(path)
    if not registry_path.exists():
        return {}
    return json.loads(registry_path.read_text(encoding="utf-8"))



def load_notification_history(path):
    history_path = Path(path)
    if not history_path.exists():
        return {"courses": {}}
    return json.loads(history_path.read_text(encoding="utf-8"))


def notification_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def update_notification_history(history, courses, message_id, sent_at):
    course_history = history.setdefault("courses", {})
    for course in courses:
        course_entry = course_history.setdefault(course["id"], {
            "name": course["name"],
            "notifications": {}
        })
        course_entry["name"] = course["name"]
        course_entry["notifications"]["announcements"] = {
            "sent_at": sent_at,
            "telegram_message_id": message_id
        }


def save_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

def load_events(path):
    events = []
    with Path(path).open(encoding="utf-8") as event_file:
        for line in event_file:
            if line.strip():
                events.append(json.loads(line))
    return events


def merge_courses(existing_courses, new_courses):
    courses = {course["url"]: course for course in existing_courses}
    courses.update({course["url"]: course for course in new_courses})
    return sorted(courses.values(), key=lambda course: (course["name"], course["id"], course["language"], course["url"]))


def format_message(title, courses):
    course_links = "\n".join(
        f"• <a href='{escape(course['url'], quote=True)}'>{escape(course['name'])} ({escape(course['id'])}) [{escape(course['language'].upper())}]</a>"
        for course in courses
    )
    return (
        "🆕 New or modified announcement in the course catalogue page\n\n"
        f"<u><strong>{escape(title)}</strong></u>\n\n"
        f"{course_links}"
    )

def call_telegram(method, token, payload):
    response = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=payload)
    result = response.json()
    if not result.get("ok"):
        raise TelegramAPIError(result.get("description", "Telegram API request failed"))
    return result["result"]


def notify(events_path, registry_path, history_path, telegram_token, chat_id):
    registry = load_registry(registry_path)
    history = load_notification_history(history_path)
    grouped_events = defaultdict(list)
    for event in load_events(events_path):
        grouped_events[event["fingerprint"]].append(event)

    for fingerprint, events in grouped_events.items():
        registry_entry = registry.get(fingerprint, {})
        courses = merge_courses(registry_entry.get("courses", []), [
            {
                "name": event["course_name"],
                "id": event["course_id"],
                "language": event["language"],
                "url": event["url"]
            }
            for event in events
        ])
        title = registry_entry.get("title", events[0]["title"])
        message = format_message(title, courses)
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true"
        }

        message_id = registry_entry.get("message_id")
        new_courses = merge_courses([], [
            {
                "name": event["course_name"],
                "id": event["course_id"],
                "language": event["language"],
                "url": event["url"]
            }
            for event in events
        ])
        if message_id is not None and courses == registry_entry.get("courses", []):
            continue
        tracked_courses = new_courses
        if message_id is not None:
            payload["message_id"] = message_id
            try:
                call_telegram("editMessageText", telegram_token, payload)
            except TelegramAPIError:
                payload.pop("message_id")
                message_id = call_telegram("sendMessage", telegram_token, payload)["message_id"]
                tracked_courses = courses
        else:
            message_id = call_telegram("sendMessage", telegram_token, payload)["message_id"]

        update_notification_history(
            history,
            tracked_courses,
            message_id,
            notification_timestamp()
        )
        registry[fingerprint] = {
            "title": title,
            "message_id": message_id,
            "courses": courses
        }

    save_json(registry_path, registry)
    save_json(history_path, history)


def main():
    notify(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])


if __name__ == "__main__":
    main()

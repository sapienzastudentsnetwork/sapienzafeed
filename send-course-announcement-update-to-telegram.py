import json
import sys
from collections import defaultdict
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


def notify(events_path, registry_path, telegram_token, chat_id):
    registry = load_registry(registry_path)
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
        if message_id is not None and courses == registry_entry.get("courses", []):
            continue
        if message_id is not None:
            payload["message_id"] = message_id
            try:
                call_telegram("editMessageText", telegram_token, payload)
            except TelegramAPIError:
                payload.pop("message_id")
                message_id = call_telegram("sendMessage", telegram_token, payload)["message_id"]
        else:
            message_id = call_telegram("sendMessage", telegram_token, payload)["message_id"]

        registry[fingerprint] = {
            "title": title,
            "message_id": message_id,
            "courses": courses
        }

    Path(registry_path).write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )


def main():
    notify(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()

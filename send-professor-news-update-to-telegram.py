import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests


def load_notification_history(path):
    history_path = Path(path)
    if not history_path.exists():
        return {"lecturers": {}}
    return json.loads(history_path.read_text(encoding="utf-8"))


def save_notification_history(path, history):
    Path(path).write_text(
        json.dumps(history, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )


def notification_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def format_message(professor_name, file_url, commit_url):
    return (
        f"📰 <b>News update</b> for professor <b>{professor_name}</b> has been posted!\n\n"
        f"📄 View the <b>updated news</b>: {file_url}\n\n"
        f"🔍 View <b>changes</b>: {commit_url}"
    )


def call_telegram(method, telegram_token, payload):
    response = requests.post(
        f"https://api.telegram.org/bot{telegram_token}/{method}",
        data=payload
    )
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.text}")
        response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise requests.RequestException(
            result.get("description", "Telegram API request failed")
        )
    return result["result"]


def send_notification(
    professor_name,
    professor_id,
    file_url,
    commit_url,
    history_path,
    telegram_token,
    chat_id
):
    result = call_telegram("sendMessage", telegram_token, {
        "chat_id": chat_id,
        "text": format_message(professor_name, file_url, commit_url),
        "parse_mode": "HTML"
    })
    message_id = result["message_id"]
    history = load_notification_history(history_path)
    lecturer = history.setdefault("lecturers", {}).setdefault(professor_id, {
        "name": professor_name,
        "notifications": {}
    })
    lecturer["name"] = professor_name
    lecturer["notifications"]["news"] = {
        "sent_at": notification_timestamp(),
        "telegram_message_id": message_id
    }
    save_notification_history(history_path, history)
    return message_id


def edit_notification(
    professor_name,
    file_url,
    commit_url,
    message_id,
    telegram_token,
    chat_id
):
    call_telegram("editMessageText", telegram_token, {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": format_message(professor_name, file_url, commit_url),
        "parse_mode": "HTML"
    })


def main():
    mode = sys.argv[1]
    professor_name = sys.argv[2]
    file_url = sys.argv[3]
    commit_url = sys.argv[4]

    if mode == "send":
        message_id = send_notification(
            professor_name,
            sys.argv[5],
            file_url,
            commit_url,
            sys.argv[6],
            sys.argv[7],
            sys.argv[8]
        )
        Path(sys.argv[9]).write_text(str(message_id), encoding="utf-8")
    elif mode == "edit":
        edit_notification(
            professor_name,
            file_url,
            commit_url,
            int(sys.argv[5]),
            sys.argv[6],
            sys.argv[7]
        )
    else:
        raise ValueError(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    main()

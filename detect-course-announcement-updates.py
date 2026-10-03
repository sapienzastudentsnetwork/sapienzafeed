import hashlib
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def extract_announcements(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    announcements = {}
    accordion = soup.find("div", id="announcement-accordion")
    if not accordion:
        return announcements

    for details in accordion.find_all("details", id=True, recursive=False):
        announcement_id = details.get("id", "")
        if not announcement_id.startswith("announcement-"):
            continue
        summary = details.find("summary", recursive=False)
        title = summary.get_text(" ", strip=True) if summary else announcement_id
        canonical_details = BeautifulSoup(str(details), "html.parser").find("details")
        canonical_details.attrs.pop("id", None)
        normalized_content = " ".join(str(canonical_details).split())
        fingerprint = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        normalized_html = " ".join(str(details).split())
        announcements[announcement_id] = (title, normalized_html, fingerprint)

    return announcements


def find_updates(old_path, new_path):
    old_announcements = extract_announcements(old_path)
    new_announcements = extract_announcements(new_path)
    updates = []

    for announcement_id, (title, content, fingerprint) in new_announcements.items():
        old_announcement = old_announcements.get(announcement_id)
        if old_announcement is None or old_announcement[1] != content:
            updates.append((announcement_id, title, fingerprint))

    return updates


def main():
    for announcement_id, title, fingerprint in find_updates(sys.argv[1], sys.argv[2]):
        event = {
            "announcement_id": announcement_id,
            "title": title,
            "fingerprint": fingerprint
        }
        if len(sys.argv) == 7:
            event.update({
                "course_name": sys.argv[3],
                "course_id": sys.argv[4],
                "language": sys.argv[5],
                "url": f"{sys.argv[6]}#{announcement_id}"
            })
        print(json.dumps(event, ensure_ascii=False))


if __name__ == "__main__":
    main()

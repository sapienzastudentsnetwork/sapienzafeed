#!/usr/bin/env python3
"""Notify when lecturer news data changes, not when HTML formatting/order changes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

NEWS_ID = "common-lecturer-news"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fingerprint(path: Path | None) -> tuple[Counter, Counter]:
    """Return order-independent visible text and href multisets for the news section.

    URLs are intentionally preserved exactly: adding, removing or changing a link is
    a real news change. Only whitespace and DOM ordering are ignored.
    """
    if path is None or not path.exists():
        return Counter(), Counter()

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    section = soup.find(id=NEWS_ID)
    if section is None:
        return Counter(), Counter()

    for tag in section(["script", "style"]):
        tag.decompose()

    # Leaf text nodes avoid treating a simple paragraph/list reorder as new data.
    texts = Counter(
        text for raw in section.find_all(string=True)
        if (text := normalize_text(str(raw)))
    )
    links = Counter(
        href for tag in section.find_all("a", href=True)
        if (href := normalize_text(tag.get("href", "")))
    )
    return texts, links


def fingerprint_digest(value: tuple[Counter, Counter]) -> str | None:
    texts, links = value
    if not texts and not links:
        return None
    serialized = json.dumps(
        [sorted(texts.items()), sorted(links.items())],
        ensure_ascii=False,
        separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, str]) -> None:
    path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )


def decide(old_path: Path | None, new_path: Path) -> tuple[bool, str]:
    old_texts, old_links = fingerprint(old_path)
    new_texts, new_links = fingerprint(new_path)
    if (old_texts, old_links) == (new_texts, new_links):
        return False, "formatting or ordering changed, but news text and URLs did not"
    if old_links != new_links:
        return True, "news URL added, removed or changed"
    return True, "visible news text changed"


def decide_with_state(
    old_path: Path | None,
    new_path: Path,
    state_path: Path,
    lecturer_id: str
) -> tuple[bool, str]:
    state = load_state(state_path)
    old_digest = fingerprint_digest(fingerprint(old_path))
    new_digest = fingerprint_digest(fingerprint(new_path))
    remembered_digest = state.get(lecturer_id)

    if remembered_digest is None and old_digest is not None:
        remembered_digest = old_digest
        state[lecturer_id] = old_digest

    if new_digest is None:
        save_state(state_path, state)
        return False, "temporary complete news disappearance suppressed"

    if new_digest == remembered_digest:
        save_state(state_path, state)
        return False, "news restored unchanged after a temporary disappearance"

    notify, reason = decide(old_path, new_path)
    state[lecturer_id] = new_digest
    save_state(state_path, state)
    return notify, reason


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--lecturer-id")
    args = parser.parse_args()

    if args.state is not None or args.lecturer_id is not None:
        if args.state is None or args.lecturer_id is None:
            parser.error("--state and --lecturer-id must be used together")
        notify, reason = decide_with_state(
            args.old,
            args.new,
            args.state,
            args.lecturer_id
        )
    else:
        notify, reason = decide(args.old, args.new)

    print("1" if notify else "0")
    print(reason, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

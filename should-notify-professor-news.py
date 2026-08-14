#!/usr/bin/env python3
"""Notify when lecturer news data changes, not when HTML formatting/order changes."""
from __future__ import annotations

import argparse
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


def decide(old_path: Path | None, new_path: Path) -> tuple[bool, str]:
    old_texts, old_links = fingerprint(old_path)
    new_texts, new_links = fingerprint(new_path)
    if (old_texts, old_links) == (new_texts, new_links):
        return False, "formatting or ordering changed, but news text and URLs did not"
    if old_links != new_links:
        return True, "news URL added, removed or changed"
    return True, "visible news text changed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path)
    parser.add_argument("--new", required=True, type=Path)
    args = parser.parse_args()
    notify, reason = decide(args.old, args.new)
    print("1" if notify else "0")
    print(reason, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

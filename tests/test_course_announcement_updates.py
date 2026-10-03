from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "announcement_updates",
    Path(__file__).parents[1] / "detect-course-announcement-updates.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def page(*announcements, unrelated=""):
    details = "".join(
        f'<details id="{announcement_id}"><summary class="level-h4">{title}</summary>'
        f'<div class="details-body">{body}</div></details>'
        for announcement_id, title, body in announcements
    )
    return f'<html><body>{unrelated}<div id="announcement-accordion">{details}</div></body></html>'


def updates(tmp_path, old, new):
    old_path = tmp_path / "old.html"
    new_path = tmp_path / "new.html"
    old_path.write_text(old, encoding="utf-8")
    new_path.write_text(new, encoding="utf-8")
    return mod.find_updates(old_path, new_path)


def test_new_announcement_is_reported(tmp_path):
    old = page(("announcement-1", "First", "Text"))
    new = page(
        ("announcement-2", "Second", "New text"),
        ("announcement-1", "First", "Text")
    )
    result = updates(tmp_path, old, new)
    assert result[0][:2] == ("announcement-2", "Second")
    assert len(result[0][2]) == 64


def test_modified_announcement_is_reported(tmp_path):
    old = page(("announcement-1", "First", "Old text"))
    new = page(("announcement-1", "First updated", "New text"))
    result = updates(tmp_path, old, new)
    assert result[0][:2] == ("announcement-1", "First updated")
    assert len(result[0][2]) == 64


def test_reordering_is_not_reported(tmp_path):
    old = page(
        ("announcement-1", "First", "Text"),
        ("announcement-2", "Second", "Text")
    )
    new = page(
        ("announcement-2", "Second", "Text"),
        ("announcement-1", "First", "Text")
    )
    assert updates(tmp_path, old, new) == []


def test_removed_announcement_is_not_reported(tmp_path):
    old = page(
        ("announcement-1", "First", "Text"),
        ("announcement-2", "Second", "Text")
    )
    new = page(("announcement-1", "First", "Text"))
    assert updates(tmp_path, old, new) == []


def test_unrelated_page_change_is_not_reported(tmp_path):
    old = page(("announcement-1", "First", "Text"), unrelated="<header>Old</header>")
    new = page(("announcement-1", "First", "Text"), unrelated="<header>New</header>")
    assert updates(tmp_path, old, new) == []


def test_identical_content_has_same_fingerprint_with_different_ids(tmp_path):
    first = page(("announcement-1", "Shared", "<p>Same body</p>"))
    second = page(("announcement-2", "Shared", "<p>Same body</p>"))
    first_path = tmp_path / "first.html"
    second_path = tmp_path / "second.html"
    first_path.write_text(first, encoding="utf-8")
    second_path.write_text(second, encoding="utf-8")
    first_item = mod.extract_announcements(first_path)["announcement-1"]
    second_item = mod.extract_announcements(second_path)["announcement-2"]
    assert first_item[2] == second_item[2]

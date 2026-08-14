from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("filter", Path(__file__).parents[1] / "should-notify-professor-news.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def html(body):
    return f'<div id="common-lecturer-news">{body}</div>'


def check(tmp_path, old, new, expected):
    op = tmp_path / "old.html"; np = tmp_path / "new.html"
    op.write_text(html(old), encoding="utf-8"); np.write_text(html(new), encoding="utf-8")
    assert mod.decide(op, np)[0] is expected


def test_formatting_only_is_suppressed(tmp_path):
    check(tmp_path, '<p>Exam timetable</p>', '<div>  Exam timetable </div>', False)


def test_reordered_news_items_are_suppressed(tmp_path):
    check(tmp_path, '<ul><li>Item A</li><li>Item B</li></ul>', '<ul><li>Item B</li><li>Item A</li></ul>', False)


def test_old_information_is_still_notified(tmp_path):
    check(tmp_path, '', '<p>Lessons started on 25 February 2025.</p>', True)


def test_new_link_is_notified(tmp_path):
    check(tmp_path, '<p>Moodle</p>', '<p><a href="https://example.test/course">Moodle</a></p>', True)


def test_changed_url_is_notified(tmp_path):
    check(tmp_path, '<a href="https://example.test/a">Course</a>', '<a href="https://example.test/b">Course</a>', True)

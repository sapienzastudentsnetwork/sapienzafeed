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


def stateful_check(tmp_path, lecturer_id, old, new):
    op = tmp_path / "old-stateful.html"
    np = tmp_path / "new-stateful.html"
    state = tmp_path / "state.json"
    op.write_text(html(old), encoding="utf-8")
    np.write_text(html(new), encoding="utf-8")
    return mod.decide_with_state(op, np, state, lecturer_id)[0], state


def test_complete_disappearance_is_suppressed_and_remembered(tmp_path):
    notify, state = stateful_check(
        tmp_path,
        "lecturer-1",
        '<p>Exam timetable</p><a href="https://example.test/course">Course</a>',
        ""
    )
    assert notify is False
    assert "lecturer-1" in state.read_text(encoding="utf-8")


def test_identical_restoration_after_disappearance_is_suppressed(tmp_path):
    original = '<p>Exam timetable</p><a href="https://example.test/course">Course</a>'
    notify, state = stateful_check(tmp_path, "lecturer-1", original, "")
    assert notify is False

    old = tmp_path / "empty.html"
    restored = tmp_path / "restored.html"
    old.write_text(html(""), encoding="utf-8")
    restored.write_text(html(original), encoding="utf-8")
    assert mod.decide_with_state(old, restored, state, "lecturer-1")[0] is False


def test_changed_restoration_after_disappearance_is_notified(tmp_path):
    original = '<p>Exam timetable</p><a href="https://example.test/course">Course</a>'
    notify, state = stateful_check(tmp_path, "lecturer-1", original, "")
    assert notify is False

    old = tmp_path / "empty.html"
    restored = tmp_path / "restored.html"
    old.write_text(html(""), encoding="utf-8")
    restored.write_text(
        html('<p>Updated exam timetable</p><a href="https://example.test/course">Course</a>'),
        encoding="utf-8"
    )
    assert mod.decide_with_state(old, restored, state, "lecturer-1")[0] is True


def test_partial_removal_is_still_notified(tmp_path):
    notify, _ = stateful_check(
        tmp_path,
        "lecturer-1",
        "<p>Item A</p><p>Item B</p>",
        "<p>Item A</p>"
    )
    assert notify is True


def test_state_is_independent_for_each_lecturer(tmp_path):
    state = tmp_path / "state.json"
    first_old = tmp_path / "first-old.html"
    second_old = tmp_path / "second-old.html"
    empty = tmp_path / "empty.html"
    first_old.write_text(html("<p>First lecturer news</p>"), encoding="utf-8")
    second_old.write_text(html("<p>Second lecturer news</p>"), encoding="utf-8")
    empty.write_text(html(""), encoding="utf-8")

    mod.decide_with_state(first_old, empty, state, "lecturer-1")
    mod.decide_with_state(second_old, empty, state, "lecturer-2")

    saved_state = mod.load_state(state)
    assert saved_state["lecturer-1"] != saved_state["lecturer-2"]

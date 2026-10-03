from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_professor_notification_keeps_content_commit_link():
    workflow = (ROOT / ".github/workflows/update-professor-news.yml").read_text()
    content_commit = workflow.index('git commit -m "Update professor news, index pages and metadata"')
    commit_hash = workflow.index("commit_hash=$(git rev-parse HEAD)", content_commit)
    content_push = workflow.index("git push", commit_hash)
    notification = workflow.index("send-professor-news-update-to-telegram.py", content_push)
    tracking_commit = workflow.index(
        'git commit -m "Update professor news Telegram notification history"',
        notification
    )
    assert content_commit < commit_hash < content_push < notification < tracking_commit
    assert "git commit --amend --no-edit" not in workflow
    assert "editMessageText" not in workflow
    assert "send-professor-news-update-to-telegram.py \\\n                edit" not in workflow


def test_announcement_tracking_is_committed_after_notification():
    workflow = (ROOT / ".github/workflows/update-course-pages.yml").read_text()
    content_commit = workflow.index('git commit -m "Update announcements sections"')
    notification = workflow.index("send-course-announcement-update-to-telegram.py", content_commit)
    tracking_commit = workflow.index(
        'git commit -m "Update course announcement Telegram notification state"',
        notification
    )
    assert content_commit < notification < tracking_commit

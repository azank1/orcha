"""Path validation for stage_artifact / save_artifact workspace."""

from pathlib import Path

from superagent.system_tools import artifacts as art


def test_resolved_is_under_session_workspace(tmp_path, monkeypatch):
    sid = "sess-ws-test"
    fake_root = tmp_path / "tmp" / sid
    fake_root.mkdir(parents=True)
    f = fake_root / "doc.txt"
    f.write_text("hello", encoding="utf-8")

    monkeypatch.setattr(art, "_session_tmp_root", lambda s: fake_root if s == sid else Path("/tmp") / s)  # noqa: S108

    assert art._resolved_is_under_session_workspace(f, sid) is True
    assert art._resolved_is_under_session_workspace(fake_root / "missing.txt", sid) is False


def test_resolved_rejects_other_session_tree(tmp_path, monkeypatch):
    sid = "sess-a"
    other = tmp_path / "tmp" / "sess-b"
    other.mkdir(parents=True)
    f = other / "leak.txt"
    f.write_text("x", encoding="utf-8")

    monkeypatch.setattr(art, "_session_tmp_root", lambda s: tmp_path / "tmp" / s)

    assert art._resolved_is_under_session_workspace(f, sid) is False

"""Repo exporter against a throwaway local remote: ownership rules, index append, no Lean, push races."""
import subprocess

import pytest

from app.db import session_scope
from app.models import Conjecture


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def remote(tmp_path, monkeypatch):
    from app.config import get_settings
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "clone", "-q", str(bare), str(seed)], check=True, capture_output=True)
    (seed / "Conjectures" / "UserProblem").mkdir(parents=True)
    (seed / "Conjectures" / "UserProblem" / "README.md").write_text("# mine\n")
    (seed / "Conjectures" / "UserProblem" / "Main.lean").write_text("theorem x : True := trivial\n")
    (seed / "README.md").write_text("# Math\n\n## Conjectures\n\n- [Mine](Conjectures/UserProblem/) — Open\n\n## Other\nkeep\n")
    git(seed, "add", "-A")
    git(seed, "-c", "user.name=u", "-c", "user.email=u@x", "commit", "-q", "-m", "seed")
    git(seed, "push", "-q", "origin", "HEAD:main")
    s = get_settings()
    monkeypatch.setattr(s, "repo_export_remote", str(bare))
    monkeypatch.setattr(s, "repo_export_branch", "main")
    monkeypatch.setattr(s, "repo_export_enabled", True)
    monkeypatch.setattr(s, "data_dir", tmp_path / "data")
    return bare, seed


def _conj(title, **kw):
    import uuid
    with session_scope() as db:
        c = Conjecture(slug=f"x-{uuid.uuid4().hex[:8]}", title=title, field="graph_theory", original_statement="S $x$",
                       normalized_statement="S", created_by="t", **kw)
        db.add(c)
        db.flush()
        return c.id


def test_export_respects_ownership_and_index(remote, tmp_path):
    from app.export.repo import sync
    bare, seed = remote
    a = _conj("A brand new problem")
    b = _conj("User's problem", extraction_details={"repo_folder": "UserProblem"})
    res = sync([a, b])
    assert res["pushed"]
    check = tmp_path / "check"
    subprocess.run(["git", "clone", "-q", str(bare), str(check)], check=True, capture_output=True)
    assert (check / "Conjectures/UserProblem/README.md").read_text() == "# mine\n"          # untouched
    assert (check / "Conjectures/UserProblem/Main.lean").exists()
    assert (check / "Conjectures/UserProblem/MathResearchLab.md").exists()                # side file only
    new = check / "Conjectures/BrandNew"
    assert (new / ".mathresearchlab").exists() and "Status:" in (new / "README.md").read_text()
    readme = (check / "README.md").read_text()
    assert "- [Mine](Conjectures/UserProblem/) — Open" in readme and "## Other\nkeep" in readme
    assert readme.count("(Conjectures/BrandNew/)") == 1
    assert not list(check.rglob("*.lean"))[1:]  # only the user's own Lean file
    assert sync([a, b])["pushed"] is False      # idempotent


def test_export_survives_push_race(remote, tmp_path, monkeypatch):
    from app.export import repo as R
    bare, seed = remote
    a = _conj("Race problem")
    real_git = R._git
    raced = {"done": False}

    def racing_git(cwd, *args, check=True):
        if args[:1] == ("commit",) or (len(args) > 4 and "commit" in args):
            if not raced["done"]:  # someone else pushes to main just before our push
                raced["done"] = True
                (seed / "other.txt").write_text("parallel session\n")
                git(seed, "add", "-A")
                git(seed, "-c", "user.name=u", "-c", "user.email=u@x", "commit", "-q", "-m", "parallel")
                git(seed, "push", "-q", "origin", "HEAD:main")
        return real_git(cwd, *args, check=check)

    monkeypatch.setattr(R, "_git", racing_git)
    assert R.sync([a])["pushed"]
    check = tmp_path / "check2"
    subprocess.run(["git", "clone", "-q", str(bare), str(check)], check=True, capture_output=True)
    assert (check / "other.txt").exists() and (check / "Conjectures/Race/README.md").exists()


def test_orphaned_app_folders_are_removed_but_user_files_kept(remote, tmp_path):
    from app.export.repo import sync
    bare, seed = remote
    a = _conj("Temporary duplicate")
    assert sync()["pushed"]
    with session_scope() as db:
        c = db.get(Conjecture, a)
        c.extraction_details = {**c.extraction_details, "duplicate_of": "x"}
    res = sync()
    check = tmp_path / "check3"
    subprocess.run(["git", "clone", "-q", str(bare), str(check)], check=True, capture_output=True)
    assert not (check / "Conjectures/TemporaryDuplicate").exists()
    assert "TemporaryDuplicate" not in (check / "README.md").read_text()
    assert (check / "Conjectures/UserProblem/README.md").read_text() == "# mine\n"
    assert "- [Mine](Conjectures/UserProblem/) — Open" in (check / "README.md").read_text()


def test_app_index_lines_refresh_but_user_lines_do_not(remote, tmp_path):
    from app.export.repo import sync
    bare, seed = remote
    a = _conj("Status flip")
    sync()
    with session_scope() as db:
        db.get(Conjecture, a).status = "DISPROVED"
    sync()
    check = tmp_path / "check4"
    subprocess.run(["git", "clone", "-q", str(bare), str(check)], check=True, capture_output=True)
    readme = (check / "README.md").read_text()
    assert "(Conjectures/StatusFlip/) — **False** (MathResearchLab)" in readme
    assert readme.count("(Conjectures/StatusFlip/)") == 1
    assert "- [Mine](Conjectures/UserProblem/) — Open" in readme

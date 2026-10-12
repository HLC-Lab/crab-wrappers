"""unverified.txt lists exactly the wrappers that have no sample case.

A wrapper is verified when at least one `<app>/samples/<case>/case.json` names it (the `wrapper`
field is relative to the app folder). One rule, checked both ways, so the list cannot go stale
when a sample is added.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _unverified():
    lines = (ROOT / "unverified.txt").read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def _app_folders():
    return sorted(p for p in ROOT.iterdir() if (p / "samples").is_dir())


def _sampled():
    """Repository-relative paths of the wrappers some case.json names."""
    found = set()
    for app in _app_folders():
        for case in sorted((app / "samples").glob("*/case.json")):
            wrapper = json.loads(case.read_text())["wrapper"]
            found.add((app / wrapper).relative_to(ROOT).as_posix())
    return found


def _wrapper_files():
    found = set()
    for app in _app_folders():
        for path in app.rglob("*.py"):
            rel = path.relative_to(app)
            if path.name.startswith("_") or path.name == "__init__.py":
                continue
            if rel.parts[0] in ("tests", "samples"):
                continue
            found.add(path.relative_to(ROOT).as_posix())
    return found


def test_a_wrapper_with_a_sample_is_not_listed():
    stale = sorted(set(_unverified()) & _sampled())
    assert stale == []


def test_a_wrapper_without_a_sample_is_listed():
    missing = sorted(_wrapper_files() - _sampled() - set(_unverified()))
    assert missing == []


def test_every_listed_wrapper_exists():
    gone = sorted(p for p in _unverified() if not (ROOT / p).is_file())
    assert gone == []


def test_every_sample_names_an_existing_wrapper():
    assert sorted(p for p in _sampled() if not (ROOT / p).is_file()) == []


def test_the_list_has_no_duplicates():
    entries = _unverified()
    assert len(entries) == len(set(entries))

"""The verification table of README.md matches the tree.

Each row is recomputed from the wrapper files, `case.json` files and `unverified.txt`. A wrapper is
verified on a real run when some case for it has a `source` other than `synthetic`, verified on
synthetic samples only when every case for it is synthetic, and unverified when it has no case.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import json
import re
from pathlib import Path

from _test_unverified_list import _app_folders, _wrapper_files

ROOT = Path(__file__).resolve().parents[1]
NAMED_ROWS = ("blink", "graph500", "quantum-espresso")


def _sources():
    """Repository-relative wrapper path -> the set of `source` values of its cases."""
    found = {}
    for app in _app_folders():
        for case in sorted((app / "samples").glob("*/case.json")):
            data = json.loads(case.read_text())
            path = (app / data["wrapper"]).relative_to(ROOT).as_posix()
            found.setdefault(path, set()).add(data["source"])
    return found


def _counts(paths):
    sources = _sources()
    total = len(paths)
    real = sum(1 for p in paths if sources.get(p, {"synthetic"}) - {"synthetic"})
    synthetic = sum(1 for p in paths if p in sources and sources[p] == {"synthetic"})
    return [total, real, synthetic, total - real - synthetic]


def _computed():
    wrappers = sorted(_wrapper_files())
    rows = {name: [p for p in wrappers if p.split("/", 1)[0] == name] for name in NAMED_ROWS}
    rows["others"] = [p for p in wrappers if p.split("/", 1)[0] not in NAMED_ROWS]
    return {name: _counts(paths) for name, paths in rows.items()}


def _readme_rows():
    rows = {}
    for line in (ROOT / "README.md").read_text().splitlines():
        match = re.match(r"\|\s*`([\w-]+)`[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*$", line)
        if match:
            rows[match.group(1)] = [int(n) for n in match.groups()[1:]]
    return rows


def test_the_readme_table_matches_the_tree():
    assert _readme_rows() == _computed()

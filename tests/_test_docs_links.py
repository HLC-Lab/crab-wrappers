"""Links to CRAB's documentation name a version: readthedocs answers 404 without `/en/<version>/`.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
RTD = re.compile(r"https://hlc-crab\.readthedocs\.io/(\S*)")


def test_readthedocs_links_name_a_version():
    bad = []
    for path in DOC_FILES:
        for rest in RTD.findall(path.read_text()):
            if rest and not re.match(r"en/(stable|latest)/", rest):
                bad.append(f"{path.relative_to(ROOT)}: {rest}")
    assert bad == []

"""Every blink wrapper declares the message size its program uses when `-msgsize` is absent.

Blink's `-msgsize` defaults to 1024 (`src/common.c`: `int msg_size = 1024;`). The programs below
never use the size (no payload, or every argument ignored), so their wrappers declare 0. Every
other wrapper inherits 1024 from `microbench`. A wrapper added later must pick one of the two.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from crab.core.data.msg_size import msg_size_of

BLINK = Path(__file__).resolve().parents[1] / "blink"

# The programs whose source never reads `msg_size`.
NO_PAYLOAD = {"barrier_b", "barrier_nb", "null_dummy", "checker"}


def _wrapper_files():
    return sorted(
        p
        for p in BLINK.rglob("*.py")
        if not p.name.startswith("_") and p.relative_to(BLINK).parts[0] != "samples"
    )


def _load_app(path):
    """Import `path` the way a wrapper is loaded and return its `app` class (no launcher)."""
    if str(BLINK) not in sys.path:
        sys.path.insert(0, str(BLINK))
    spec = importlib.util.spec_from_file_location(f"_blink_defaults_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_every_blink_wrapper_declares_its_default_message_size(path):
    expected = 0 if path.stem in NO_PAYLOAD else 1024
    assert _load_app(path).default_msg_size == expected


def test_the_zero_list_matches_the_programs_that_ignore_the_size():
    assert NO_PAYLOAD <= {p.stem for p in _wrapper_files()}


def test_a_blink_app_without_msgsize_records_1024_through_crab():
    alltoall = _load_app(BLINK / "alltoall" / "alltoall_comm_only.py")
    plain = alltoall(0, True, "-iter 5")
    assert msg_size_of(plain.args, plain.default_msg_size) == 1024
    explicit = alltoall(0, True, "-msgsize 8 -iter 5")
    assert msg_size_of(explicit.args, explicit.default_msg_size) == 8
    barrier = _load_app(BLINK / "barrier" / "barrier_b.py")(0, True, "-iter 5")
    assert msg_size_of(barrier.args, barrier.default_msg_size) == 0

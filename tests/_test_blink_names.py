"""A blink wrapper is named after the binary it launches, and every upstream binary has one.

Upstream is HLC-Lab/blink at faea270 (2026-06-30). The names below are every executable it
builds except the tool `dist_test`, which is not a benchmark. A wrapper `blink/<x>.py` must call
`get_path("<x>")` exactly once, so a short invented name cannot come back.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import re
from pathlib import Path

import pytest

BLINK = Path(__file__).resolve().parents[1] / "blink"

UPSTREAM_BINARIES = (
    "allgather_b",
    "allgather_comm_only",
    "allgather_nb",
    "allreduce_b",
    "allreduce_nb",
    "alltoall_b",
    "alltoall_comm_only",
    "alltoall_man",
    "alltoall_nb",
    "barrier_b",
    "barrier_nb",
    "broadcast_b",
    "broadcast_nb",
    "checker",
    "gather_b",
    "gather_nb",
    "incast_b",
    "incast_bsnbr",
    "incast_get",
    "incast_nb",
    "incast_put",
    "kpartners_nb",
    "null_dummy",
    "pairwise_b",
    "pairwise_bsnbr",
    "pairwise_nb",
    "pingpong_b",
    "pingpong_pairwise_b",
    "reduce_b",
    "reduce_nb",
    "reduce_scatter_b",
    "reduce_scatter_nb",
    "ring_bsnbr",
    "ring_nb",
    "scatter_b",
    "scatter_nb",
    "stencil_2d_nb",
    "tagmatch_nb",
)

# Binaries that exist only in the fork blink-clean.
FORK_ONLY = ("bursty_noise_a2a", "bursty_noise_incast")

# workerpool.py is a helper for the bursty-noise wrappers, not the wrapper of one binary.
NOT_A_SINGLE_BINARY = ("workerpool",)

# checker.py builds its path by hand from CRAB_ROOT instead of calling get_path, so it is
# checked on that literal. It is left as it is until it gets a sample.
HAND_BUILT_PATH = {"checker": "/src/microbench/bin/checker"}

GET_PATH = re.compile(r"""get_path\(\s*["']([^"']+)["']\s*\)""")


def _wrapper_files():
    return sorted(
        p
        for p in BLINK.glob("*.py")
        if not p.name.startswith("_") and p.stem not in NOT_A_SINGLE_BINARY
    )


@pytest.mark.parametrize("name", UPSTREAM_BINARIES)
def test_every_upstream_binary_has_a_wrapper(name):
    assert (BLINK / f"{name}.py").is_file()


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_wrapper_launches_the_binary_it_is_named_after(path):
    source = path.read_text()
    if path.stem in HAND_BUILT_PATH:
        assert HAND_BUILT_PATH[path.stem] in source
        assert not GET_PATH.findall(source)
        return

    assert GET_PATH.findall(source) == [path.stem]


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_wrapper_name_is_an_upstream_or_fork_binary(path):
    assert path.stem in UPSTREAM_BINARIES + FORK_ONLY

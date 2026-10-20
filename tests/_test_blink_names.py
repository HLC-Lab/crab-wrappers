"""A blink wrapper is named after the binary it launches, and every upstream binary has one.

Upstream is HLC-Lab/blink at faea270 (2026-06-30). The names below are every executable it
builds except the tool `dist_test`, which is not a benchmark, each with the folder of upstream's
`src/` that holds its source. A wrapper `blink/<group>/<x>.py` sits in that folder and must call
`get_path("<x>")` exactly once, so a short invented name cannot come back.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import re
from pathlib import Path

import pytest

BLINK = Path(__file__).resolve().parents[1] / "blink"

# Upstream binary -> the folder of `src/` that holds its source. The wrapper sits in the same
# folder of `blink/`. `tools/dist_test.c` has no wrapper: it is not a benchmark.
UPSTREAM_GROUPS = {
    "allgather_b": "allgather",
    "allgather_comm_only": "allgather",
    "allgather_nb": "allgather",
    "allreduce_b": "allreduce",
    "allreduce_nb": "allreduce",
    "alltoall_b": "alltoall",
    "alltoall_comm_only": "alltoall",
    "alltoall_man": "alltoall",
    "alltoall_nb": "alltoall",
    "barrier_b": "barrier",
    "barrier_nb": "barrier",
    "broadcast_b": "broadcast",
    "broadcast_nb": "broadcast",
    "checker": "tools",
    "gather_b": "gather",
    "gather_nb": "gather",
    "incast_b": "incast",
    "incast_bsnbr": "incast",
    "incast_get": "incast",
    "incast_nb": "incast",
    "incast_put": "incast",
    "kpartners_nb": "kpartners",
    "null_dummy": "tools",
    "pairwise_b": "pairwise",
    "pairwise_bsnbr": "pairwise",
    "pairwise_nb": "pairwise",
    "pingpong_b": "pingpong",
    "pingpong_pairwise_b": "pingpong",
    "reduce_b": "reduce",
    "reduce_nb": "reduce",
    "reduce_scatter_b": "reduce_scatter",
    "reduce_scatter_nb": "reduce_scatter",
    "ring_bsnbr": "ring",
    "ring_nb": "ring",
    "scatter_b": "scatter",
    "scatter_nb": "scatter",
    "stencil_2d_nb": "stencil",
    "tagmatch_nb": "tagmatch",
}
UPSTREAM_BINARIES = tuple(UPSTREAM_GROUPS)

GET_PATH = re.compile(r"""get_path\(\s*["']([^"']+)["']\s*\)""")


def _wrapper_files():
    return sorted(
        p
        for p in BLINK.rglob("*.py")
        if not p.name.startswith("_") and p.relative_to(BLINK).parts[0] != "samples"
    )


@pytest.mark.parametrize("name", UPSTREAM_BINARIES)
def test_every_upstream_binary_has_a_wrapper_in_its_upstream_folder(name):
    assert (BLINK / UPSTREAM_GROUPS[name] / f"{name}.py").is_file()


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_wrapper_launches_the_binary_it_is_named_after(path):
    assert GET_PATH.findall(path.read_text()) == [path.stem]


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_wrapper_name_is_an_upstream_binary(path):
    assert path.stem in UPSTREAM_GROUPS


@pytest.mark.parametrize("path", _wrapper_files(), ids=lambda p: p.stem)
def test_wrapper_sits_in_the_folder_upstream_keeps_its_source_in(path):
    assert path.relative_to(BLINK).parent.as_posix() == UPSTREAM_GROUPS[path.stem]


def test_no_wrapper_sits_directly_in_blink():
    loose = sorted(p.name for p in BLINK.glob("*.py") if not p.name.startswith("_"))
    assert loose == []


def test_no_bursty_noise_wrapper_remains():
    assert sorted(p.name for p in BLINK.rglob("bursty_noise_*.py")) == []

"""The gpubench wrappers resolve their binary path with or without CRAB_SYSTEM.

Outside a job (`crab wrappers list`, `crab validate`, `crab parse`) CRAB_SYSTEM is not set: the
path is still built, without a select_* prefix because the system is unknown. Inside a job the
path is the one the preset has always produced.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app(0, False, "")


@pytest.fixture
def crab_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CRAB_ROOT", str(tmp_path))
    monkeypatch.delenv("CRAB_SYSTEM", raising=False)
    return str(tmp_path)


def test_binary_path_without_crab_system_does_not_raise(crab_root):
    wrapper = _load("others/gpubench-a2a-nccl.py")
    assert wrapper.get_binary_path() == f"{crab_root}/src/microbench-gpu/bin/a2a_Nccl"


def test_cuda_aware_without_crab_system_has_no_select_prefix(crab_root):
    wrapper = _load("others/gpubench-a2a-nccl.py")
    assert wrapper.get_path("a2a_CudaAware") == f"{crab_root}/src/microbench-gpu/bin/a2a_CudaAware"


def test_cuda_aware_on_leonardo_selects_the_nic(crab_root, monkeypatch):
    monkeypatch.setenv("CRAB_SYSTEM", "leonardo")
    wrapper = _load("others/gpubench-a2a-nccl.py")
    base = f"{crab_root}/src/microbench-gpu"
    assert wrapper.get_path("a2a_CudaAware") == f"{base}/select_nic_leonardo {base}/bin/a2a_CudaAware"


@pytest.mark.parametrize("system", ["lumi", "alps"])
def test_cuda_aware_on_lumi_and_alps_selects_the_gpu(system, crab_root, monkeypatch):
    monkeypatch.setenv("CRAB_SYSTEM", system)
    wrapper = _load("others/gpubench-a2a-nccl.py")
    base = f"{crab_root}/src/microbench-gpu"
    assert wrapper.get_path("a2a_CudaAware") == f"{base}/select_gpu_{system} {base}/bin/a2a_CudaAware"


def test_non_cuda_aware_ignores_the_system(crab_root, monkeypatch):
    monkeypatch.setenv("CRAB_SYSTEM", "leonardo")
    wrapper = _load("others/gpubench-a2a-nccl.py")
    assert wrapper.get_path("a2a_Nccl") == f"{crab_root}/src/microbench-gpu/bin/a2a_Nccl"

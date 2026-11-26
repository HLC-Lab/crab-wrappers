"""The cp.x wrapper: its binary, its input rewrite, and what it keeps besides the metric.

cp.x sits next to pw.x, so the wrapper derives it from the pw receipt like ph.x. read_data writes
cp.x's stdout to `cp.out` and the wrapper lists it as an extra artifact, so it survives
`retain_files: false`. The strict sample test covers the parsed wall time itself.

The file name starts with `_` like the other tests here; pytest.ini collects `_test_*.py`.
Run with: python -m pytest tests
"""

import importlib.util
from pathlib import Path

import pytest
from crab.setup import memory
from crab.wrappers.base import MissingBinaryError

QE_DIR = Path(__file__).resolve().parents[1] / "quantum-espresso"
SAMPLES = QE_DIR / "samples"


def _load():
    spec = importlib.util.spec_from_file_location("qe_cp_v7", QE_DIR / "cp" / "v7.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app(0, False, "")


def _executable(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n")
    path.chmod(0o755)
    return str(path)


@pytest.fixture
def receipts(tmp_path, monkeypatch):
    folder = tmp_path / "receipts"
    folder.mkdir()
    monkeypatch.setattr(memory, "ENV_DIR", str(folder))
    monkeypatch.setattr(memory, "LEGACY_ENV_DIR", str(folder))

    def write(install_type: str, binary_path: str) -> None:
        memory.save_receipt("qe-v7", {"id": "qe-v7", "type": install_type, "binary_path": binary_path})

    return write


@pytest.fixture
def input_file(tmp_path):
    path = tmp_path / "cp.in"
    path.write_text("&CONTROL\n  outdir = './scratch/',\n  pseudo_dir = './pseudo/'\n/\n")
    return str(path)


def _run_app(app, input_file: str, run_dir: Path) -> str:
    run_dir.mkdir(exist_ok=True)
    app.input_file = input_file
    app.run_dir = str(run_dir)
    return app.run_app()


@pytest.mark.parametrize("case", ["cp-v7-leonardo-gpu-si8", "cp-v7-leonardo-gpu-si128"])
def test_cp_out_is_written_and_listed_as_artifact(case, tmp_path):
    app = _load()
    app.run_dir = str(tmp_path)
    app.stdout = (SAMPLES / case / "stdout.txt").read_text()
    assert app.read_data()
    assert app.get_extra_artifacts() == ["cp.out"]
    for name in app.get_extra_artifacts():
        assert (tmp_path / name).read_text() == app.stdout


def test_source_install_runs_cp_from_the_build_dir(tmp_path, receipts):
    target = tmp_path / "qe-v7"
    _executable(target / "build" / "bin" / "pw.x")
    cp = _executable(target / "build" / "bin" / "cp.x")
    receipts("source", str(target / "bin"))

    assert _load().resolve_binary() == cp


def test_module_install_with_a_command_name_runs_cp_x(tmp_path, receipts, input_file):
    receipts("module", "pw.x")

    app = _load()
    assert app.resolve_binary() == "cp.x"
    assert _run_app(app, input_file, tmp_path / "run").split(" < ")[0] == "cp.x"


def test_missing_cp_next_to_pw_is_a_loud_error(tmp_path, receipts, input_file):
    bindir = tmp_path / "qe" / "bin"
    _executable(bindir / "pw.x")
    receipts("binary", str(bindir))

    with pytest.raises(MissingBinaryError) as excinfo:
        _load().resolve_binary()
    assert "cp.x" in str(excinfo.value)
    assert str(bindir) in str(excinfo.value)


def test_outdir_and_pseudo_dir_point_into_the_run_folder(tmp_path, receipts, input_file):
    bindir = tmp_path / "qe" / "bin"
    _executable(bindir / "pw.x")
    cp = _executable(bindir / "cp.x")
    receipts("binary", str(bindir))
    run_dir = tmp_path / "run"

    command = _run_app(_load(), input_file, run_dir)

    modified = run_dir / "modified_input.in"
    assert command == f"{cp} < {modified}"
    text = modified.read_text()
    assert f"outdir = '{run_dir}/scratch/'" in text
    assert f"pseudo_dir = '{run_dir}/scratch/pseudo/'" in text

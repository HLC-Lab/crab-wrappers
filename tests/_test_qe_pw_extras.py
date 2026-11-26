"""What the pw.x wrappers keep besides the metrics.

read_data writes pw.x's stdout to `pw.out` in the run folder and the wrapper lists that file as an
extra artifact, so it survives `retain_files: false`. The strict sample test does not cover this.

The file name starts with `_` like the other tests here; pytest.ini collects `_test_*.py`.
Run with: python -m pytest tests
"""

import importlib.util
from pathlib import Path

import pytest

QE_DIR = Path(__file__).resolve().parents[1] / "quantum-espresso"
SAMPLE = QE_DIR / "samples" / "pw-v7-leonardo-gpu" / "stdout.txt"


def _load(version: str):
    spec = importlib.util.spec_from_file_location(f"qe_pw_{version}", QE_DIR / "pw" / f"{version}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app(0, False, "")


@pytest.mark.parametrize("version", ["v6", "v7"])
def test_pw_out_is_written_and_listed_as_artifact(version, tmp_path):
    app = _load(version)
    app.run_dir = str(tmp_path)
    app.stdout = SAMPLE.read_text()
    assert app.read_data() == [{"wall_time": 16.7}]
    assert app.get_extra_artifacts() == ["pw.out"]
    for pattern in app.get_extra_artifacts():
        assert (tmp_path / pattern).read_text() == app.stdout

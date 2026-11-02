"""Every `presets/<cluster>.json` follows the shared-preset rules and loads through CRAB.

Part one reads the files alone (no CRAB needed): the rules of CONTRIBUTING.md, "Presets".
Part two asks CRAB itself to resolve each preset with `crab presets show <name> --json`, so a file
CRAB rejects fails here. CRAB must be installed (CI installs it); there is no silent skip.

The file name starts with `_` so `crab wrappers list` does not take it for a wrapper.
Run with: python -m pytest tests
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "presets"

MARK = re.compile(r"<YOUR_[A-Z0-9_]+>")
KEYED_ITEM = re.compile(r"--[^=\s]+=")
MAX_NOTES = 3
SEE = "see CONTRIBUTING.md, section Presets"

# Run the crab entry point (`crab.cli.main:cli_router`) with the interpreter that runs the tests,
# so it works without a `crab` script on PATH.
CRAB = "import sys; from crab.cli.main import cli_router; sys.argv[0] = 'crab'; cli_router()"


def _files():
    return sorted(PRESETS.glob("*.json"))


def _load(path):
    return json.loads(path.read_text())


def _entries():
    """(file name, preset name, body) for every preset of every file."""
    return [(path.name, name, body) for path in _files() for name, body in _load(path).items()]


def _flag_lists(body):
    """(where, items) for the sbatch list and every launcher's flag list of a preset body."""
    found = [("sbatch", body.get("sbatch", []))]
    for kind, launcher in body.get("launchers", {}).items():
        found.append((f"launchers.{kind}.flags", launcher.get("flags", [])))
    return found


def test_presets_folder_has_files():
    assert _files(), f"no presets/*.json in {ROOT}"


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.name)
def test_file_is_an_object_of_objects(path):
    data = _load(path)
    assert isinstance(data, dict) and data, f"{path.name}: must be a JSON object of presets"
    for name, body in data.items():
        assert isinstance(body, dict), f"{path.name}: preset {name!r} must be a JSON object"


def test_no_common_key():
    for file, name, _ in _entries():
        assert name != "_common", (
            f"{file}: a '_common' key was removed from CRAB; put the env in each preset"
        )


def test_each_preset_name_is_in_one_file_only():
    seen = {}
    for file, name, _ in _entries():
        assert name not in seen, f"preset {name!r} is in both {seen[name]} and {file}"
        seen[name] = file


def test_sbatch_items_use_the_long_form():
    for file, name, body in _entries():
        for item in body.get("sbatch", []):
            assert isinstance(item, str) and item.startswith("--"), (
                f"{file}: preset {name!r}: sbatch item {item!r} is not a long option. "
                f"Use the long option (--account=..., not -A ...): an override matches "
                f"items by their --name= only; {SEE}"
            )


def test_no_mark_in_header_lines():
    for file, name, body in _entries():
        for line in body.get("header", []):
            assert not MARK.search(line), (
                f"{file}: preset {name!r}: header line {line!r} holds a <YOUR_...> mark. "
                f"A header line cannot be patched by key; put the value in an env value or a "
                f"--name=<YOUR_...> flag; {SEE}"
            )


def test_marks_in_flags_sit_inside_name_value_items():
    for file, name, body in _entries():
        for where, items in _flag_lists(body):
            for item in items:
                if MARK.search(item):
                    assert KEYED_ITEM.match(item), (
                        f"{file}: preset {name!r}: {where} item {item!r} holds a <YOUR_...> "
                        f"mark but is not a --name=value item; write --name=<YOUR_...>; {SEE}"
                    )


def test_notes_are_a_short_list_of_one_line_strings():
    for file, name, body in _entries():
        if "notes" not in body:
            continue
        notes = body["notes"]
        assert isinstance(notes, list), f"{file}: preset {name!r}: notes must be a list; {SEE}"
        assert len(notes) <= MAX_NOTES, (
            f"{file}: preset {name!r}: {len(notes)} notes, at most {MAX_NOTES} allowed; {SEE}"
        )
        for note in notes:
            assert isinstance(note, str) and "\n" not in note, (
                f"{file}: preset {name!r}: each note must be a string on one line; {SEE}"
            )


def _crab_show(name, tmp_path):
    env = dict(os.environ)
    env["CRAB_PATH_WRAPPERS"] = str(ROOT)
    env["CRAB_PATH_PRESETS"] = str(tmp_path / "overrides")
    env["CRAB_HOME"] = str(tmp_path / "home")
    (tmp_path / "overrides").mkdir(exist_ok=True)
    (tmp_path / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "-c", CRAB, "presets", "show", name, "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
        timeout=120,
    )


def test_leonardo_gpu_asks_for_four_gpus_and_keeps_the_leonardo_gotchas(tmp_path):
    result = _crab_show("leonardo_gpu", tmp_path)
    assert result.returncode == 0, (
        f"crab presets show leonardo_gpu --json exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    data = json.loads(result.stdout)
    assert "error" not in data, data.get("error")
    preset = data["preset"]

    assert "leonardo" in data["extends"]

    gres = [item for item in preset["sbatch"] if item.startswith("--gres=")]
    assert gres == ["--gres=gpu:4,tmpfs:0"]
    assert "--partition=boost_usr_prod" in preset["sbatch"]
    assert "--account=<YOUR_ACCOUNT>" in preset["sbatch"]

    assert preset["launcher"] == "srun"
    assert "UCX_IB_SL" in preset["env"]
    assert "CRAB_IB_DEVICES" in preset["env"]

    topology = preset["topology"]
    assert len(topology["gpus"]) == 4
    assert len(topology["nics"]) == 4
    assert [nic["near_gpu"] for nic in topology["nics"]] == [0, 1, 2, 3]
    assert topology["nic_env"] == "UCX_NET_DEVICES"
    assert topology["gpu_vendor"] == "nvidia"


def test_leonardo_gpu_is_a_variant_that_leaves_leonardo_alone():
    base = _load(PRESETS / "leonardo.json")
    assert list(base) == ["leonardo"]
    assert "topology" not in base["leonardo"]
    assert "--gres=tmpfs:0" in base["leonardo"]["sbatch"]
    assert not any("gpu" in item for item in base["leonardo"]["sbatch"])

    variant = _load(PRESETS / "leonardo_gpu.json")["leonardo_gpu"]
    assert variant["extends"] == "leonardo"
    for key in ("scheduler", "launcher", "env", "header"):
        assert key not in variant, f"a variant sets only what differs, but repeats {key!r}"


def test_crab_is_installed():
    probe = subprocess.run(
        [sys.executable, "-c", "import crab.cli.main"], capture_output=True, text=True
    )
    assert probe.returncode == 0, (
        "CRAB is not importable, so presets cannot be loaded. Install it first: "
        "pip install 'git+https://github.com/HLC-Lab/CRAB.git@develop'\n" + probe.stderr
    )


@pytest.mark.parametrize(
    "name", sorted(name for _, name, _ in _entries()) or ["<no presets>"]
)
def test_preset_loads_through_crab(name, tmp_path):
    result = _crab_show(name, tmp_path)
    assert result.returncode == 0, (
        f"crab presets show {name} --json exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    data = json.loads(result.stdout)
    assert "error" not in data, f"{name}: {data['error']}"
    assert data["name"] == name
    source = Path(data["sources"]["description"]).resolve()
    assert source.parent == PRESETS.resolve(), (
        f"{name}: description comes from {source}, not from this repository's presets/ folder"
    )

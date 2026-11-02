# Contributing

A wrapper is shared by everyone who runs the same application, so the bar is: it parses real
output correctly, and a test proves it.

## 1. Start from the scaffold

In a CRAB checkout with this repository on its wrapper search path:

```bash
crab wrappers new myapp            # creates myapp/myapp.py, README.md and samples/example/
crab wrappers test myapp --strict  # passes as generated
```

Use `--local` to create it in your CRAB checkout's `local/wrappers/` while it is private.

## 2. Write the wrapper

The wrapper is a class named `app` that subclasses `crab.wrappers.base.base`. It implements
wrapper contract version 1 (`wrapper_api = 1` in CRAB); the full description is CRAB's
[Writing a wrapper](https://hlc-crab.readthedocs.io/extending/wrappers/) page.

- `executable`: the program name CRAB looks up on `PATH` when neither the config's `binary` key
  nor a receipt gives a path.
- `benchmark_id`: the receipt name, for `crab receipts set <id> --binary <path>`.
- `metadata`: one entry per measured value: `{"name": ..., "unit": ..., "conv": True|False}`.
  `conv: True` means CRAB repeats runs until that value converges. Optional: `"type"` (`"float"`
  by default, or `"int"`, `"str"` or `"bool"`); `"role": "check"` for a boolean correctness
  verdict, where false fails the run.
- `keys`: names of sweep dimensions every row carries, for example `["size"]` when one run prints
  results for several message sizes. Leave it empty when a run gives single values.
- `default_msg_size` (optional): the message size the program uses when `-msgsize` is absent from
  its arguments. CRAB records it in the `msg_size` column of the results CSV. Leave it at 0 for a
  program without a message size.
- `read_data()`: return a list of rows, one dict per sample, holding every key and every metric
  and nothing else. The old shape, one list of values per metric, is an error in CRAB 1.0. The
  application's output is in `self.stdout` and `self.stderr`, and files it
  wrote are in `self.run_dir`.
- `get_extra_artifacts()` (optional): paths or glob patterns, relative to `self.run_dir`, of
  files to keep with the results.

Rules:

- If the output is not what you expect, raise an exception. CRAB then marks the run as failed and
  logs why. Never return zeros or placeholders: they look like real measurements.
- Report what the application measures, in its own units. Ratios between runs (slowdowns,
  interference) belong to the analysis, not to the wrapper.

## 3. Add a real sample

Replace `samples/example/` with output from a real run. Put it in `samples/<case>/`:
`stdout.txt` (plus `stderr.txt` and any files the application wrote), `case.json` naming the
wrapper and the `args` it was run with, and `expected.json` with the rows the wrapper must
return. Say in the app's README where each sample comes from: system, date, application version.

A case can also check that bad output is refused. Put `expected_error.txt` in the case folder
instead of `expected.json`, holding a piece of the error message the wrapper must raise (for
example `no rows`). The case passes only if parsing fails with a parse error whose message
contains that text. A case with both files, or neither, is reported as an error.

Check a single case by hand with:

```bash
crab parse myapp/myapp.py myapp/samples/<case>/stdout.txt --check myapp/samples/<case>/expected.json
```

## 4. Open a pull request

Run both checks with the CRAB package installed (the tests import it) and `CRAB_PATH_WRAPPERS`
pointing at your clone of this repository, from a CRAB checkout or from any install:

```bash
export CRAB_PATH_WRAPPERS=/path/to/crab-wrappers
crab wrappers test --strict
python -m pytest -q          # from the root of this repository
```

CI runs these two, after checking that every wrapper loads (`crab wrappers list`). Then open the
pull request.

- A wrapper with a sample case must not be listed in `unverified.txt`: remove its line. The test
  `tests/_test_unverified_list.py` fails when the list and the samples disagree, in either
  direction.
- A new Blink wrapper is named after the program it launches, and calls `get_path("<name>")` with
  that name; `tests/_test_blink_names.py` checks it.

Each CRAB release has a matching tag `vX.Y.Z` of this repository, which `crab update` checks out
for users on a release. Your pull request goes to `main`.

## Presets

A preset describes one cluster, so it is shared by everyone who uses that cluster. It lives in
`presets/<cluster>.json` as a JSON object of presets, `{"<name>": {...}}`, in the format of CRAB's
[presets reference](https://hlc-crab.readthedocs.io/reference/presets/). One file may hold several
variants of a cluster. A preset name appears in one file only.

Rules, which `tests/_test_presets.py` checks:

- Use long `sbatch` options only: `--account=...`, not `-A ...`. A user's override replaces a
  shared item by its `--name=` prefix, so a short form could not be patched.
- A value that only the user knows is a mark, `<YOUR_NAME>` (capital letters, digits and
  underscores), for example `--account=<YOUR_ACCOUNT>`. A mark goes only in an env value, in a
  `--name=<YOUR_NAME>` flag item (sbatch or launcher) or in the launcher `command`. Never put one
  in a `header` line, which an override cannot patch by key.
- A choice the cluster offers, such as a partition or GPU versus CPU nodes, is a variant preset
  with `"extends": "<name>"` that sets only what differs.
- A gotcha of the cluster (a `--gres=tmpfs:0` option, an InfiniBand service level) goes into the
  preset itself, so nobody has to remember it.
- A user's own environment (their UCX or OpenMPI build, a venv, modules, a QoS) is not a preset
  field. CRAB's documentation covers it once, for every preset.
- `notes`, when present, is a list of at most 3 entries, each a single line. Use it only for what
  the other rules cannot express.
- No `_common` key: put the environment in each preset.

Check a preset by hand with:

```bash
export CRAB_PATH_WRAPPERS=$PWD
crab presets show <name>     # the resolved preset, its sources, and what is still unset
python -m pytest -q          # includes tests/_test_presets.py
```

CI runs the tests with CRAB installed from its `develop` branch, so every preset must load there.

# Writing a CRAB wrapper, sample first

This file guides a language model, and the human it works with, through writing a CRAB wrapper:
a small Python class that tells CRAB how to read one application's output. It is plain text on
purpose: follow it step by step. Each step ends with a check, and the next step starts only when the
check is green.

## 1. When to use it, and what you need from the human

Use it when a new application needs a wrapper, or an existing wrapper parses output wrongly.

Ask the human for all four before you write anything:

1. the application's name (it becomes the wrapper's folder, `<app>`);
2. its binary, or the module that provides it;
3. the exact command line that was run, arguments included;
4. a real output file from that run, as the application printed it.

If there is no real output, STOP. Never invent, edit or "tidy" output: the wrapper is only as good
as the sample. Tell the human to run the application once, on a compute node, not the login node,
after loading the same modules the jobs will load. For example:

```bash
srun --nodes=2 --ntasks=2 --time=00:05:00 <binary> <args> > stdout.txt
```

Wait for `stdout.txt` (and `stderr.txt`, if the application prints results there) before going on.

## 2. The contract in 10 lines

1. A wrapper is a file `<app>.py` holding a class named `app` that subclasses `crab.wrappers.base.base`.
2. `benchmark_id`: the receipt name, normally the app name.
3. `executable`: the program name CRAB looks up on `PATH` when nothing else gives a binary.
4. `keys`: the sweep columns every row carries (for example `["size"]`), or `[]` for single values.
5. `metadata`: one entry per measured value, `{"name": ..., "unit": ..., "conv": True|False}`.
6. `conv: True` marks the value CRAB repeats runs for, until it converges.
7. `read_data()` returns a list of rows, one dict per sample.
8. Every row holds every key and every metric, and nothing else.
9. The output is in `self.stdout` (and `self.stderr`); files the application wrote are in `self.run_dir`.
10. If the output is not what you expect, raise. Never return zeros or an empty list: CRAB would record them as measurements.

The rest is on the CRAB wrapper page: https://hlc-crab.readthedocs.io/en/stable/extending/wrappers/

## 3. Steps

### a. Decide `keys` and `metadata`

Read the real output. Find the sweep column, if any: it becomes `keys`. List each measured value
with the unit the application prints, and set `conv: True` on the one that must converge.

Check: you can say, for every column of the output, whether it is a key, a metric or ignored.

### b. Create the wrapper

```bash
crab wrappers new <app> --local
```

This creates `<app>/<app>.py`, `<app>/README.md` and `<app>/samples/example/`, and prints the path
it created. `--local` keeps the wrapper private and git-ignored, in CRAB's local wrappers folder.

Check: the command printed `Created .../<app>/<app>.py`.

### c. Write `read_data()`

Edit `<app>.py`: set `executable`, `benchmark_id`, `keys` and `metadata`, and write `read_data()`
from the real output. Skip empty lines and `#` lines, parse the numbers, and raise `ValueError`
naming what is missing when a line or a value is not there.

Check: the file has no trace of the scaffold's `time:` parsing.

### d. Replace the scaffold sample

1. Copy the real output to `<app>/samples/example/stdout.txt`.
2. Write `<app>/samples/example/expected.json` from the output: a list with one object per row, in
   output order. With more than a few rows, generate it with a script that reads the raw output on
   its own. It must not call the wrapper, or a bug in the wrapper would be copied into the answer.
3. Set `<app>/samples/example/case.json` to the wrapper file, the arguments that were run and an
   empty `set`:

```json
{"wrapper": "<app>.py", "args": "<the args that were run>", "set": {}}
```

Check: nothing of the scaffold app is left in `stdout.txt`, `expected.json` or `case.json`.

### e. Run the sample test

```bash
crab wrappers test <app> --strict
```

Check: the last line reads `1 ok, 0 failed`. Read the failed count, not only the exit status.

### f. Break it once

Remove one data line from `stdout.txt`, or change one value in `expected.json`, and run the test
again. The last line must show a failed count above 0 (for example `0 ok, 2 failed`: a case that
fails under `--strict` also leaves the wrapper uncovered). Then restore the file and run it again
until it is green. A test that cannot go red proves nothing.

### g. Record where the binary lives

Ask the human for the binary's real path and the exact module line the jobs load. Do not guess
either. `benchmark_id` is the receipt name. Run this on the machine where the jobs will run:

```bash
crab receipts set <app> --binary <path of the binary> --pre-run "<module load line>"
```

`--pre-run` can be repeated, one command each. If the binary does not exist on the machine where
you run it, add `--allow-missing` and tell the human why.

Check: the command printed `Saved receipt '<app>': <path>`.

### h. Check the listing

```bash
crab wrappers list | grep <app>
```

Check: the line ends with `binary receipt: <path>`. A line ending with `binary missing` means
neither the receipt nor `executable` points at a file that exists: fix the receipt name (it must
equal `benchmark_id`), the path or `executable`. A line with `cannot load:` shows the Python error.

## 4. Rules

- Never edit CRAB itself. A change you think CRAB needs is a note for the human.
- Never commit or push. The human decides.
- One application per wrapper.
- Report values in the units the application prints.
- Ratios, slowdowns and interference belong to the analysis, not the wrapper.
- A wrapper meant for the shared crab-wrappers repository needs, in `case.json`, `"source": "real-run"`
  and a `"note"` naming the system, the date and the application version, plus a line in the app's
  `README.md` saying the same. See CONTRIBUTING.md, section "Add a real sample".

## 5. Done means

Show the human three things:

1. the last line of `crab wrappers test <app> --strict` (`1 ok, 0 failed`);
2. the `crab receipts set` command you ran, with its real values;
3. the `crab wrappers list` line for the wrapper.

Then tell the human the one thing to do next: use `<app>/<app>.py` as the `path` of the app in a
jobs file. To share the wrapper, open a pull request to the crab-wrappers repository.

## 6. Worked example: the shape of a latency benchmark

A real output starts with an empty line and three `#` header lines, then one `size latency` row per
message size:

```text

# <benchmark name and version>
# <datatype line>
# Size       Avg Latency(us)
1                       0.97
2                       0.97
```

There is one sweep column (`size`) and one measured value (`latency`, in `us`, the one to
converge). So `keys = ["size"]` and `metadata = [{"name": "latency", "unit": "us", "conv": True}]`.
`read_data()` skips empty and `#` lines and returns one dict per row, as on the CRAB wrapper page:

```python
def read_data(self):
    rows = []
    for line in self.stdout.splitlines():
        if line and not line.startswith("#"):
            size, latency = line.split()
            rows.append({"size": int(size), "latency": float(latency)})
    return rows
```

That example is short on purpose. It fails with an unclear error on a line with three columns, and
it returns an empty list when the output has no rows. Make yours raise `ValueError` with a message
that names the line or the missing part, and raise when no row was found. Then check it with the
steps above.

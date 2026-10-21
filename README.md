# CRAB wrappers

Shared wrappers for [CRAB](https://github.com/HLC-Lab/CRAB). A wrapper tells CRAB how to launch
one application and how to turn its output into measurements. There is one wrapper per
application, kept here so that everyone who runs that application parses its output the same
way.

## Using them

CRAB looks for a config's wrapper `path` (for example `blink/alltoall/alltoall_b.py`) in these
folders, in this order:

1. `local/wrappers/` inside your CRAB checkout, for private or in-progress wrappers (git-ignored);
2. each folder listed in `CRAB_PATH_WRAPPERS` (separate several with `:`), or the checkout's
   `wrappers/` folder when that variable is not set.

Clone this repository to one of those places, for example as `wrappers/` inside your CRAB
checkout. CRAB's `make` clones it into `wrappers/` and `crab update` updates it. A CRAB installed
with pip or pipx has no checkout: it clones this repository on first use, and `crab update`
keeps that clone current. `crab wrappers list` shows what CRAB finds and where each binary comes
from.

## The contract

A wrapper's `read_data()` returns rows: a list of dicts, one per sample, keyed by the metric
names plus any key columns (for example the message size of a sweep). The older shape, one list
of values per metric, is an error in CRAB 1.0: a run that returns it fails, and every wrapper in
this repository was migrated to rows. This is wrapper contract version 1, which CRAB reports as
`wrapper_api = 1`. The full guide is CRAB's
[Writing a wrapper](https://hlc-crab.readthedocs.io/extending/wrappers/) page, and
[CONTRIBUTING.md](CONTRIBUTING.md) lists the steps for adding one here.

## Versions

From CRAB 1.0, each CRAB release has a matching tag of this repository, named `vX.Y.Z` after the
CRAB version (the first, `v1.0.0`, is made at the 1.0 release). `crab update` puts the clone on
the tag that matches the installed CRAB, so the wrappers and the CRAB that runs them stay in step.
`crab update --head` follows `main` instead, for wrappers that are newer than your release. When
the repository has no tag for your CRAB version yet, an existing clone stays where it is.

## Layout

```
<app>/
  <wrapper>.py          one or more wrappers for the application
  _<helper>.py          shared code for that app's wrappers (not a wrapper itself)
  README.md             what it measures, how to install the app, where the samples come from
  samples/<case>/       real output and the values the wrapper must produce
    case.json           {"wrapper": "<wrapper>.py", "args": "...", "set": {...}}
    stdout.txt          the application's output (plus stderr.txt and any files it wrote)
    expected.json       the rows the wrapper must return for that output
```

## Verified and unverified wrappers

A wrapper is verified when at least one sample case covers it: `crab wrappers test <app>` runs
the wrapper on the saved output and compares the result with `expected.json`. The wrappers
listed in `unverified.txt` are exactly those with no sample case yet, so nothing checks their
parsing. Most of them came from CRAB before this repository existed and work as before.

A case's `case.json` says where its output comes from (`source`). The table counts a wrapper as
verified on a real run when some case for it holds output the application itself produced (a run
on a cluster, or the application's own reference output), and as verified on synthetic samples
only when every case for it was written or reshaped by hand.

| App | Wrappers | Verified (real run) | Verified (synthetic only) | Unverified |
|---|---|---|---|---|
| `blink` (2 need the fork blink-clean) | 40 | 2 | 2 | 36 |
| `graph500` | 1 | 0 | 1 | 0 |
| `quantum-espresso` (pw and ph, v6 and v7) | 4 | 4 | 0 | 0 |
| `others` | 40 | 0 | 11 | 29 |

## Contributing

New wrappers and fixes come in as pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md). A
pull request is merged when its sample cases and the tests pass in CI.

## License

MIT, see [LICENSE](LICENSE).

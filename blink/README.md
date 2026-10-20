# Blink wrappers

[Blink](https://github.com/HLC-Lab/blink) is a suite of MPI microbenchmarks for measuring how a
network behaves under different traffic patterns: collectives, incast, pairwise and ring
exchanges, and ping-pong. Each benchmark runs a number of iterations
(or until it is stopped) and prints one row per iteration.

Each wrapper here launches one Blink program and reads its table: one row per measured
iteration, with five durations in seconds (`Avg-Duration`, `Min-Duration`, `Max-Duration`,
`Median-Duration`, `MainRank-Duration`: the average, minimum, maximum and median over the ranks,
and the value on the main rank). `Avg-Duration` is the value CRAB repeats runs on until it
converges.

## Install Blink

Since 2026-05-22 Blink builds with CMake and names its programs after the collective they run
(`alltoall_nb`, `allreduce_b`, ...). You need CMake 3.16 or newer, a C and C++ compiler, and Open
MPI or MPICH:

```bash
git clone https://github.com/HLC-Lab/blink ~/blink
CC=mpicc CXX=mpicxx cmake -S ~/blink -B ~/blink/build -DCMAKE_BUILD_TYPE=Release -DBLINK_TESTS=OFF
cmake --build ~/blink/build -j
```

Clone Blink outside this repository. The programs end up in `~/blink/build/bin/`.
`-DBLINK_TESTS=OFF` skips Blink's own test suite, which would download googletest.

If CMake's MPI check fails on a module-based cluster, add `-DBLINK_MPI_WRAPPER=ON` (Open MPI
only) to the first command. That option assumes `CC` and `CXX` are MPI compiler wrappers.

Check a program with `mpirun -n 1 ~/blink/build/bin/alltoall_nb -h`. It prints the flags the
program accepts.

`crab setup` builds Blink this way in a CRAB whose Blink recipe uses CMake (the CRAB branch
`fix/blink-names` today). If you built Blink yourself, tell CRAB where the programs are with
`crab receipts set blink --binary ~/blink/build/bin`. The receipt must be the folder, not one
program.

If Blink was installed by an older CRAB, the `blink` receipt points at the fork's `bin/`, where
the new names do not exist. Run `crab setup` again (it offers to clear the old build) or
`crab receipts set blink --binary <path to build/bin>`. `crab wrappers list` does not check that
the file exists, so it will not warn you about a stale receipt.

## Wrapper names

A wrapper `blink/<group>/<name>.py` launches the Blink program `<name>`: the names are the same,
and `<group>` is the folder of Blink's `src/` that holds the program's source. The test
`tests/_test_blink_names.py` checks both, so a wrapper cannot drift from the program it runs or
from the upstream layout.

| Folder | Wrappers |
|---|---|
| `allgather/` | `allgather_b`, `allgather_comm_only`, `allgather_nb` |
| `allreduce/` | `allreduce_b`, `allreduce_nb` |
| `alltoall/` | `alltoall_b`, `alltoall_comm_only`, `alltoall_man`, `alltoall_nb` |
| `barrier/` | `barrier_b`, `barrier_nb` |
| `broadcast/` | `broadcast_b`, `broadcast_nb` |
| `gather/` | `gather_b`, `gather_nb` |
| `incast/` | `incast_b`, `incast_bsnbr`, `incast_get`, `incast_nb`, `incast_put` |
| `kpartners/` | `kpartners_nb` |
| `pairwise/` | `pairwise_b`, `pairwise_bsnbr`, `pairwise_nb` |
| `pingpong/` | `pingpong_b`, `pingpong_pairwise_b` |
| `reduce/` | `reduce_b`, `reduce_nb` |
| `reduce_scatter/` | `reduce_scatter_b`, `reduce_scatter_nb` |
| `ring/` | `ring_bsnbr`, `ring_nb` |
| `scatter/` | `scatter_b`, `scatter_nb` |
| `stencil/` | `stencil_2d_nb` |
| `tagmatch/` | `tagmatch_nb` |
| `tools/` | `checker`, `null_dummy` |

In a config, the wrapper path includes both folders, because CRAB does not search subfolders for
a bare file name:

```json
"path": "blink/alltoall/alltoall_nb.py"
```

Every benchmark takes the same common flags, except `null_dummy`, which ignores its arguments.
Run a program with `-h` for the full list. `tagmatch_nb` accepts the burst flags but does not
burst. The ones you will use most:

| Flag | Meaning |
|---|---|
| `-msgsize <bytes>` | message size in bytes (default 1024) |
| `-iter <n>` | measured iterations (default 1) |
| `-warmup <n>` | warm-up iterations, not measured (default 5) |
| `-endl` | run until stopped instead of for `-iter` iterations |
| `-maxsamples <n>` | rows kept (default 1000); with a larger `-iter` only the last 1000 measured iterations are reported |
| `-blength <duration>`, `-bpause <duration>` | burst length and pause between bursts; a bare number is seconds, and the suffixes `s`, `ms`, `us` and `ns` are accepted |
| `-bldist <exp\|pareto\|lognormal>`, `-bpdist <exp\|pareto\|lognormal>` | draw the burst length or the pause at random with that mean; `-blshape` and `-bpshape` set the shape |

`-h` also lists the flags of a single program. Upstream has them for `pairwise_*` (`-mode`,
`-offset`), `ring_*` (`-rring`), `kpartners_nb` (`-k`), `stencil_2d_nb` (`-dimx`, `-periodic`)
and `tagmatch_nb` (`-ntags`, `-sendorder`, `-recvorder`, `-prepost`, `-wildcard`).

Benchmarks reject arguments they do not know and positional arguments. Two things break a run:

- Do not pass `-pretty-print`. The wrapper reads the CSV table, and that flag replaces it.
- `pingpong_b` needs exactly 2 ranks and `pingpong_pairwise_b` an even number of ranks.

For example, an aggressor that sends 2 MiB messages in 10 ms bursts with a 1 ms pause between
them, until the victims finish (set `"collect": false, "end": "f"` for it):

```json
"args": "-endl -msgsize 2097152 -blength 0.01 -bpause 0.001"
```

## Updating a config that uses the old names

Before Blink moved to CMake, these wrappers had shorter names. A config written for those needs
the new ones:

| Old name | New name |
|---|---|
| `a2a_b` | `alltoall_b` |
| `a2a_nb` | `alltoall_nb` |
| `a2a_comm_only` | `alltoall_comm_only` |
| `a2a_man` | `alltoall_man` |
| `agtr_comm_only` | `allgather_comm_only` |
| `ardc_b` | `allreduce_b` |
| `ardc_nb` | `allreduce_nb` |
| `bdc_b` | `broadcast_b` |
| `bdc_nb` | `broadcast_nb` |
| `barrier` | `barrier_b` |
| `inc_b` | `incast_b` |
| `inc_bsnbr` | `incast_bsnbr` |
| `inc_get` | `incast_get` |
| `inc_nb` | `incast_nb` |
| `inc_put` | `incast_put` |
| `o2o_bsnbr` | `pairwise_bsnbr` |
| `o2o_nb` | `pairwise_nb` |
| `ping-pong_b` | `pingpong_b` |
| `pw-ping-pong_b` | `pingpong_pairwise_b` |

`ring_bsnbr`, `ring_nb`, `checker` and `null_dummy` keep their names. Every new name sits in a
folder (see the table above), so the new path is `blink/<group>/<name>.py`.

Two flags were renamed too:

| Old flag | New flag |
|---|---|
| `-bprand` | `-bpdist <exp\|pareto\|lognormal>` (shape `-bpshape`) |
| `-blrand` | `-bldist <exp\|pareto\|lognormal>` (shape `-blshape`) |

A config that still passes an old flag aborts with "Unknown argument". The `sed` command below
changes only wrapper names, so fix flags by hand.

The `sed` command below goes from the old names straight to the new paths. To rename the
wrappers in a config in place (the original is kept as `config.json.bak`):

```bash
sed -E -i.bak \
  -e 's#\bpw-ping-pong_b\.py#pingpong/pingpong_pairwise_b.py#g' \
  -e 's#\bping-pong_b\.py#pingpong/pingpong_b.py#g' \
  -e 's#\ba2a_(b|nb|comm_only|man)\.py#alltoall/alltoall_\1.py#g' \
  -e 's#\bagtr_comm_only\.py#allgather/allgather_comm_only.py#g' \
  -e 's#\bardc_(b|nb)\.py#allreduce/allreduce_\1.py#g' \
  -e 's#\bbdc_(b|nb)\.py#broadcast/broadcast_\1.py#g' \
  -e 's#\bbarrier\.py#barrier/barrier_b.py#g' \
  -e 's#\binc_(b|bsnbr|get|nb|put)\.py#incast/incast_\1.py#g' \
  -e 's#\bo2o_(bsnbr|nb)\.py#pairwise/pairwise_\1.py#g' \
  config.json
```

It only touches names ending in `.py`. If a path in your config has no `blink/` folder, add it by
hand.

`pingpong_b` also reads a different output now. The old fork printed a time and a bandwidth;
Blink's `pingpong_b` prints the same five durations as the other benchmarks, and so does the
wrapper.

## Bursty noise wrappers are gone

`bursty_noise_a2a` and `bursty_noise_incast` came from the fork
[blink-clean](https://github.com/SharkGamerZ/blink-clean); upstream Blink removed those programs,
so the wrappers are removed too. Upstream produces the same traffic with its normal benchmarks and
the burst flags: for all-to-all noise use `alltoall/alltoall_nb.py`, for incast noise use
`incast/incast_nb.py`, both with `-endl -blength <length> -bpause <pause>` (and `-msgsize`; the old
programs sent 2 MiB per peer, so `-msgsize 2097152`). Set `"collect": false, "end": "f"` for the
app, as before. The old programs took the pause first and the length second as bare positional
numbers; the new flags take them by name, and a bare number is seconds.

## Samples

`samples/` holds the output the wrappers are checked against (`crab wrappers test blink`). It
stays flat; a `case.json` names its wrapper as `<group>/<name>.py`. Four wrappers have samples:
`alltoall_b`, `allreduce_b`, `pingpong_b` and `pingpong_pairwise_b`.

The three Leonardo samples were run with the fork's `a2a_b` and `ardc_b` before the rename. The
table format is the same as upstream's. No sample comes from a CMake-built Blink yet.

| Sample | Source |
|---|---|
| `samples/leonardo-alltoall_b-1KiB` | Leonardo booster, 2 nodes x 16 ranks, Open MPI 4.1.6, captured 2026-10-07 with the CRAB sample kit |
| `samples/leonardo-alltoall_b-1MiB` | same run setup, 1 MiB messages |
| `samples/leonardo-allreduce_b-4KiB` | same run setup, `allreduce_b` with 4 KiB messages |
| `samples/alltoall_b-ucx-warnings` | synthetic: the 1 KiB capture with UCX warning lines added before and inside the table |
| `samples/alltoall_b-row-missing` | synthetic: the 1 KiB capture with a row removed; the wrapper must refuse it |
| `samples/alltoall_b-truncated` | synthetic: the 1 KiB capture cut after 60 rows, as when a job is killed; the wrapper must refuse it |
| `samples/pingpong_b-synthetic` | synthetic, shaped after the output of upstream `pingpong_b` |
| `samples/pingpong_pairwise_b-targets` | synthetic, shaped after the old fork's `pw-ping-pong_b` output (a targets line before the table), with rows from the 1 KiB capture |

The other wrappers have no sample yet and are listed in [`../unverified.txt`](../unverified.txt):
they launch their program and parse the same table, but nothing checks that on real output. The
ones added with the CMake names are `allgather_b`, `allgather_nb`, `barrier_nb`, `gather_b`,
`gather_nb`, `kpartners_nb`, `pairwise_b`, `reduce_b`, `reduce_nb`, `reduce_scatter_b`,
`reduce_scatter_nb`, `scatter_b`, `scatter_nb`, `stencil_2d_nb` and `tagmatch_nb`. A real capture
of any of them is a welcome contribution; see [../CONTRIBUTING.md](../CONTRIBUTING.md).

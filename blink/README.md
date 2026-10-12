# Blink wrappers

[Blink](https://github.com/HLC-Lab/blink) is a suite of MPI microbenchmarks for measuring how a
network behaves under different traffic patterns: collectives, incast, pairwise and ring
exchanges, ping-pong, and bursty background noise. Each benchmark runs a number of iterations
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
git clone https://github.com/HLC-Lab/blink
CC=mpicc CXX=mpicxx cmake -S blink -B blink/build -DCMAKE_BUILD_TYPE=Release -DBLINK_TESTS=OFF
cmake --build blink/build -j
```

The programs end up in `blink/build/bin/`. `-DBLINK_TESTS=OFF` skips Blink's own test suite,
which would download googletest. `crab setup` builds Blink this way. If you built it yourself,
tell CRAB where the programs are with `crab receipts set blink --binary <path to build/bin>`.

## Wrapper names

A wrapper `blink/<name>.py` launches the Blink program `<name>`: the names are the same. The test
`tests/_test_blink_names.py` checks it, so a wrapper cannot drift from the program it runs.

In a config, the wrapper path includes the folder, because CRAB does not search subfolders for a
bare file name:

```json
"path": "blink/alltoall_nb.py"
```

Every benchmark takes the same common flags; run one with `-h` for the full list. The ones you
will use most:

| Flag | Meaning |
|---|---|
| `-msgsize <bytes>` | message size in bytes |
| `-iter <n>` | measured iterations |
| `-warmup <n>` | warm-up iterations, not measured |
| `-endl` | run until stopped instead of for `-iter` iterations |
| `-blength <duration>`, `-bpause <duration>` | burst length and pause between bursts; a bare number is seconds, and the suffixes `s`, `ms`, `us` and `ns` are accepted |

Benchmarks reject arguments they do not know and positional arguments. For example, an
aggressor that sends short bursts until the victims finish:

```json
"args": "-endl -blength 0.0001 -bpause 0.01"
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

`ring_bsnbr`, `ring_nb`, `checker` and `null_dummy` keep their names.

To rename the wrappers in a config in place (the original is kept as `config.json.bak`):

```bash
sed -E -i.bak \
  -e 's#\bpw-ping-pong_b\.py#pingpong_pairwise_b.py#g' \
  -e 's#\bping-pong_b\.py#pingpong_b.py#g' \
  -e 's#\ba2a_(b|nb|comm_only|man)\.py#alltoall_\1.py#g' \
  -e 's#\bagtr_comm_only\.py#allgather_comm_only.py#g' \
  -e 's#\bardc_(b|nb)\.py#allreduce_\1.py#g' \
  -e 's#\bbdc_(b|nb)\.py#broadcast_\1.py#g' \
  -e 's#\bbarrier\.py#barrier_b.py#g' \
  -e 's#\binc_(b|bsnbr|get|nb|put)\.py#incast_\1.py#g' \
  -e 's#\bo2o_(bsnbr|nb)\.py#pairwise_\1.py#g' \
  config.json
```

It only touches names ending in `.py`. If a path in your config has no `blink/` folder, add it by
hand.

`pingpong_b` also reads a different output now. The old fork printed a time and a bandwidth;
Blink's `pingpong_b` prints the same five durations as the other benchmarks, and so does the
wrapper.

## Wrappers that need the fork

Three wrappers do not work with upstream Blink, which has no such programs:

| Wrapper | What it is |
|---|---|
| `bursty_noise_a2a.py` | bursty all-to-all noise (fork only) |
| `bursty_noise_incast.py` | bursty incast noise (fork only) |
| `workerpool.py` | scheduler for the noise workers (fork only); it runs `workerpool_scheduler.py` from `$CRAB_ROOT/benchmarks/workerpool/` |

They need the fork [blink-clean](https://github.com/SharkGamerZ/blink-clean), which builds with a
Makefile, keeps the old short names for its other programs, and puts its
binaries in `bin/`. Point the `blink` receipt at that `bin/` when you use them.

## Samples

`samples/` holds the output the wrappers are checked against (`crab wrappers test blink`). Four
wrappers have samples: `alltoall_b`, `allreduce_b`, `pingpong_b` and `pingpong_pairwise_b`.

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

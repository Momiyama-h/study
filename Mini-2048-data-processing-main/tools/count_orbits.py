#!/usr/bin/env python3
"""
Count raw/canonical unique boards and orbit size distribution from mini2048 CSV logs.

Usage examples:
  python3 tools/count_orbits.py logs1.csv logs2.csv
  python3 tools/count_orbits.py --topk 10 logs/*.csv
  python3 tools/count_orbits.py --no-raw-set logs/*.csv
  python3 tools/count_orbits.py --selftest
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, List, Tuple


Board = Tuple[int, int, int, int, int, int, int, int, int]


def idx(r: int, c: int) -> int:
    return r * 3 + c


def build_map(transform: Callable[[int, int], Tuple[int, int]]) -> List[int]:
    m = [0] * 9
    for r in range(3):
        for c in range(3):
            r2, c2 = transform(r, c)
            m[idx(r2, c2)] = idx(r, c)
    return m


def rot90(r: int, c: int) -> Tuple[int, int]:
    return c, 2 - r


def rot180(r: int, c: int) -> Tuple[int, int]:
    return 2 - r, 2 - c


def rot270(r: int, c: int) -> Tuple[int, int]:
    return 2 - c, r


def mirror_lr(r: int, c: int) -> Tuple[int, int]:
    return r, 2 - c


TRANSFORMS = [
    lambda r, c: (r, c),  # identity
    rot90,
    rot180,
    rot270,
    mirror_lr,
    lambda r, c: rot90(*mirror_lr(r, c)),
    lambda r, c: rot180(*mirror_lr(r, c)),
    lambda r, c: rot270(*mirror_lr(r, c)),
]

MAPS = [build_map(t) for t in TRANSFORMS]


def transform(board: Board, mapping: List[int]) -> Board:
    return tuple(board[mapping[i]] for i in range(9))  # type: ignore[misc]


def all_symmetries(board: Board) -> List[Board]:
    return [transform(board, m) for m in MAPS]


def canonical(board: Board) -> Board:
    return min(all_symmetries(board))


def orbit_size(board: Board) -> int:
    return len(set(all_symmetries(board)))


def iter_boards(paths: Iterable[Path], input_format: str) -> Tuple[int, int, Iterable[Board]]:
    warn = 0
    total = 0
    boards: List[Board] = []
    required = [f"tile{i}" for i in range(9)]
    for p in paths:
        fmt = input_format
        if fmt == "auto":
            fmt = "csv" if p.suffix.lower() == ".csv" else "state"
        if fmt == "csv":
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None or any(k not in reader.fieldnames for k in required):
                    warn += 1
                    continue
                for row in reader:
                    try:
                        vals = tuple(int(row[f"tile{i}"]) for i in range(9))
                    except Exception:
                        warn += 1
                        continue
                    if len(vals) != 9:
                        warn += 1
                        continue
                    boards.append(vals)  # type: ignore[arg-type]
                    total += 1
        elif fmt == "state":
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("gameover_turn"):
                        continue
                    parts = line.split()
                    if len(parts) != 9:
                        warn += 1
                        continue
                    try:
                        vals = tuple(int(x) for x in parts)
                    except Exception:
                        warn += 1
                        continue
                    boards.append(vals)  # type: ignore[arg-type]
                    total += 1
        else:
            raise SystemExit(f"Unknown input_format: {input_format}")
    return total, warn, boards


def selftest() -> int:
    # maps are permutations
    if len(MAPS) != 8:
        raise SystemExit("selftest failed: MAPS length != 8")
    for m in MAPS:
        if sorted(m) != list(range(9)):
            raise SystemExit("selftest failed: mapping is not permutation")

    # orbit size examples
    b1 = (0, 0, 0,
          0, 0, 0,
          0, 0, 0)
    b2 = (1, 2, 1,
          3, 4, 3,
          1, 2, 1)  # vertical+horizontal symmetric, not 90-rot
    b3 = (1, 2, 3,
          4, 5, 6,
          3, 2, 1)  # 180-rot symmetric only
    b4 = (0, 1, 2,
          3, 4, 5,
          6, 7, 8)  # no symmetry
    sizes = [orbit_size(b1), orbit_size(b2), orbit_size(b3), orbit_size(b4)]
    if sizes[0] != 1:
        raise SystemExit("selftest failed: orbit size 1 example")
    if sizes[1] != 2:
        raise SystemExit("selftest failed: orbit size 2 example")
    if sizes[2] != 4:
        raise SystemExit("selftest failed: orbit size 4 example")
    if sizes[3] != 8:
        raise SystemExit("selftest failed: orbit size 8 example")
    print("selftest OK")
    return 0


def format_board(b: Board) -> str:
    rows = [b[0:3], b[3:6], b[6:9]]
    return " / ".join(" ".join(str(x) for x in r) for r in rows)


def main() -> int:
    epilog = """examples:
  python3 tools/count_orbits.py logs1.csv logs2.csv
  python3 tools/count_orbits.py --topk 10 logs/*.csv
  python3 tools/count_orbits.py --no-raw-set logs/*.csv
  python3 tools/count_orbits.py --selftest
"""
    ap = argparse.ArgumentParser(
        description="Count raw/canonical unique boards and orbit sizes from CSV logs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    ap.add_argument("csvs", nargs="*", help="CSV files (tile0..tile8) or state.txt files")
    ap.add_argument(
        "--input-format",
        choices=["auto", "csv", "state"],
        default="auto",
        help="input format (auto: .csv=csv, otherwise state)",
    )
    ap.add_argument("--topk", type=int, default=0, help="show top K canonical boards")
    ap.add_argument("--no-raw-set", action="store_true", help="skip raw unique set (save memory)")
    ap.add_argument("--selftest", action="store_true", help="run self test and exit")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.csvs:
        raise SystemExit("ERROR: specify at least one CSV file")

    paths = [Path(p) for p in args.csvs]
    total, warn, boards = iter_boards(paths, args.input_format)

    raw_set = set() if not args.no_raw_set else None
    canonical_counts: Counter[Board] = Counter()
    orbit_sizes: dict[Board, int] = {}

    for b in boards:
        if raw_set is not None:
            raw_set.add(b)
        c = canonical(b)
        if c not in canonical_counts:
            orbit_sizes[c] = orbit_size(c)
        canonical_counts[c] += 1

    raw_unique = len(raw_set) if raw_set is not None else None
    canonical_unique = len(canonical_counts)
    if raw_unique:
        compression = canonical_unique / raw_unique
    else:
        compression = None

    print(f"total boards (valid rows): {total}")
    print(f"skipped rows (warnings): {warn}")
    if raw_unique is None:
        print("raw unique boards: skipped (--no-raw-set)")
    else:
        print(f"raw unique boards: {raw_unique}")
    print(f"canonical unique boards: {canonical_unique}")
    if compression is None:
        print("compression (canonical/raw): n/a")
    else:
        print(f"compression (canonical/raw): {compression:.6f}")

    # orbit size distribution (per canonical)
    dist = Counter(orbit_sizes.values())
    print("orbit size distribution:")
    for size in sorted(dist):
        count = dist[size]
        pct = (count / canonical_unique * 100) if canonical_unique else 0.0
        print(f"  size={size}: {count} ({pct:.2f}%)")

    if args.topk and args.topk > 0:
        print(f"top {args.topk} canonical boards:")
        for b, cnt in canonical_counts.most_common(args.topk):
            osize = orbit_sizes.get(b, 0)
            print(f"  count={cnt} orbit={osize} board={format_board(b)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

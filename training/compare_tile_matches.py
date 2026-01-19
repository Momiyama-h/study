#!/usr/bin/env python3
"""Count matching tile patterns between two CSV logs and list the top 10.

The script reads two CSV files that contain columns named tile0..tile8.
It counts how many times each complete tile pattern appears in both files
and prints the top 10 patterns with the highest shared occurrence counts.

Usage:
    # prev: python compare_tile_matches.py board_log.csv board_log_nosym.csv
    python compare_tile_matches.py board_log.csv board_log_notsym.csv
"""

import argparse
import csv
from collections import Counter
from typing import Counter as CounterType, Iterable, Tuple

TileState = Tuple[int, ...]

def load_counts(path: str) -> CounterType[TileState]:
    """Load tile counts from a CSV file."""
    counter: CounterType[TileState] = Counter()
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        tile_fields = [f"tile{i}" for i in range(9)]
        for row in reader:
            state = tuple(int(row[field]) for field in tile_fields)
            counter[state] += 1
    return counter


def format_state(state: TileState) -> str:
    """Format tile state for printing."""
    return ",".join(str(v) for v in state)


def find_matches(counts_a: CounterType[TileState], counts_b: CounterType[TileState], top_n: int = 10) -> Iterable[Tuple[TileState, int]]:
    """Yield the top shared patterns sorted by shared count descending."""
    shared_states = counts_a.keys() & counts_b.keys()
    matches = []
    for state in shared_states:
        matches.append((state, min(counts_a[state], counts_b[state])))
    matches.sort(key=lambda item: item[1], reverse=True)
    return matches[:top_n]


def main() -> None:
    parser = argparse.ArgumentParser(description="Count matching tile patterns across two CSV logs")
    parser.add_argument("csv_a", help="First CSV file (expects tile0..tile8 columns)")
    parser.add_argument("csv_b", help="Second CSV file (expects tile0..tile8 columns)")
    parser.add_argument("--top", type=int, default=10, help="Number of patterns to show (default: 10)")
    args = parser.parse_args()

    counts_a = load_counts(args.csv_a)
    counts_b = load_counts(args.csv_b)

    print(f"Loaded {len(counts_a)} unique patterns from {args.csv_a}")
    print(f"Loaded {len(counts_b)} unique patterns from {args.csv_b}")

    matches = find_matches(counts_a, counts_b, args.top)
    if not matches:
        print("No matching patterns found.")
        return

    print("\nTop matching patterns (pattern -> shared count):")
    for idx, (state, count) in enumerate(matches, start=1):
        print(f"{idx:2d}: [{format_state(state)}] -> {count}")


if __name__ == "__main__":
    main()

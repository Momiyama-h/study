#!/usr/bin/env python3
import argparse
import csv
import math
import re
from pathlib import Path
from typing import List, Optional


SCORE_RE = re.compile(r"score:\s*(\d+)")


def parse_scores(state_path: Path) -> List[int]:
    scores: List[int] = []
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("gameover_turn:"):
                m = SCORE_RE.search(line)
                if m:
                    scores.append(int(m.group(1)))
    return scores


def parse_seed(dir_name: str) -> Optional[int]:
    if not dir_name.startswith("seed"):
        return None
    try:
        return int(dir_name[4:])
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="board_data の state.txt から seed×条件の平均/SD をCSVに集計する"
    )
    parser.add_argument("--run-name", required=True, help="run_name under board_data")
    parser.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root",
    )
    parser.add_argument(
        "--tuples",
        default="4,5,6",
        help="comma-separated tuples (default: 4,5,6)",
    )
    parser.add_argument(
        "--sym-list",
        default="sym,notsym",
        help="comma-separated sym list (default: sym,notsym)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="output csv path (default: <board_root>/<run_name>/score_seed_matrix.csv)",
    )
    args = parser.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    cols = [f"NT{t}_{s}" for t in tuples for s in syms]

    seeds = []
    for p in run_dir.glob("seed*"):
        if p.is_dir():
            seed = parse_seed(p.name)
            if seed is not None:
                seeds.append(seed)
    seeds = sorted(seeds)

    rows = []
    for seed in seeds:
        row = {"seed": seed}
        for t in tuples:
            for s in syms:
                state = run_dir / f"seed{seed}" / f"NT{t}_{s}" / "state.txt"
                key = f"NT{t}_{s}"
                if not state.exists():
                    row[key] = ""
                    continue
                scores = parse_scores(state)
                if not scores:
                    row[key] = ""
                    continue
                mean = sum(scores) / len(scores)
                row[key] = f"{mean:.4f}"
        rows.append(row)

    means = {"seed": "mean"}
    sds = {"seed": "sd"}
    for c in cols:
        vals = [float(r[c]) for r in rows if r.get(c)]
        if not vals:
            means[c] = ""
            sds[c] = ""
            continue
        m = sum(vals) / len(vals)
        if len(vals) >= 2:
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            sd = math.sqrt(max(var, 0.0))
        else:
            sd = 0.0
        means[c] = f"{m:.4f}"
        sds[c] = f"{sd:.4f}"

    output = (
        Path(args.output)
        if args.output
        else run_dir / "score_seed_matrix.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["seed"] + cols)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(means)
        writer.writerow(sds)
    print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

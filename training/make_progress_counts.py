#!/usr/bin/env python3
"""
Count boards by progress from state.txt for each seed/NT/sym under board_data.

Outputs:
  - CSV: progress,count
  - Plot: line plot of count vs progress

Default output dir:
  /HDD/momiyama2/data/study/analysis_outputs/<run_name>/progress_counts
"""
import argparse
from collections import Counter
from pathlib import Path
from typing import Iterable, List


def iter_state_lines(state_path: Path) -> Iterable[List[int]]:
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 9:
                # Skip "gameover_turn: ..." lines
                continue
            try:
                vals = list(map(int, parts))
            except ValueError:
                continue
            yield vals


def progress_calc(vals: List[int]) -> int:
    return sum((1 << v) for v in vals if v) // 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count boards by progress (sum of tiles / 2) from state.txt for each "
            "seed/NT/sym under board_data."
        )
    )
    parser.add_argument("--run-name", required=True, help="run_name under board_data")
    parser.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root",
    )
    parser.add_argument(
        "--analysis-root",
        default="/HDD/momiyama2/data/study/analysis_outputs",
        help="analysis_outputs root",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="output dir (default: analysis_root/<run_name>/progress_counts)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "plot", "both"],
        default="both",
        help="output format (default: both)",
    )
    parser.add_argument(
        "--ext",
        default="png",
        help="plot file extension (png/pdf, default: png)",
    )
    parser.add_argument(
        "--grid-y",
        action="store_true",
        help="add horizontal grid lines to plots",
    )
    parser.add_argument(
        "--x-max",
        type=int,
        default=None,
        help="optional max x (progress) for plots",
    )
    args = parser.parse_args()

    run_dir = Path(args.board_root) / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"run_dir not found: {run_dir}")

    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path(args.analysis_root) / args.run_name / "progress_counts"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    want_csv = args.format in ("csv", "both")
    want_plot = args.format in ("plot", "both")

    if want_plot:
        try:
            import matplotlib.pyplot as plt  # noqa: F401
        except Exception as e:
            print(f"Plot disabled: {e}")
            want_plot = False

    ext = args.ext.lstrip(".")

    # Find all state.txt under seed*/NT*_*[/eval_seed*] directories.
    state_files = []
    for p in run_dir.rglob("state.txt"):
        parent = p.parent
        if parent.name.startswith("eval_seed"):
            nt_dir = parent.parent
            seed_dir = nt_dir.parent if nt_dir else None
        else:
            nt_dir = parent
            seed_dir = parent.parent if parent else None
        if nt_dir and seed_dir and nt_dir.name.startswith("NT") and seed_dir.name.startswith("seed"):
            state_files.append(p)
    state_files = sorted(set(state_files))

    if not state_files:
        raise SystemExit(f"no state.txt found under: {run_dir}")

    # normalize duplicates from pattern attempts
    state_files = sorted(set(state_files))

    for state_path in state_files:
        nt_dir = state_path.parent
        eval_seed = ""
        if nt_dir.name.startswith("eval_seed"):
            eval_seed = nt_dir.name
            nt_dir = nt_dir.parent
        seed_dir = nt_dir.parent
        seed = seed_dir.name
        nt = nt_dir.name

        counts = Counter()
        for vals in iter_state_lines(state_path):
            counts[progress_calc(vals)] += 1

        if not counts:
            continue

        xs = sorted(counts.keys())
        ys = [counts[x] for x in xs]
        base = f"progress_count_{seed}_{nt}"
        if eval_seed:
            base = f"{base}_{eval_seed}"

        if want_csv:
            csv_path = out_dir / f"{base}.csv"
            with csv_path.open("w", encoding="utf-8") as w:
                w.write("progress,count\n")
                for x in xs:
                    w.write(f"{x},{counts[x]}\n")

        if want_plot:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(6, 4))
            plt.plot(xs, ys, linewidth=1)
            plt.title(f"{seed}/{nt}")
            plt.xlabel("progress")
            plt.ylabel("count")
            if args.grid_y:
                plt.grid(axis="y", alpha=0.3)
            if args.x_max is not None:
                plt.xlim(0, args.x_max)
            plt.tight_layout()
            out_path = out_dir / f"{base}.{ext}"
            plt.savefig(out_path)
            plt.close()

    print(f"Saved to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from collections import defaultdict
import math
import sys

try:
    import matplotlib.pyplot as plt
except Exception as e:
    print("ERROR: matplotlib is required:", e, file=sys.stderr)
    raise


def parse_args():
    p = argparse.ArgumentParser(
        description="Plot seed-mean score vs traincount_total from legacy log_score.csv."
    )
    p.add_argument("--run-name", required=True, help="run_name under ntuple_dat")
    p.add_argument(
        "--ntuple-dat-root",
        default="/HDD/momiyama2/data/study/ntuple_dat",
        help="root of ntuple_dat",
    )
    p.add_argument("--tuples", default="4,6", help="comma-separated tuples, e.g. 4,6")
    p.add_argument(
        "--sym-list", default="sym,notsym", help="comma-separated sym list"
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="output dir (default: analysis_outputs/<run_name>/score_log)",
    )
    p.add_argument(
        "--file-prefix",
        default="score_log_mean_legacy",
        help="output filename prefix",
    )
    return p.parse_args()


def mean_sd(vals):
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


def read_legacy_csv(fp: Path):
    rows = []
    with fp.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row.get("traincount_total", ""))
                y = float(row.get("avg_score", ""))
                rows.append((x, y))
            except Exception:
                continue
    return rows


def aggregate(files):
    buckets = defaultdict(lambda: defaultdict(list))
    for fp in files:
        rows = read_legacy_csv(fp)
        for x, y in rows:
            buckets[fp][x].append(y)
    return buckets


def plot_tuple(out_dir: Path, prefix: str, tuple_id: int, sym_list, run_dir: Path):
    plt.figure(figsize=(8, 5))

    for sym in sym_list:
        cond = f"NT{tuple_id}_{sym}"
        # collect all log_score.csv under run/seed*/cond
        files = list(run_dir.glob(f"seed*/{cond}/log_score.csv"))
        if not files:
            continue

        # condition -> x -> list of y across seeds
        series = defaultdict(list)
        for fp in files:
            for x, y in read_legacy_csv(fp):
                series[x].append(y)

        xs = sorted(series.keys())
        means = []
        sds = []
        for x in xs:
            m, sd = mean_sd(series[x])
            means.append(m)
            sds.append(sd)

        plt.plot(xs, means, label=cond)
        plt.fill_between(
            xs,
            [m - s for m, s in zip(means, sds)],
            [m + s for m, s in zip(means, sds)],
            alpha=0.2,
        )

    plt.xlabel("traincount_total")
    plt.ylabel("avg_score (seed mean ± SD)")
    plt.title(f"Score mean ± SD vs traincount_total (NT{tuple_id})")
    plt.legend()
    plt.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prefix}_NT{tuple_id}_update.png"
    plt.savefig(out_path)
    plt.close()
    print(f"saved: {out_path}")


def main():
    args = parse_args()
    run_dir = Path(args.ntuple_dat_root) / args.run_name
    if not run_dir.exists():
        print(f"ERROR: run_name dir not found: {run_dir}", file=sys.stderr)
        return 1

    tuples = [int(t.strip()) for t in args.tuples.split(",") if t.strip()]
    sym_list = [s.strip() for s in args.sym_list.split(",") if s.strip()]

    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs") / args.run_name / "score_log"
    )

    for t in tuples:
        plot_tuple(out_dir, args.file_prefix, t, sym_list, run_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

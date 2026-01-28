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
        description="Plot seed-mean score vs update_count or CPU time from log_score CSVs."
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
        "--x-axis",
        choices=["update", "cpu"],
        default="update",
        help="x-axis: update=traincount_total or cpu=cpu_sec_total",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="output dir (default: analysis_outputs/<run_name>/score_log)",
    )
    p.add_argument(
        "--file-prefix",
        default="score_log_mean",
        help="output filename prefix",
    )
    return p.parse_args()


def read_logs(run_dir: Path):
    files = list(run_dir.rglob("log_score_*_pid*.csv"))
    return files


def aggregate(files, want_conditions, x_axis):
    # condition -> x -> list of score_mean
    buckets = {cond: defaultdict(list) for cond in want_conditions}
    for fp in files:
        try:
            with fp.open() as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cond = row.get("condition")
                    if cond not in buckets:
                        continue
                    if x_axis == "update":
                        x = float(row.get("traincount_total", ""))
                    else:
                        x = float(row.get("cpu_sec_total", ""))
                    y = float(row.get("score_mean", ""))
                    buckets[cond][x].append(y)
        except Exception as e:
            print(f"WARN: failed to read {fp}: {e}", file=sys.stderr)
    return buckets


def mean_sd(vals):
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


def plot_for_tuple(out_dir: Path, prefix: str, tuple_id: int, sym_list, buckets, x_axis):
    plt.figure(figsize=(8, 5))
    for sym in sym_list:
        cond = f"nt{tuple_id}_{sym}"
        series = buckets.get(cond, {})
        if not series:
            continue
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

    plt.xlabel("traincount_total" if x_axis == "update" else "cpu_sec_total")
    plt.ylabel("score_mean (seed mean ± SD)")
    plt.title(
        f"Score mean ± SD vs {('update_count' if x_axis=='update' else 'cpu_sec')} (NT{tuple_id})"
    )
    plt.legend()
    plt.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prefix}_NT{tuple_id}_{x_axis}.png"
    plt.savefig(out_path)
    plt.close()
    print(f"saved: {out_path}")


def main():
    args = parse_args()
    run_dir = Path(args.ntuple_dat_root) / args.run_name
    if not run_dir.exists():
        print(f"ERROR: run_name dir not found: {run_dir}", file=sys.stderr)
        return 1

    files = read_logs(run_dir)
    if not files:
        print(f"ERROR: no log_score_*_pid*.csv found under {run_dir}", file=sys.stderr)
        return 1

    tuples = [int(t.strip()) for t in args.tuples.split(",") if t.strip()]
    sym_list = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    want_conditions = [f"nt{t}_{s}" for t in tuples for s in sym_list]

    buckets = aggregate(files, set(want_conditions), args.x_axis)

    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs") / args.run_name / "score_log"
    )

    for t in tuples:
        plot_for_tuple(out_dir, args.file_prefix, t, sym_list, buckets, args.x_axis)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

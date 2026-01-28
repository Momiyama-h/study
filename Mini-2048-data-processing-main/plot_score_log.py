#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load_series(dat_root: Path, run_name: str):
    series = defaultdict(list)
    for path in dat_root.glob(str(Path(run_name) / "seed*" / "NT*_*" / "log_score.csv")):
        parts = path.parent.name.split("_", 1)
        if len(parts) != 2:
            continue
        nt_tag, sym_tag = parts
        key = f"{nt_tag}_{sym_tag}"
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    traincount = int(float(row["traincount_total"]))
                    avg_score = float(row["avg_score"])
                except (KeyError, ValueError):
                    continue
                series[key].append((traincount, avg_score))
    return series


def aggregate(series):
    aggregated = {}
    for key, points in series.items():
        by_x = defaultdict(list)
        for x, y in points:
            by_x[x].append(y)
        xs = sorted(by_x.keys())
        means = []
        sds = []
        for x in xs:
            vals = by_x[x]
            mean = sum(vals) / len(vals)
            means.append(mean)
            if len(vals) < 2:
                sds.append(0.0)
            else:
                var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
                sds.append(var ** 0.5)
        aggregated[key] = (xs, means, sds)
    return aggregated


def plot(aggregated, out_path: Path, title_suffix: str | None = None):
    if not aggregated:
        raise SystemExit("no log_score.csv found for run_name")
    plt.figure(figsize=(10, 6))
    for key in sorted(aggregated.keys()):
        xs, ys, sds = aggregated[key]
        if not xs:
            continue
        line, = plt.plot(xs, ys, label=key)
        color = line.get_color()
        plt.fill_between(
            xs,
            [y - s for y, s in zip(ys, sds)],
            [y + s for y, s in zip(ys, sds)],
            alpha=0.12,
            hatch="///",
            edgecolor=color,
            linewidth=0.0,
        )
    plt.xlabel("traincount")
    plt.ylabel("average_score")
    title = "Score vs Traincount (mean across seeds)"
    if title_suffix:
        title = f"{title} - {title_suffix}"
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", required=True)
    parser.add_argument(
        "--dat-root", default="/HDD/momiyama2/data/study/ntuple_dat"
    )
    parser.add_argument(
        "--out-root", default="/HDD/momiyama2/data/study/analysis_outputs"
    )
    parser.add_argument("--output", default="score_log.png")
    parser.add_argument(
        "--split-nt",
        action="store_true",
        help="split NT4 and NT6 into separate plots",
    )
    args = parser.parse_args()

    dat_root = Path(args.dat_root)
    out_root = Path(args.out_root)

    series = load_series(dat_root, args.run_name)
    aggregated = aggregate(series)
    out_base = out_root / args.run_name
    if args.split_nt:
        for nt_tag in ("NT4", "NT6"):
            nt_series = {
                k: v for k, v in aggregated.items() if k.startswith(f"{nt_tag}_")
            }
            if not nt_series:
                continue
            out_name = Path(args.output)
            if out_name.suffix:
                out_file = out_name.stem + f"_{nt_tag}" + out_name.suffix
            else:
                out_file = out_name.name + f"_{nt_tag}"
            plot(nt_series, out_base / out_file, title_suffix=nt_tag)
    else:
        out_path = out_base / args.output
        plot(aggregated, out_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import argparse
import csv
import math
from typing import List, Tuple


def parse_eval_txt(path: str) -> List[float]:
    # eval.txt: each line has 4 evals (one per action). We take max as after-state value.
    vals = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if not parts:
                continue
            try:
                nums = [float(x) for x in parts]
            except ValueError:
                continue
            vals.append(max(nums))
    return vals


def parse_pp_eval_after(path: str) -> List[float]:
    vals = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                vals.append(float(line))
            except ValueError:
                continue
    return vals


def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, int]:
    # Returns slope, intercept, n; NaN if not computable.
    pairs = [(a, b) for a, b in zip(x, y) if math.isfinite(a) and math.isfinite(b)]
    n = len(pairs)
    if n < 2:
        return (math.nan, math.nan, n)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((v - mean_x) ** 2 for v in xs)
    if var_x == 0:
        return (math.nan, math.nan, n)
    cov_xy = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    slope = cov_xy / var_x
    intercept = mean_y - slope * mean_x
    return (slope, intercept, n)


def mean_sd(values: List[float]) -> Tuple[float, float]:
    vals = [v for v in values if math.isfinite(v)]
    if not vals:
        return (math.nan, math.nan)
    mean = sum(vals) / len(vals)
    if len(vals) < 2:
        return (mean, math.nan)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    return (mean, math.sqrt(var))


def main():
    ap = argparse.ArgumentParser(
        description="Compute regression (slope/intercept) between eval.txt and pp-eval-after-state.txt for each seed/NT/sym"
    )
    ap.add_argument("--run-name", required=True)
    ap.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root",
    )
    ap.add_argument("--tuples", default="4,5,6")
    ap.add_argument("--sym-list", default="sym,notsym")
    ap.add_argument("--seed-start", type=int, required=True)
    ap.add_argument("--seed-end", type=int, required=True)
    ap.add_argument(
        "--out-dir",
        default=None,
        help="output dir (default: analysis_outputs/<run_name>/pp_regression)",
    )
    args = ap.parse_args()

    tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]

    out_dir = args.out_dir
    if not out_dir:
        out_dir = os.path.join(
            "/HDD/momiyama2/data/study/analysis_outputs", args.run_name, "pp_regression"
        )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pp_regression_evaltxt.csv")

    # build column list
    columns = []
    for t in tuples:
        for s in syms:
            columns.append(f"NT{t}_{s}_slope")
            columns.append(f"NT{t}_{s}_intercept")
            columns.append(f"NT{t}_{s}_n")

    rows = []
    for seed in range(args.seed_start, args.seed_end + 1):
        row = {"seed": seed}
        for t in tuples:
            for s in syms:
                base = os.path.join(
                    args.board_root, args.run_name, f"seed{seed}", f"NT{t}_{s}"
                )
                eval_path = os.path.join(base, "eval.txt")
                pp_path = os.path.join(base, "pp-eval-after-state.txt")

                slope_key = f"NT{t}_{s}_slope"
                intercept_key = f"NT{t}_{s}_intercept"
                n_key = f"NT{t}_{s}_n"

                if not (os.path.exists(eval_path) and os.path.exists(pp_path)):
                    row[slope_key] = math.nan
                    row[intercept_key] = math.nan
                    row[n_key] = 0
                    continue

                x = parse_eval_txt(eval_path)
                y = parse_pp_eval_after(pp_path)
                if not x or not y:
                    row[slope_key] = math.nan
                    row[intercept_key] = math.nan
                    row[n_key] = 0
                    continue

                n = min(len(x), len(y))
                if n < len(x) or n < len(y):
                    x = x[:n]
                    y = y[:n]

                slope, intercept, n_used = linear_regression(x, y)
                row[slope_key] = slope
                row[intercept_key] = intercept
                row[n_key] = n_used

        rows.append(row)

    # append mean / sd rows for slope & intercept (n is not aggregated)
    mean_row = {"seed": "mean"}
    sd_row = {"seed": "sd"}
    for col in columns:
        if col.endswith("_n"):
            mean_row[col] = ""
            sd_row[col] = ""
            continue
        vals = [r.get(col, math.nan) for r in rows]
        mean, sd = mean_sd(vals)
        mean_row[col] = mean
        sd_row[col] = sd

    rows.append(mean_row)
    rows.append(sd_row)

    with open(out_path, "w", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=["seed"] + columns)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()

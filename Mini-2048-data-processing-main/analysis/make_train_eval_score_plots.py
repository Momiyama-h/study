#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from make_train_eval_score_matrix import (
    build_rows,
    list_eval_seeds,
    list_train_seeds,
    list_tuple_sym,
)


def parse_seeds_list(raw: str) -> List[int]:
    return [int(x) for x in raw.replace(",", " ").split() if x.strip()]


def load_long_csv(path: Path) -> Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]]:
    stats: Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tr = int(row["train_seed"])
                ev = int(row["eval_seed"])
            except (ValueError, KeyError):
                continue
            t = row.get("tuple", "").replace("NT", "")
            s = row.get("sym", "")
            mean_s = row.get("mean", "")
            sd_s = row.get("sd", "")
            n_s = row.get("n_games", "0")
            mean = float(mean_s) if mean_s else None
            sd = float(sd_s) if sd_s else None
            try:
                n = int(n_s)
            except ValueError:
                n = 0
            stats[(tr, ev, t, s)] = (mean, sd, n)
    return stats


def collect_matrix(
    stats: Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]],
    train_seeds: List[int],
    eval_seeds: List[int],
    tuple_id: str,
    sym: str,
) -> List[List[Optional[float]]]:
    mat: List[List[Optional[float]]] = []
    for tr in train_seeds:
        row: List[Optional[float]] = []
        for ev in eval_seeds:
            mean, _sd, _n = stats.get((tr, ev, tuple_id, sym), (None, None, 0))
            row.append(mean)
        mat.append(row)
    return mat


def matrix_minmax(mat: List[List[Optional[float]]]) -> Tuple[Optional[float], Optional[float]]:
    vals = [v for row in mat for v in row if v is not None]
    if not vals:
        return None, None
    return min(vals), max(vals)


def plot_heatmap(
    mat: List[List[Optional[float]]],
    train_seeds: List[int],
    eval_seeds: List[int],
    title: str,
    out_path: Path,
    cmap: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> bool:
    vals = [[0.0 if v is None else v for v in row] for row in mat]
    if all(v == 0.0 for row in vals for v in row):
        return False
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(vals, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(eval_seeds)))
    ax.set_xticklabels(eval_seeds, rotation=45)
    ax.set_yticks(range(len(train_seeds)))
    ax.set_yticklabels(train_seeds)
    ax.set_xlabel("eval_seed")
    ax.set_ylabel("train_seed")
    if title:
        ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.8)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def plot_scatter(
    xs: List[float],
    ys: List[float],
    title: str,
    x_label: str,
    y_label: str,
    out_path: Path,
) -> bool:
    if not xs or not ys:
        return False
    lo = min(xs + ys)
    hi = max(xs + ys)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(xs, ys, s=18, alpha=0.7)
    ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def plot_delta_box(
    deltas_by_tuple: Dict[str, List[float]],
    title: str,
    out_path: Path,
) -> bool:
    labels = []
    data = []
    for t in sorted(deltas_by_tuple.keys(), key=lambda x: int(x)):
        vals = deltas_by_tuple[t]
        if vals:
            labels.append(f"NT{t}")
            data.append(vals)
    if not data:
        return False
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(data, labels=labels, showfliers=False)
    ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_ylabel("sym - notsym")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def plot_delta_bar_by_nt(
    tuples: List[str],
    deltas_by_tuple: Dict[str, List[float]],
    title: str,
    out_path: Path,
) -> bool:
    labels: List[str] = []
    means: List[float] = []
    sds: List[float] = []
    for t in sorted(tuples, key=lambda x: int(x)):
        vals = deltas_by_tuple.get(t, [])
        if not vals:
            continue
        labels.append(f"NT{t}")
        mean = sum(vals) / len(vals)
        if len(vals) > 1:
            var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
            sd = math.sqrt(var)
        else:
            sd = 0.0
        means.append(mean)
        sds.append(sd)
    if not means:
        return False
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, means, yerr=sds, capsize=4, alpha=0.8)
    ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_ylabel("sym - notsym (eval-avg, per train_seed)")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    p = argparse.ArgumentParser(
        description="train_seed×eval_seed のスコアから可視化図を作成"
    )
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root",
    )
    p.add_argument("--train-seed-start", type=int, default=None)
    p.add_argument("--train-seed-end", type=int, default=None)
    p.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    p.add_argument("--eval-seed-start", type=int, default=None)
    p.add_argument("--eval-seed-end", type=int, default=None)
    p.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    p.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    p.add_argument("--sym-list", default="", help="comma-separated sym list (default: auto)")
    p.add_argument("--input-long", default="", help="long-format CSV path")
    p.add_argument(
        "--out-dir",
        default="",
        help="output dir for primary images (default: analysis_outputs/<run_name>/train_eval_plots)",
    )
    p.add_argument("--ext", default="png", help="primary output extension (default: png)")
    p.add_argument(
        "--pdf",
        action="store_true",
        help="also write PDF outputs into a separate directory",
    )
    p.add_argument(
        "--pdf-out-dir",
        default="",
        help="output dir for PDF images (default: <out-dir>_pdf)",
    )
    p.add_argument("--heatmap", action="store_true")
    p.add_argument("--diff-heatmap", action="store_true")
    p.add_argument("--scatter", action="store_true")
    p.add_argument("--delta-box", action="store_true")
    p.add_argument(
        "--delta-nt",
        action="store_true",
        help="sym-notsym差分をeval_seed平均後にtrain_seedごとに計算し、NT別の平均±SDを棒グラフで出力",
    )
    p.add_argument("--no-title", action="store_true", help="omit titles in plots")
    p.add_argument("--all", action="store_true", help="generate all plots")
    args = p.parse_args()

    if not (
        args.heatmap
        or args.diff_heatmap
        or args.scatter
        or args.delta_box
        or args.delta_nt
        or args.all
    ):
        raise SystemExit(
            "ERROR: no plot type specified. Use --heatmap/--diff-heatmap/--scatter/--delta-box/--delta-nt or --all."
        )

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    # seeds
    if args.train_seeds:
        train_seeds = parse_seeds_list(args.train_seeds)
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)
    if args.eval_seeds:
        eval_seeds = parse_seeds_list(args.eval_seeds)
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds = list_eval_seeds(run_dir) or train_seeds

    # tuples/syms
    if args.tuples:
        tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    else:
        tuples, _syms = list_tuple_sym(run_dir)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    else:
        _tuples, syms = list_tuple_sym(run_dir)

    # stats
    stats: Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]]
    if args.input_long:
        stats = load_long_csv(Path(args.input_long))
    else:
        _rows, _cols, stats = build_rows(run_dir, train_seeds, eval_seeds, tuples, syms, False)

    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "train_eval_plots"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf_out_dir: Optional[Path] = None
    if args.pdf or args.pdf_out_dir:
        if args.pdf_out_dir:
            pdf_out_dir = Path(args.pdf_out_dir)
        else:
            pdf_out_dir = out_dir.parent / f"{out_dir.name}_pdf"
        pdf_out_dir.mkdir(parents=True, exist_ok=True)

    def iter_outputs(stem: str) -> List[Path]:
        outputs = [out_dir / f"{stem}.{args.ext}"]
        if pdf_out_dir:
            outputs.append(pdf_out_dir / f"{stem}.pdf")
        return outputs

    # heatmaps
    if args.all or args.heatmap:
        for t in tuples:
            for s in syms:
                mat = collect_matrix(stats, train_seeds, eval_seeds, t, s)
                vmin, vmax = matrix_minmax(mat)
                title = "" if args.no_title else f"{args.run_name} NT{t}_{s} mean score"
                for out_path in iter_outputs(f"train_eval_heatmap_NT{t}_{s}"):
                    if plot_heatmap(
                        mat,
                        train_seeds,
                        eval_seeds,
                        title,
                        out_path,
                        vmin=vmin,
                        vmax=vmax,
                    ):
                        print(f"saved: {out_path}")
                    else:
                        print(f"skip (no data): {out_path}")

    # diff heatmap (sym - notsym)
    if (args.all or args.diff_heatmap) and ("sym" in syms and "notsym" in syms):
        for t in tuples:
            mat_sym = collect_matrix(stats, train_seeds, eval_seeds, t, "sym")
            mat_ns = collect_matrix(stats, train_seeds, eval_seeds, t, "notsym")
            diff: List[List[Optional[float]]] = []
            for r in range(len(train_seeds)):
                row: List[Optional[float]] = []
                for c in range(len(eval_seeds)):
                    a = mat_sym[r][c]
                    b = mat_ns[r][c]
                    row.append((a - b) if (a is not None and b is not None) else None)
                diff.append(row)
            vals = [v for row in diff for v in row if v is not None]
            if not vals:
                print(f"skip (no data): diff heatmap NT{t}")
                continue
            max_abs = max(abs(v) for v in vals)
            title = "" if args.no_title else f"{args.run_name} NT{t} (sym - notsym)"
            for out_path in iter_outputs(f"train_eval_diff_heatmap_NT{t}_sym_minus_notsym"):
                if plot_heatmap(
                    diff,
                    train_seeds,
                    eval_seeds,
                    title,
                    out_path,
                    cmap="coolwarm",
                    vmin=-max_abs,
                    vmax=max_abs,
                ):
                    print(f"saved: {out_path}")

    # scatter (sym vs notsym)
    if (args.all or args.scatter) and ("sym" in syms and "notsym" in syms):
        for t in tuples:
            xs: List[float] = []
            ys: List[float] = []
            for tr in train_seeds:
                for ev in eval_seeds:
                    s_mean, _sd, _n = stats.get((tr, ev, t, "sym"), (None, None, 0))
                    n_mean, _sd2, _n2 = stats.get((tr, ev, t, "notsym"), (None, None, 0))
                    if s_mean is None or n_mean is None:
                        continue
                    xs.append(n_mean)
                    ys.append(s_mean)
            title = "" if args.no_title else f"{args.run_name} NT{t} sym vs notsym"
            for out_path in iter_outputs(f"train_eval_scatter_sym_vs_notsym_NT{t}"):
                if plot_scatter(xs, ys, title, "notsym mean", "sym mean", out_path):
                    print(f"saved: {out_path}")
                else:
                    print(f"skip (no data): {out_path}")

    # delta box
    if (args.all or args.delta_box) and ("sym" in syms and "notsym" in syms):
        deltas: Dict[str, List[float]] = {t: [] for t in tuples}
        for t in tuples:
            for tr in train_seeds:
                for ev in eval_seeds:
                    s_mean, _sd, _n = stats.get((tr, ev, t, "sym"), (None, None, 0))
                    n_mean, _sd2, _n2 = stats.get((tr, ev, t, "notsym"), (None, None, 0))
                    if s_mean is None or n_mean is None:
                        continue
                    deltas[t].append(s_mean - n_mean)
        title = "" if args.no_title else f"{args.run_name} sym - notsym (all train/eval)"
        for out_path in iter_outputs("train_eval_delta_box_sym_minus_notsym"):
            if plot_delta_box(deltas, title, out_path):
                print(f"saved: {out_path}")
            else:
                print(f"skip (no data): {out_path}")

    # delta bar by NT (eval_seed平均 -> train_seed差分)
    if (args.all or args.delta_nt) and ("sym" in syms and "notsym" in syms):
        deltas_by_nt: Dict[str, List[float]] = {t: [] for t in tuples}
        for t in tuples:
            for tr in train_seeds:
                sym_vals: List[float] = []
                ns_vals: List[float] = []
                for ev in eval_seeds:
                    s_mean, _sd, _n = stats.get((tr, ev, t, "sym"), (None, None, 0))
                    n_mean, _sd2, _n2 = stats.get((tr, ev, t, "notsym"), (None, None, 0))
                    if s_mean is not None:
                        sym_vals.append(s_mean)
                    if n_mean is not None:
                        ns_vals.append(n_mean)
                if not sym_vals or not ns_vals:
                    continue
                sym_avg = sum(sym_vals) / len(sym_vals)
                ns_avg = sum(ns_vals) / len(ns_vals)
                deltas_by_nt[t].append(sym_avg - ns_avg)
        title = "" if args.no_title else f"{args.run_name} sym - notsym (eval-avg, by train_seed)"
        for out_path in iter_outputs("train_eval_delta_bar_by_nt"):
            if plot_delta_bar_by_nt(tuples, deltas_by_nt, title, out_path):
                print(f"saved: {out_path}")
            else:
                print(f"skip (no data): {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

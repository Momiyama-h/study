#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean_sd(vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not vals:
        return None, None
    mean = sum(vals) / len(vals)
    if len(vals) >= 2:
        var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
        sd = math.sqrt(max(var, 0.0))
    else:
        sd = 0.0
    return mean, sd


def load_reach_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_quant_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def aggregate_reach(
    rows: List[Dict[str, str]]
) -> Tuple[List[str], List[str], Dict[Tuple[str, str], Tuple[Optional[float], Optional[float]]]]:
    tuples: List[str] = []
    syms: List[str] = []
    per_train: Dict[Tuple[str, str, str], List[float]] = {}
    for r in rows:
        t = r.get("tuple", "").replace("NT", "")
        s = r.get("sym", "")
        tr = r.get("train_seed", "")
        p = parse_float(r.get("p_reach", ""))
        if not t or not s or not tr or p is None:
            continue
        if t not in tuples:
            tuples.append(t)
        if s not in syms:
            syms.append(s)
        key = (tr, t, s)
        per_train.setdefault(key, []).append(p)

    # eval_seed平均 → train_seed差分の統計
    by_tuple_sym: Dict[Tuple[str, str], List[float]] = {}
    for (tr, t, s), vals in per_train.items():
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        by_tuple_sym.setdefault((t, s), []).append(mean)

    stats: Dict[Tuple[str, str], Tuple[Optional[float], Optional[float]]] = {}
    for (t, s), vals in by_tuple_sym.items():
        stats[(t, s)] = mean_sd(vals)

    tuples_sorted = sorted(tuples, key=lambda x: int(x))
    syms_sorted = sorted(syms)
    return tuples_sorted, syms_sorted, stats


def aggregate_quantiles(
    rows: List[Dict[str, str]]
) -> Tuple[List[str], List[str], Dict[Tuple[str, str, str], Optional[float]]]:
    tuples: List[str] = []
    syms: List[str] = []
    per_train: Dict[Tuple[str, str, str], Dict[str, List[float]]] = {}
    for r in rows:
        t = r.get("tuple", "").replace("NT", "")
        s = r.get("sym", "")
        tr = r.get("train_seed", "")
        if not t or not s or not tr:
            continue
        if t not in tuples:
            tuples.append(t)
        if s not in syms:
            syms.append(s)
        for q in ("p25", "median", "p75", "p90"):
            v = parse_float(r.get(q, ""))
            if v is None:
                continue
            per_train.setdefault((tr, t, s), {}).setdefault(q, []).append(v)

    # eval_seed平均 → train_seed平均
    by_tuple_sym: Dict[Tuple[str, str, str], List[float]] = {}
    for (tr, t, s), qmap in per_train.items():
        for q, vals in qmap.items():
            if not vals:
                continue
            mean = sum(vals) / len(vals)
            by_tuple_sym.setdefault((t, s, q), []).append(mean)

    stats: Dict[Tuple[str, str, str], Optional[float]] = {}
    for (t, s, q), vals in by_tuple_sym.items():
        mean, _sd = mean_sd(vals)
        stats[(t, s, q)] = mean

    tuples_sorted = sorted(tuples, key=lambda x: int(x))
    syms_sorted = sorted(syms)
    return tuples_sorted, syms_sorted, stats


def plot_reach_bar(
    tuples: List[str],
    syms: List[str],
    stats: Dict[Tuple[str, str], Tuple[Optional[float], Optional[float]]],
    title: str,
    out_path: Path,
    combine_sym: bool,
) -> bool:
    if not tuples or not syms:
        return False
    color_map = {"sym": "#1f77b4", "notsym": "#ff7f0e"}
    fig, ax = plt.subplots(figsize=(7, 4))
    x = list(range(len(tuples)))
    if combine_sym:
        width = 0.8 / max(len(syms), 1)
        offsets = [(-0.4 + width / 2) + i * width for i in range(len(syms))]
        for i, s in enumerate(syms):
            means: List[float] = []
            sds: List[float] = []
            for t in tuples:
                mean, sd = stats.get((t, s), (None, None))
                means.append(mean if mean is not None else 0.0)
                sds.append(sd if sd is not None else 0.0)
            ax.bar(
                [xi + offsets[i] for xi in x],
                means,
                width=width,
                yerr=sds,
                capsize=3,
                alpha=0.8,
                label=s,
                color=color_map.get(s),
            )
        ax.legend()
    else:
        # single sym (caller passes one sym at a time)
        s = syms[0]
        means = []
        sds = []
        for t in tuples:
            mean, sd = stats.get((t, s), (None, None))
            means.append(mean if mean is not None else 0.0)
            sds.append(sd if sd is not None else 0.0)
        ax.bar(x, means, yerr=sds, capsize=3, alpha=0.8, label=s, color=color_map.get(s))
    ax.set_xticks(x)
    ax.set_xticklabels([f"NT{t}" for t in tuples])
    ax.set_ylabel("reach probability")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def plot_quant_lines(
    tuples: List[str],
    sym: str,
    stats: Dict[Tuple[str, str, str], Optional[float]],
    title: str,
    out_path: Path,
) -> bool:
    if not tuples:
        return False
    x = list(range(len(tuples)))
    fig, ax = plt.subplots(figsize=(7, 4))
    series = [
        ("p25", "p25", "s", "--", -0.06),
        ("median", "median", "o", "-", 0.0),
        ("p75", "p75", "^", ":", 0.03),
        ("p90", "p90", "D", "-.", 0.06),
    ]
    for q, label, marker, linestyle, offset in series:
        ys: List[float] = []
        for t in tuples:
            v = stats.get((t, sym, q))
            ys.append(v if v is not None else float("nan"))
        if all(math.isnan(v) for v in ys):
            continue
        xs = [xi + offset for xi in x]
        ax.plot(xs, ys, marker=marker, linestyle=linestyle, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([f"NT{t}" for t in tuples])
    ax.set_ylabel("max tile exponent")
    if title:
        ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    p = argparse.ArgumentParser(description="tile_stats のCSVから到達率/分位の図を作成")
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--tile-stats-dir",
        default="",
        help="tile_stats dir (default: analysis_outputs_v2/<run_name>/tile_stats)",
    )
    p.add_argument(
        "--out-dir",
        default="",
        help="output dir (default: analysis_outputs_v2/<run_name>/tile_stats_plots)",
    )
    p.add_argument("--reach-exp", type=int, default=9, help="reach exponent k (2^k)")
    p.add_argument("--ext", default="png", help="primary output extension (default: png)")
    p.add_argument("--pdf", action="store_true", help="also write PDF outputs")
    p.add_argument("--pdf-out-dir", default="", help="PDF output dir (default: <out-dir>_pdf)")
    p.add_argument("--combine-sym", action="store_true", help="combine sym/notsym into one reach bar plot")
    p.add_argument("--no-title", action="store_true", help="omit titles in plots")
    args = p.parse_args()

    base_dir = (
        Path(args.tile_stats_dir)
        if args.tile_stats_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "tile_stats"
    )
    reach_csv = base_dir / "reach_prob" / f"tile_reach_prob_2pow{args.reach_exp}.csv"
    quant_csv = base_dir / "quantiles" / "tile_max_exp_quantiles.csv"
    if not reach_csv.exists() or not quant_csv.exists():
        raise SystemExit(f"ERROR: tile_stats CSV not found in {base_dir}")

    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "tile_stats_plots"
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
        outs = [out_dir / f"{stem}.{args.ext}"]
        if pdf_out_dir:
            outs.append(pdf_out_dir / f"{stem}.pdf")
        return outs

    reach_rows = load_reach_csv(reach_csv)
    tuples, syms, reach_stats = aggregate_reach(reach_rows)
    title = "" if args.no_title else f"{args.run_name} reach prob (2^{args.reach_exp})"
    if args.combine_sym:
        for out_path in iter_outputs(f"tile_reach_bar_2pow{args.reach_exp}"):
            if plot_reach_bar(tuples, syms, reach_stats, title, out_path, True):
                print(f"saved: {out_path}")
            else:
                print(f"skip (no data): {out_path}")
    else:
        for s in syms:
            for out_path in iter_outputs(f"tile_reach_bar_2pow{args.reach_exp}_{s}"):
                if plot_reach_bar(tuples, [s], reach_stats, title, out_path, False):
                    print(f"saved: {out_path}")
                else:
                    print(f"skip (no data): {out_path}")

    quant_rows = load_quant_csv(quant_csv)
    tuples_q, syms_q, quant_stats = aggregate_quantiles(quant_rows)
    for s in syms_q:
        q_title = "" if args.no_title else f"{args.run_name} max tile exp (NT, {s})"
        for out_path in iter_outputs(f"tile_max_exp_quantiles_{s}"):
            if plot_quant_lines(tuples_q, s, quant_stats, q_title, out_path):
                print(f"saved: {out_path}")
            else:
                print(f"skip (no data): {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

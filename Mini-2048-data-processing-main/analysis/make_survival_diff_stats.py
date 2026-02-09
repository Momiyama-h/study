#!/usr/bin/env python3
import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")
PROGRESS_RE = re.compile(r"progress:\s*(\d+)")


def parse_seed_dir(name: str) -> Optional[int]:
    if not name.startswith("seed"):
        return None
    try:
        return int(name[4:])
    except ValueError:
        return None


def parse_eval_seed_dir(name: str) -> Optional[int]:
    if not name.startswith("eval_seed"):
        return None
    try:
        return int(name[9:])
    except ValueError:
        return None


def list_train_seeds(run_dir: Path) -> List[int]:
    seeds: List[int] = []
    for p in run_dir.glob("seed*"):
        if p.is_dir():
            s = parse_seed_dir(p.name)
            if s is not None:
                seeds.append(s)
    return sorted(seeds)


def list_eval_seeds(run_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in run_dir.glob("seed*/NT*_*/*"):
        if not p.is_dir():
            continue
        es = parse_eval_seed_dir(p.name)
        if es is not None and es not in evals:
            evals.append(es)
    return sorted(evals)


def list_tuple_sym(run_dir: Path) -> Tuple[List[str], List[str]]:
    tuples: List[str] = []
    syms: List[str] = []
    for nt_dir in run_dir.glob("seed*/NT*_*"):
        if not nt_dir.is_dir():
            continue
        m = NT_DIR_RE.match(nt_dir.name)
        if not m:
            continue
        t = m.group("tuple")
        s = m.group("sym")
        if t not in tuples:
            tuples.append(t)
        if s not in syms:
            syms.append(s)
    return sorted(tuples, key=lambda x: int(x)), sorted(syms)


def parse_progresses(state_path: Path) -> List[int]:
    progresses: List[int] = []
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            if "progress:" not in line:
                continue
            m = PROGRESS_RE.search(line)
            if m:
                progresses.append(int(m.group(1)))
    return progresses


def survival_curve(progresses: List[int], max_progress: Optional[int]) -> Optional[List[float]]:
    if not progresses:
        return None
    droped_counter = Counter(progresses)
    max_value = len(progresses)
    if max_progress is None:
        max_p = max(progresses) + 10
    else:
        max_p = max_progress
    survival_rate: List[float] = []
    for i in range(max_p + 1):
        max_value -= droped_counter.get(i, 0)
        survival_rate.append(max_value / len(progresses))
    return survival_rate


def mean_curve(curves: List[List[float]]) -> Optional[np.ndarray]:
    if not curves:
        return None
    min_len = min(len(c) for c in curves)
    if min_len == 0:
        return None
    arr = np.array([c[:min_len] for c in curves], dtype=float)
    return arr.mean(axis=0)


def bh_adjust(pvals: List[Optional[float]]) -> List[Optional[float]]:
    valid = [(i, p) for i, p in enumerate(pvals) if p is not None]
    if not valid:
        return [None for _ in pvals]
    order = sorted(valid, key=lambda x: x[1])
    n = len(order)
    adj = [None for _ in pvals]
    prev = 1.0
    for rank, (idx, p) in enumerate(reversed(order), start=1):
        r = n - rank + 1
        val = p * n / r
        prev = min(prev, val)
        adj[idx] = prev
    return adj


def signflip_pvals(deltas: np.ndarray, n_perm: int, rng: np.random.Generator) -> List[Optional[float]]:
    # deltas: shape (n_train, n_progress)
    n_train, n_prog = deltas.shape
    if n_train < 2:
        return [None] * n_prog
    obs = deltas.mean(axis=0)
    # sign-flip permutations
    if n_perm <= 0:
        n_perm = 2000
    signs = rng.choice([-1.0, 1.0], size=(n_perm, n_train))
    means = (signs @ deltas) / n_train
    p = (np.abs(means) >= np.abs(obs)).mean(axis=0)
    return [float(x) for x in p]


def bootstrap_ci(deltas: np.ndarray, n_boot: int, alpha: float, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    n_train, n_prog = deltas.shape
    if n_train == 0:
        return np.array([]), np.array([])
    if n_boot <= 0:
        n_boot = 1000
    idx = rng.integers(0, n_train, size=(n_boot, n_train))
    boot_means = deltas[idx].mean(axis=1)
    low = np.quantile(boot_means, alpha / 2, axis=0)
    high = np.quantile(boot_means, 1 - alpha / 2, axis=0)
    return low, high


def main() -> int:
    p = argparse.ArgumentParser(
        description="sym vs notsym の生存率差（progressごと）を seed 構造に沿って評価し、CSV/図を出力"
    )
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root (v2 default)",
    )
    p.add_argument("--train-seed-start", type=int, default=None)
    p.add_argument("--train-seed-end", type=int, default=None)
    p.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    p.add_argument("--eval-seed-start", type=int, default=None)
    p.add_argument("--eval-seed-end", type=int, default=None)
    p.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    p.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    p.add_argument("--sym-list", default="sym,notsym", help="comma-separated sym list")
    p.add_argument("--max-progress", type=int, default=None, help="max progress to compute (default: max+10)")
    p.add_argument("--n-bootstrap", type=int, default=1000)
    p.add_argument("--n-perm", type=int, default=2000)
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--fdr", action="store_true", help="BH-FDR adjust p-values")
    p.add_argument("--no-title", action="store_true", help="plots without title")
    p.add_argument("--ext", default="png", help="plot extension (png/pdf)")
    p.add_argument("--pdf", action="store_true", help="also output pdf")
    p.add_argument("--pdf-out-dir", default="", help="pdf output dir (optional)")
    p.add_argument("--out-dir", default="", help="output dir (default: analysis_outputs_v2/<run>/surv_diff_stats)")
    args = p.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    # seeds
    train_seeds: List[int] = []
    if args.train_seeds:
        train_seeds = [int(x) for x in args.train_seeds.replace(",", " ").split() if x.strip()]
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    eval_seeds: List[int] = []
    if args.eval_seeds:
        eval_seeds = [int(x) for x in args.eval_seeds.replace(",", " ").split() if x.strip()]
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds = list_eval_seeds(run_dir)

    tuples: List[str] = []
    syms: List[str] = []
    if args.tuples:
        tuples = [t for t in args.tuples.split(",") if t]
    if args.sym_list:
        syms = [s for s in args.sym_list.split(",") if s]
    if not tuples or not syms:
        auto_tuples, auto_syms = list_tuple_sym(run_dir)
        if not tuples:
            tuples = auto_tuples
        if not syms:
            syms = auto_syms

    if "sym" not in syms or "notsym" not in syms:
        raise SystemExit("ERROR: sym-list must include both sym and notsym")

    out_dir = Path(args.out_dir) if args.out_dir else Path("/HDD/momiyama2/data/study/analysis_outputs_v2") / args.run_name / "surv_diff_stats"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(0)

    # curves[tuple][train_seed][sym] -> list of curves (per eval_seed)
    curves: Dict[str, Dict[int, Dict[str, List[List[float]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for tr in train_seeds:
        for ev in eval_seeds:
            for t in tuples:
                for s in ("sym", "notsym"):
                    state = run_dir / f"seed{tr}" / f"NT{t}_{s}" / f"eval_seed{ev}" / "state.txt"
                    if not state.exists():
                        state = run_dir / f"seed{tr}" / f"NT{t}_{s}" / "state.txt"
                    if not state.exists():
                        continue
                    progresses = parse_progresses(state)
                    curve = survival_curve(progresses, args.max_progress)
                    if curve is None:
                        continue
                    curves[t][tr][s].append(curve)

    # per-train_seed mean curves and deltas
    per_train_rows: List[Dict[str, str]] = []
    summary_rows: List[Dict[str, str]] = []
    auc_rows: List[Dict[str, str]] = []

    for t in tuples:
        delta_curves: List[np.ndarray] = []
        train_ids: List[int] = []
        # collect per-train outputs
        for tr in train_seeds:
            sym_curves = curves[t][tr].get("sym", [])
            not_curves = curves[t][tr].get("notsym", [])
            sym_mean = mean_curve(sym_curves)
            not_mean = mean_curve(not_curves)
            if sym_mean is None or not_mean is None:
                continue
            min_len = min(len(sym_mean), len(not_mean))
            sym_mean = sym_mean[:min_len]
            not_mean = not_mean[:min_len]
            delta = sym_mean - not_mean
            delta_curves.append(delta)
            train_ids.append(tr)
            # write per-train rows
            n_eval = min(len(sym_curves), len(not_curves))
            for prg, d in enumerate(delta.tolist()):
                per_train_rows.append({
                    "train_seed": str(tr),
                    "tuple": f"NT{t}",
                    "progress": str(prg),
                    "delta": f"{d:.6f}",
                    "sym_mean": f"{sym_mean[prg]:.6f}",
                    "notsym_mean": f"{not_mean[prg]:.6f}",
                    "n_eval": str(n_eval),
                })

        if not delta_curves:
            continue

        arr = np.array(delta_curves, dtype=float)
        n_train, n_prog = arr.shape
        mean = arr.mean(axis=0)
        if n_train >= 2:
            sd = arr.std(axis=0, ddof=1)
        else:
            sd = np.zeros_like(mean)
        ci_low, ci_high = bootstrap_ci(arr, args.n_bootstrap, args.alpha, rng)
        pvals = signflip_pvals(arr, args.n_perm, rng)
        p_adj = bh_adjust(pvals) if args.fdr else [None for _ in pvals]

        for prg in range(n_prog):
            summary_rows.append({
                "tuple": f"NT{t}",
                "progress": str(prg),
                "n_train": str(n_train),
                "mean_delta": f"{mean[prg]:.6f}",
                "sd_delta": f"{sd[prg]:.6f}",
                "ci_low": f"{ci_low[prg]:.6f}" if len(ci_low) else "",
                "ci_high": f"{ci_high[prg]:.6f}" if len(ci_high) else "",
                "p_value": f"{pvals[prg]:.6f}" if pvals[prg] is not None else "",
                "p_fdr": f"{p_adj[prg]:.6f}" if p_adj[prg] is not None else "",
            })

        # AUC summary per train_seed
        aucs = arr.sum(axis=1)
        auc_mean = float(np.mean(aucs))
        auc_sd = float(np.std(aucs, ddof=1)) if n_train >= 2 else 0.0
        # bootstrap CI for AUC
        if args.n_bootstrap > 0 and n_train > 0:
            idx = rng.integers(0, n_train, size=(args.n_bootstrap, n_train))
            boot = aucs[idx].mean(axis=1)
            auc_ci_low = float(np.quantile(boot, args.alpha / 2))
            auc_ci_high = float(np.quantile(boot, 1 - args.alpha / 2))
        else:
            auc_ci_low, auc_ci_high = float("nan"), float("nan")
        # sign-flip p-value for AUC
        if n_train >= 2:
            signs = rng.choice([-1.0, 1.0], size=(max(args.n_perm, 2000), n_train))
            means = (signs @ aucs) / n_train
            auc_p = float((np.abs(means) >= abs(auc_mean)).mean())
        else:
            auc_p = None
        auc_rows.append({
            "tuple": f"NT{t}",
            "n_train": str(n_train),
            "auc_mean": f"{auc_mean:.6f}",
            "auc_sd": f"{auc_sd:.6f}",
            "auc_ci_low": f"{auc_ci_low:.6f}",
            "auc_ci_high": f"{auc_ci_high:.6f}",
            "p_value": f"{auc_p:.6f}" if auc_p is not None else "",
        })

        # plots per tuple
        ext = args.ext.lstrip('.')
        fig, ax = plt.subplots(figsize=(7, 4))
        xs = np.arange(n_prog)
        ax.plot(xs, mean, label="sym - notsym")
        if len(ci_low) and len(ci_high):
            ax.fill_between(xs, ci_low, ci_high, alpha=0.2)
        ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
        ax.set_xlabel("progress")
        ax.set_ylabel("survival diff")
        if not args.no_title:
            ax.set_title(f"NT{t} survival diff (sym - notsym)")
        fig.tight_layout()
        out_path = out_dir / f"surv_diff_curve_NT{t}.{ext}"
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        if args.pdf:
            pdf_dir = Path(args.pdf_out_dir) if args.pdf_out_dir else out_dir
            pdf_dir.mkdir(parents=True, exist_ok=True)
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(xs, mean, label="sym - notsym")
            if len(ci_low) and len(ci_high):
                ax.fill_between(xs, ci_low, ci_high, alpha=0.2)
            ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
            ax.set_xlabel("progress")
            ax.set_ylabel("survival diff")
            if not args.no_title:
                ax.set_title(f"NT{t} survival diff (sym - notsym)")
            fig.tight_layout()
            fig.savefig(pdf_dir / f"surv_diff_curve_NT{t}.pdf", bbox_inches="tight")
            plt.close(fig)

        # AUC bar plot
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.bar([0], [auc_mean], yerr=[auc_sd], capsize=4, alpha=0.8)
        ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
        ax.set_xticks([0])
        ax.set_xticklabels([f"NT{t}"])
        ax.set_ylabel("AUC (sym - notsym)")
        if not args.no_title:
            ax.set_title(f"NT{t} survival diff AUC")
        fig.tight_layout()
        fig.savefig(out_dir / f"surv_diff_auc_NT{t}.{ext}", dpi=200, bbox_inches="tight")
        plt.close(fig)
        if args.pdf:
            pdf_dir = Path(args.pdf_out_dir) if args.pdf_out_dir else out_dir
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.bar([0], [auc_mean], yerr=[auc_sd], capsize=4, alpha=0.8)
            ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
            ax.set_xticks([0])
            ax.set_xticklabels([f"NT{t}"])
            ax.set_ylabel("AUC (sym - notsym)")
            if not args.no_title:
                ax.set_title(f"NT{t} survival diff AUC")
            fig.tight_layout()
            fig.savefig(pdf_dir / f"surv_diff_auc_NT{t}.pdf", bbox_inches="tight")
            plt.close(fig)

    # write CSVs
    per_train_path = out_dir / "surv_diff_by_train_seed_long.csv"
    with per_train_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "train_seed", "tuple", "progress", "delta", "sym_mean", "notsym_mean", "n_eval"
        ])
        writer.writeheader()
        writer.writerows(per_train_rows)

    summary_path = out_dir / "surv_diff_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "tuple", "progress", "n_train", "mean_delta", "sd_delta", "ci_low", "ci_high", "p_value", "p_fdr"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)

    auc_path = out_dir / "surv_diff_auc.csv"
    with auc_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "tuple", "n_train", "auc_mean", "auc_sd", "auc_ci_low", "auc_ci_high", "p_value"
        ])
        writer.writeheader()
        writer.writerows(auc_rows)

    print(f"saved: {per_train_path}")
    print(f"saved: {summary_path}")
    print(f"saved: {auc_path}")
    print(f"plots: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

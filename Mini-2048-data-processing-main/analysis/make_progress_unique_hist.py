#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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


def list_tuple_sym(run_dir: Path) -> Tuple[List[str], List[str]]:
    tuples: List[str] = []
    syms: List[str] = []
    for nt_dir in run_dir.glob("seed*/NT*_*"):
        if not nt_dir.is_dir():
            continue
        parts = nt_dir.name.split("_", 1)
        if len(parts) != 2:
            continue
        t = parts[0].replace("NT", "")
        s = parts[1]
        if t not in tuples:
            tuples.append(t)
        if s not in syms:
            syms.append(s)
    return sorted(tuples, key=lambda x: int(x)), sorted(syms)


def list_eval_seeds_for_nt(nt_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in nt_dir.glob("eval_seed*"):
        if not p.is_dir():
            continue
        es = parse_eval_seed_dir(p.name)
        if es is not None:
            evals.append(es)
    return sorted(evals)


def iter_state_boards(state_path: Path):
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn"):
                continue
            vals = line.split()
            if len(vals) != 9:
                continue
            try:
                yield tuple(int(v) for v in vals)
            except ValueError:
                continue


def iter_eval_progress(eval_path: Path):
    with eval_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("game"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                prg = int(float(parts[4]))
            except ValueError:
                continue
            yield prg


def calc_unique_in_range(state_path: Path, eval_path: Path, pmin: int, pmax: int) -> Tuple[int, int]:
    uniq = set()
    total = 0
    for prg, board in zip(iter_eval_progress(eval_path), iter_state_boards(state_path)):
        if pmin <= prg <= pmax:
            total += 1
            uniq.add(board)
    return len(uniq), total


def mean_std(vals: List[float]) -> Tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / len(vals)
    return m, math.sqrt(var)


def calc_unique_bins(
    state_path: Path, eval_path: Path, pmin: int, pmax: int, bin_size: int
) -> Tuple[List[int], List[int]]:
    bins = (pmax - pmin) // bin_size + 1
    uniq_bins = [set() for _ in range(bins)]
    total_bins = [0 for _ in range(bins)]
    for prg, board in zip(iter_eval_progress(eval_path), iter_state_boards(state_path)):
        if prg < pmin or prg > pmax:
            continue
        idx = (prg - pmin) // bin_size
        total_bins[idx] += 1
        uniq_bins[idx].add(board)
    uniq_counts = [len(s) for s in uniq_bins]
    return uniq_counts, total_bins


def main() -> int:
    ap = argparse.ArgumentParser(
        description="progress範囲内のユニーク盤面数を集計し、sym/notsymでヒストグラム比較する"
    )
    ap.add_argument("--run-name", required=True)
    ap.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root (default: board_data_v2)",
    )
    ap.add_argument("--train-seed-start", type=int, default=None)
    ap.add_argument("--train-seed-end", type=int, default=None)
    ap.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    ap.add_argument("--eval-seed-start", type=int, default=None)
    ap.add_argument("--eval-seed-end", type=int, default=None)
    ap.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    ap.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    ap.add_argument("--sym-list", default="sym,notsym", help="comma-separated sym list")
    ap.add_argument("--progress-start", type=int, required=True)
    ap.add_argument("--progress-end", type=int, required=True)
    ap.add_argument("--bins", type=int, default=20)
    ap.add_argument("--use-ratio", action="store_true", help="plot unique_ratio instead of unique_count")
    ap.add_argument("--curve", action="store_true", help="output progress->unique_ratio curve (mean±sd)")
    ap.add_argument("--curve-bin", type=int, default=10, help="progress bin size for curve (default: 10)")
    ap.add_argument("--curve-no-sd", action="store_true", help="disable sd band for curve plots")
    ap.add_argument("--no-title", action="store_true")
    ap.add_argument("--ext", default="png", help="plot extension (png/pdf)")
    ap.add_argument("--pdf", action="store_true", help="also output pdf")
    ap.add_argument("--pdf-out-dir", default="", help="pdf output dir (optional)")
    ap.add_argument("--out-dir", default="", help="output dir (default: analysis_outputs_v2/<run>/progress_unique_hist)")
    args = ap.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    if args.train_seeds:
        raw = args.train_seeds.replace(",", " ").split()
        train_seeds = [int(x) for x in raw if x.strip()]
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    if args.eval_seeds:
        raw = args.eval_seeds.replace(",", " ").split()
        eval_seeds_fixed = [int(x) for x in raw if x.strip()]
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds_fixed = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds_fixed = None

    if args.tuples:
        tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    else:
        tuples, _ = list_tuple_sym(run_dir)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    else:
        _, syms = list_tuple_sym(run_dir)

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_root = Path("/HDD/momiyama2/data/study/analysis_outputs")
        if str(board_root).endswith("board_data_v2"):
            out_root = Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        out_dir = out_root / args.run_name / "progress_unique_hist"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, str]] = []
    values: Dict[Tuple[str, str], List[int]] = {}
    curve_values: Dict[Tuple[str, str, int], List[float]] = {}

    pmin, pmax = args.progress_start, args.progress_end
    curve_bin = max(1, args.curve_bin)
    curve_bins = (pmax - pmin) // curve_bin + 1 if args.curve else 0
    for tr in train_seeds:
        for t in tuples:
            for s in syms:
                nt_dir = run_dir / f"seed{tr}" / f"NT{t}_{s}"
                if not nt_dir.exists():
                    continue
                if eval_seeds_fixed is not None:
                    eval_seeds = eval_seeds_fixed
                else:
                    eval_seeds = list_eval_seeds_for_nt(nt_dir)
                    if not eval_seeds:
                        eval_seeds = [None]
                for ev in eval_seeds:
                    if ev is None:
                        state = nt_dir / "state.txt"
                        eval_file = nt_dir / "eval.txt"
                    else:
                        state = nt_dir / f"eval_seed{ev}" / "state.txt"
                        eval_file = nt_dir / f"eval_seed{ev}" / "eval.txt"
                    if not state.exists() or not eval_file.exists():
                        continue
                    uniq, total = calc_unique_in_range(state, eval_file, pmin, pmax)
                    ratio = (uniq / total) if total > 0 else 0.0
                    rows.append({
                        "train_seed": str(tr),
                        "eval_seed": "" if ev is None else str(ev),
                        "tuple": f"NT{t}",
                        "sym": s,
                        "progress_start": str(pmin),
                        "progress_end": str(pmax),
                        "unique_count": str(uniq),
                        "total_states": str(total),
                        "unique_ratio": f"{ratio:.6f}",
                    })
                    values.setdefault((t, s), []).append(ratio if args.use_ratio else uniq)
                    if args.curve:
                        uniq_bins, total_bins = calc_unique_bins(state, eval_file, pmin, pmax, curve_bin)
                        for i in range(curve_bins):
                            denom = total_bins[i]
                            r = (uniq_bins[i] / denom) if denom > 0 else 0.0
                            curve_values.setdefault((t, s, i), []).append(r)

    if not rows:
        raise SystemExit("ERROR: no matching state/eval files found")

    csv_path = out_dir / "progress_unique_hist.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "train_seed", "eval_seed", "tuple", "sym",
            "progress_start", "progress_end",
            "unique_count", "total_states", "unique_ratio"
        ])
        writer.writeheader()
        writer.writerows(rows)

    # plots per NT
    for t in tuples:
        data_sym = values.get((t, "sym"), [])
        data_notsym = values.get((t, "notsym"), [])
        if not data_sym and not data_notsym:
            continue
        # choose bins based on combined data
        combined = data_sym + data_notsym
        if not combined:
            continue
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(data_sym, bins=args.bins, alpha=0.6, label="sym")
        ax.hist(data_notsym, bins=args.bins, alpha=0.6, label="notsym")
        xlab = "unique_ratio" if args.use_ratio else "unique boards (progress range)"
        ax.set_xlabel(xlab)
        ax.set_ylabel("count")
        if not args.no_title:
            if args.use_ratio:
                ax.set_title(f"NT{t} unique_ratio (progress {pmin}-{pmax})")
            else:
                ax.set_title(f"NT{t} unique boards (progress {pmin}-{pmax})")
        ax.legend()
        fig.tight_layout()
        ext = args.ext.lstrip('.')
        fig.savefig(out_dir / f"progress_unique_hist_NT{t}.{ext}", dpi=200, bbox_inches="tight")
        plt.close(fig)

        if args.pdf:
            pdf_dir = Path(args.pdf_out_dir) if args.pdf_out_dir else out_dir
            pdf_dir.mkdir(parents=True, exist_ok=True)
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.hist(data_sym, bins=args.bins, alpha=0.6, label="sym")
            ax.hist(data_notsym, bins=args.bins, alpha=0.6, label="notsym")
            xlab = "unique_ratio" if args.use_ratio else "unique boards (progress range)"
            ax.set_xlabel(xlab)
            ax.set_ylabel("count")
            if not args.no_title:
                if args.use_ratio:
                    ax.set_title(f"NT{t} unique_ratio (progress {pmin}-{pmax})")
                else:
                    ax.set_title(f"NT{t} unique boards (progress {pmin}-{pmax})")
            ax.legend()
            fig.tight_layout()
            fig.savefig(pdf_dir / f"progress_unique_hist_NT{t}.pdf", bbox_inches="tight")
            plt.close(fig)

    print(f"saved: {csv_path}")
    print(f"plots: {out_dir}")

    if args.curve:
        curve_csv = out_dir / "progress_unique_curve.csv"
        with curve_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "tuple", "sym", "progress_start", "progress_end",
                "progress_center", "unique_ratio_mean", "unique_ratio_sd", "n_samples"
            ])
            writer.writeheader()
            for t in tuples:
                for s in syms:
                    for i in range(curve_bins):
                        vals = curve_values.get((t, s, i), [])
                        if not vals:
                            continue
                        b_start = pmin + i * curve_bin
                        b_end = min(pmax, b_start + curve_bin - 1)
                        center = (b_start + b_end) / 2.0
                        mean, sd = mean_std(vals)
                        writer.writerow({
                            "tuple": f"NT{t}",
                            "sym": s,
                            "progress_start": b_start,
                            "progress_end": b_end,
                            "progress_center": f"{center:.1f}",
                            "unique_ratio_mean": f"{mean:.6f}",
                            "unique_ratio_sd": f"{sd:.6f}",
                            "n_samples": len(vals),
                        })

        for t in tuples:
            x = []
            y_sym = []
            y_notsym = []
            sd_sym = []
            sd_notsym = []
            for i in range(curve_bins):
                b_start = pmin + i * curve_bin
                b_end = min(pmax, b_start + curve_bin - 1)
                center = (b_start + b_end) / 2.0
                x.append(center)
                vals_sym = curve_values.get((t, "sym", i), [])
                vals_notsym = curve_values.get((t, "notsym", i), [])
                m_sym, s_sym = mean_std(vals_sym)
                m_notsym, s_notsym = mean_std(vals_notsym)
                y_sym.append(m_sym if vals_sym else float("nan"))
                y_notsym.append(m_notsym if vals_notsym else float("nan"))
                sd_sym.append(s_sym if vals_sym else 0.0)
                sd_notsym.append(s_notsym if vals_notsym else 0.0)

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(x, y_sym, label="sym")
            ax.plot(x, y_notsym, label="notsym")
            if not args.curve_no_sd:
                ax.fill_between(x,
                                [a - b for a, b in zip(y_sym, sd_sym)],
                                [a + b for a, b in zip(y_sym, sd_sym)],
                                alpha=0.2)
                ax.fill_between(x,
                                [a - b for a, b in zip(y_notsym, sd_notsym)],
                                [a + b for a, b in zip(y_notsym, sd_notsym)],
                                alpha=0.2)
            ax.set_xlabel("progress")
            ax.set_ylabel("unique_ratio")
            if not args.no_title:
                ax.set_title(f"NT{t} unique_ratio by progress (bin={curve_bin})")
            ax.legend()
            fig.tight_layout()
            ext = args.ext.lstrip(".")
            fig.savefig(out_dir / f"progress_unique_curve_NT{t}.{ext}", dpi=200, bbox_inches="tight")
            plt.close(fig)

            if args.pdf:
                pdf_dir = Path(args.pdf_out_dir) if args.pdf_out_dir else out_dir
                pdf_dir.mkdir(parents=True, exist_ok=True)
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.plot(x, y_sym, label="sym")
                ax.plot(x, y_notsym, label="notsym")
                if not args.curve_no_sd:
                    ax.fill_between(x,
                                    [a - b for a, b in zip(y_sym, sd_sym)],
                                    [a + b for a, b in zip(y_sym, sd_sym)],
                                    alpha=0.2)
                    ax.fill_between(x,
                                    [a - b for a, b in zip(y_notsym, sd_notsym)],
                                    [a + b for a, b in zip(y_notsym, sd_notsym)],
                                    alpha=0.2)
                ax.set_xlabel("progress")
                ax.set_ylabel("unique_ratio")
                if not args.no_title:
                    ax.set_title(f"NT{t} unique_ratio by progress (bin={curve_bin})")
                ax.legend()
                fig.tight_layout()
                fig.savefig(pdf_dir / f"progress_unique_curve_NT{t}.pdf", bbox_inches="tight")
                plt.close(fig)

        print(f"curve csv: {curve_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

    pmin, pmax = args.progress_start, args.progress_end
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

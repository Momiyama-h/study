#!/usr/bin/env python3
"""Compute LUT occupancy per progress bin from board_data state logs (3x3 mini2048).

- Reads state.txt (all states) from board_data_v2
- Computes progress = (sum tile values) / 2
- Bins by progress (quantile or fixed)
- For each bin, counts unique tuple indices used (occupancy)
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

C = 11  # tile variation (0..10)
NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compute N-tuple LUT occupancy per progress bin from board_data state.txt"
        )
    )
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root (default: board_data_v2)",
    )
    p.add_argument("--train-seed-start", type=int, default=None)
    p.add_argument("--train-seed-end", type=int, default=None)
    p.add_argument("--train-seeds", default="", help="comma/space list")
    p.add_argument("--eval-seed-start", type=int, default=None)
    p.add_argument("--eval-seed-end", type=int, default=None)
    p.add_argument("--eval-seeds", default="", help="comma/space list")
    p.add_argument("--tuples", default="4,5,6", help="comma-separated tuples")
    p.add_argument("--sym-list", default="sym,notsym", help="comma-separated")
    p.add_argument(
        "--bin-mode",
        choices=["quantile", "fixed"],
        default="quantile",
        help="binning mode (quantile or fixed)",
    )
    p.add_argument("--bins", type=int, default=10, help="number of bins (quantile)")
    p.add_argument(
        "--bin-width", type=int, default=10, help="progress bin width (fixed mode)"
    )
    p.add_argument("--progress-start", type=int, default=None)
    p.add_argument("--progress-end", type=int, default=None)
    p.add_argument(
        "--out-dir",
        default="",
        help="output dir (default: analysis_outputs_v2/<run>/progress_occupancy)",
    )
    p.add_argument("--no-title", action="store_true")
    p.add_argument("--ext", default="png", help="plot extension (png/pdf)")
    p.add_argument("--pdf", action="store_true", help="also save pdf")
    p.add_argument("--pdf-out-dir", default="", help="pdf output dir (optional)")
    p.add_argument(
        "--nt4a",
        action="store_true",
        help="use NT4a tuple definitions (only affects NT4)",
    )
    return p.parse_args()


def parse_seed_list(raw: str) -> List[int]:
    if not raw:
        return []
    return [int(x) for x in raw.replace(",", " ").split() if x.strip()]


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


def list_eval_seeds_for_nt(nt_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in nt_dir.glob("eval_seed*"):
        if not p.is_dir():
            continue
        es = parse_eval_seed_dir(p.name)
        if es is not None:
            evals.append(es)
    return sorted(evals)


def iter_state_boards(state_path: Path) -> Iterable[Tuple[int, ...]]:
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn"):
                continue
            parts = line.split()
            if len(parts) != 9:
                continue
            try:
                yield tuple(int(x) for x in parts)
            except ValueError:
                continue


def calc_progress(board: Sequence[int]) -> int:
    s = 0
    for v in board:
        if v > 0:
            s += 1 << v
    return s // 2


def read_pos_from_header(path: Path, want_nt4a: bool, tuple_size: int) -> List[List[int]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_nt4a = False
    in_else = False
    in_pos = False
    buf: List[str] = []
    for line in lines:
        if line.strip().startswith("#ifdef NT4A"):
            in_nt4a = True
            continue
        if line.strip().startswith("#else") and in_nt4a:
            in_else = True
            continue
        if line.strip().startswith("#endif") and in_nt4a:
            in_nt4a = False
            in_else = False
            continue
        if in_nt4a:
            if want_nt4a and not in_else:
                pass
            elif (not want_nt4a) and in_else:
                pass
            else:
                continue
        if "const int pos" in line:
            in_pos = True
            continue
        if in_pos:
            if line.strip().startswith("};"):
                break
            buf.append(line)

    pos: List[List[int]] = []
    for line in buf:
        if "{" not in line:
            continue
        nums = re.findall(r"-?\d+", line)
        if len(nums) < tuple_size:
            continue
        pos.append([int(n) for n in nums[:tuple_size]])
    return pos


def read_sympos_from_header(path: Path) -> List[List[int]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_sympos = False
    buf: List[str] = []
    for line in lines:
        if "const int sympos" in line:
            in_sympos = True
            continue
        if in_sympos:
            if line.strip().startswith("};"):
                break
            buf.append(line)

    sympos: List[List[int]] = []
    for line in buf:
        if "{" not in line:
            continue
        nums = re.findall(r"-?\d+", line)
        if len(nums) == 9:
            sympos.append([int(n) for n in nums])
    if len(sympos) != 8:
        raise ValueError(f"sympos parse failed: {path} (found {len(sympos)})")
    return sympos


def tuple_definitions(tuple_n: int, sym: str, want_nt4a: bool) -> List[List[int]]:
    base = Path(__file__).resolve().parents[2] / "training"
    if tuple_n == 4:
        header = base / ("4tuples_sym.h" if sym == "sym" else "4tuples_nosym.h")
        return read_pos_from_header(header, want_nt4a, tuple_n)
    if tuple_n == 5:
        header = base / ("5tuples_sym.h" if sym == "sym" else "5tuples_notsym.h")
        return read_pos_from_header(header, False, tuple_n)
    if tuple_n == 6:
        header = base / ("6tuples_sym.h" if sym == "sym" else "6tuples_notsym.h")
        return read_pos_from_header(header, False, tuple_n)
    raise ValueError(f"unsupported tuple size: {tuple_n}")


def sympos_definitions(tuple_n: int) -> List[List[int]]:
    base = Path(__file__).resolve().parents[2] / "training"
    header = base / f"{tuple_n}tuples_sym.h"
    return read_sympos_from_header(header)


def tuple_index(board: Sequence[int], pos: Sequence[int]) -> int:
    idx = 0
    for p in pos:
        idx = idx * C + board[p]
    return idx


def tuple_index_sym(board: Sequence[int], pos: Sequence[int], sympos: Sequence[int]) -> int:
    idx = 0
    for p in pos:
        idx = idx * C + board[sympos[p]]
    return idx


def build_quantile_bins(counter: Counter, nbins: int) -> List[Tuple[int, int]]:
    total = sum(counter.values())
    if total == 0:
        return []
    items = sorted(counter.items())
    targets = [(i + 1) * total / nbins for i in range(nbins - 1)]
    bins: List[Tuple[int, int]] = []
    bin_start = items[0][0]
    cum = 0
    t_idx = 0
    for p, c in items:
        cum += c
        while t_idx < len(targets) and cum >= targets[t_idx]:
            bins.append((bin_start, p))
            bin_start = p + 1
            t_idx += 1
    bins.append((bin_start, items[-1][0]))
    return bins


def build_fixed_bins(pmin: int, pmax: int, width: int) -> List[Tuple[int, int]]:
    bins: List[Tuple[int, int]] = []
    cur = pmin
    while cur <= pmax:
        end = min(pmax, cur + width - 1)
        bins.append((cur, end))
        cur = end + 1
    return bins


def find_bin(progress: int, bins: List[Tuple[int, int]]) -> Optional[int]:
    for i, (a, b) in enumerate(bins):
        if a <= progress <= b:
            return i
    return None


def compute_dataset(
    state_path: Path,
    tuple_pos: List[List[int]],
    sympos_list: Optional[List[List[int]]],
    bins: List[Tuple[int, int]],
    sym: str,
) -> Tuple[List[int], List[List[int]], List[List[int]]]:
    num_bins = len(bins)
    num_tuples = len(tuple_pos)
    uniq_sets = [[set() for _ in range(num_tuples)] for _ in range(num_bins)]
    access_counts = [[0 for _ in range(num_tuples)] for _ in range(num_bins)]
    n_states = [0 for _ in range(num_bins)]

    is_sym = sym == "sym" and sympos_list is not None

    for board in iter_state_boards(state_path):
        prg = calc_progress(board)
        bidx = find_bin(prg, bins)
        if bidx is None:
            continue
        n_states[bidx] += 1
        for ti, pos in enumerate(tuple_pos):
            if is_sym:
                for sympos in sympos_list:
                    idx = tuple_index_sym(board, pos, sympos)
                    uniq_sets[bidx][ti].add(idx)
                    access_counts[bidx][ti] += 1
            else:
                idx = tuple_index(board, pos)
                uniq_sets[bidx][ti].add(idx)
                access_counts[bidx][ti] += 1

    uniq_counts = [[len(s) for s in row] for row in uniq_sets]
    return n_states, uniq_counts, access_counts


def mean_sd(vals: Sequence[float]) -> Tuple[float, float]:
    if not vals:
        return float("nan"), float("nan")
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


def main() -> int:
    args = parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run dir not found: {run_dir}")

    tuples = [int(x) for x in args.tuples.replace(",", " ").split() if x.strip()]
    syms = [x.strip() for x in args.sym_list.replace(",", " ").split() if x.strip()]

    if args.train_seeds:
        train_seeds = parse_seed_list(args.train_seeds)
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    if args.eval_seeds:
        eval_seeds_fixed = parse_seed_list(args.eval_seeds)
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds_fixed = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds_fixed = None

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_root = Path("/HDD/momiyama2/data/study/analysis_outputs")
        if str(board_root).endswith("board_data_v2"):
            out_root = Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        out_dir = out_root / args.run_name / "progress_occupancy"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Precompute tuple definitions
    tuple_pos: Dict[Tuple[int, str], List[List[int]]] = {}
    sympos_map: Dict[int, List[List[int]]] = {}
    for t in tuples:
        for s in syms:
            tuple_pos[(t, s)] = tuple_definitions(t, s, args.nt4a)
        if "sym" in syms:
            sympos_map[t] = sympos_definitions(t)

    # First pass: progress distribution for quantile bins
    counter = Counter()
    total_states = 0
    sample_printed = False
    missing = []

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
                    else:
                        state = nt_dir / f"eval_seed{ev}" / "state.txt"
                    if not state.exists():
                        missing.append((tr, ev, t, s, str(state)))
                        continue
                    if not sample_printed:
                        print("sample state path:", state)
                        sample_printed = True
                    for board in iter_state_boards(state):
                        prg = calc_progress(board)
                        if args.progress_start is not None and prg < args.progress_start:
                            continue
                        if args.progress_end is not None and prg > args.progress_end:
                            continue
                        counter[prg] += 1
                        total_states += 1

    if missing:
        print("Missing state.txt (showing up to 20):")
        for row in missing[:20]:
            print("  ", row)

    if total_states == 0:
        raise SystemExit("ERROR: no states found for progress distribution")

    # Build bins
    if args.bin_mode == "quantile":
        bins = build_quantile_bins(counter, max(1, args.bins))
    else:
        if args.progress_start is not None:
            pmin = args.progress_start
        else:
            pmin = min(counter.keys())
        if args.progress_end is not None:
            pmax = args.progress_end
        else:
            pmax = max(counter.keys())
        bins = build_fixed_bins(pmin, pmax, max(1, args.bin_width))

    if not bins:
        raise SystemExit("ERROR: failed to build bins")

    print("bins:")
    for i, (a, b) in enumerate(bins):
        print(f"  bin{i}: {a}-{b}")

    # Second pass: per-dataset occupancy
    rows: List[Dict[str, str]] = []
    rows_all: List[Dict[str, str]] = []

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
                    else:
                        state = nt_dir / f"eval_seed{ev}" / "state.txt"
                    if not state.exists():
                        continue

                    n_states, uniq_counts, access_counts = compute_dataset(
                        state,
                        tuple_pos[(t, s)],
                        sympos_map.get(t),
                        bins,
                        s,
                    )

                    table_size = C ** t
                    num_tuples = len(tuple_pos[(t, s)])

                    for bidx, (b_start, b_end) in enumerate(bins):
                        # per tuple
                        for ti in range(num_tuples):
                            uniq = uniq_counts[bidx][ti]
                            acc = access_counts[bidx][ti]
                            occ = (uniq / table_size) if table_size > 0 else float("nan")
                            upa = (uniq / acc) if acc > 0 else float("nan")
                            if n_states[bidx] == 0:
                                occ = float("nan")
                                upa = float("nan")
                            rows.append(
                                {
                                    "run_name": args.run_name,
                                    "tuple": f"NT{t}",
                                    "sym": s,
                                    "train_seed": str(tr),
                                    "eval_seed": "" if ev is None else str(ev),
                                    "bin_id": str(bidx),
                                    "bin_start": str(b_start),
                                    "bin_end": str(b_end),
                                    "n_states": str(n_states[bidx]),
                                    "tuple_idx": str(ti),
                                    "table_size": str(table_size),
                                    "unique_indices": str(uniq),
                                    "accesses": str(acc),
                                    "occupancy": f"{occ:.6f}" if not math.isnan(occ) else "nan",
                                    "unique_per_access": f"{upa:.6f}" if not math.isnan(upa) else "nan",
                                }
                            )

                        # aggregated over tuples
                        uniq_sum = sum(uniq_counts[bidx])
                        acc_sum = sum(access_counts[bidx])
                        table_sum = table_size * num_tuples
                        occ_all = (uniq_sum / table_sum) if table_sum > 0 else float("nan")
                        upa_all = (uniq_sum / acc_sum) if acc_sum > 0 else float("nan")
                        if n_states[bidx] == 0:
                            occ_all = float("nan")
                            upa_all = float("nan")
                        rows_all.append(
                            {
                                "run_name": args.run_name,
                                "tuple": f"NT{t}",
                                "sym": s,
                                "train_seed": str(tr),
                                "eval_seed": "" if ev is None else str(ev),
                                "bin_id": str(bidx),
                                "bin_start": str(b_start),
                                "bin_end": str(b_end),
                                "n_states": str(n_states[bidx]),
                                "tuple_idx": "all",
                                "table_size": str(table_sum),
                                "unique_indices": str(uniq_sum),
                                "accesses": str(acc_sum),
                                "occupancy": f"{occ_all:.6f}" if not math.isnan(occ_all) else "nan",
                                "unique_per_access": f"{upa_all:.6f}" if not math.isnan(upa_all) else "nan",
                            }
                        )

    if not rows_all:
        raise SystemExit("ERROR: no occupancy rows generated")

    # Write CSVs
    per_tuple_csv = out_dir / "progress_occupancy_per_tuple.csv"
    with per_tuple_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "run_name",
                "tuple",
                "sym",
                "train_seed",
                "eval_seed",
                "bin_id",
                "bin_start",
                "bin_end",
                "n_states",
                "tuple_idx",
                "table_size",
                "unique_indices",
                "accesses",
                "occupancy",
                "unique_per_access",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    summary_csv = out_dir / "progress_occupancy_all.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "run_name",
                "tuple",
                "sym",
                "train_seed",
                "eval_seed",
                "bin_id",
                "bin_start",
                "bin_end",
                "n_states",
                "tuple_idx",
                "table_size",
                "unique_indices",
                "accesses",
                "occupancy",
                "unique_per_access",
            ],
        )
        w.writeheader()
        w.writerows(rows_all)

    print("saved:", per_tuple_csv)
    print("saved:", summary_csv)

    # Aggregate by train_seed (mean over eval_seed) for plotting
    by_train: Dict[Tuple[str, str, int], List[float]] = defaultdict(list)
    for r in rows_all:
        key = (r["tuple"], r["sym"], int(r["bin_id"]))
        by_train[(r["tuple"], r["sym"], int(r["bin_id"]), r["train_seed"])].append(
            float(r["occupancy"]) if r["occupancy"] != "nan" else float("nan")
        )

    # Build per-train mean list
    train_vals: Dict[Tuple[str, str, int], List[float]] = defaultdict(list)
    for (tup, sym, bidx, tr), vals in by_train.items():
        v = [x for x in vals if not math.isnan(x)]
        if not v:
            continue
        train_vals[(tup, sym, bidx)].append(sum(v) / len(v))

    # Plot per NT
    for t in tuples:
        for_plot = {s: [] for s in syms}
        for s in syms:
            for bidx in range(len(bins)):
                vals = train_vals.get((f"NT{t}", s, bidx), [])
                m, sd = mean_sd(vals)
                for_plot[s].append((m, sd, len(vals)))

        fig, ax = plt.subplots(figsize=(7, 4))
        xs = [0.5 * (a + b) for a, b in bins]
        for s in syms:
            ys = [v[0] for v in for_plot[s]]
            sds = [v[1] for v in for_plot[s]]
            ax.plot(xs, ys, label=s)
            if any(not math.isnan(sd) for sd in sds):
                lower = [max(0.0, y - sd) if not math.isnan(y) else float("nan") for y, sd in zip(ys, sds)]
                upper = [min(1.0, y + sd) if not math.isnan(y) else float("nan") for y, sd in zip(ys, sds)]
                ax.fill_between(xs, lower, upper, alpha=0.2)

        ax.set_xlabel("progress (bin center)")
        ax.set_ylabel("occupancy (unique_indices / table_size)")
        if not args.no_title:
            ax.set_title(f"NT{t} progress occupancy")
        ax.legend()
        fig.tight_layout()
        ext = args.ext.lstrip(".")
        fig.savefig(out_dir / f"progress_occupancy_NT{t}.{ext}", dpi=200, bbox_inches="tight")
        plt.close(fig)

        if args.pdf:
            pdf_dir = Path(args.pdf_out_dir) if args.pdf_out_dir else out_dir
            pdf_dir.mkdir(parents=True, exist_ok=True)
            fig, ax = plt.subplots(figsize=(7, 4))
            for s in syms:
                ys = [v[0] for v in for_plot[s]]
                sds = [v[1] for v in for_plot[s]]
                ax.plot(xs, ys, label=s)
                if any(not math.isnan(sd) for sd in sds):
                    lower = [max(0.0, y - sd) if not math.isnan(y) else float("nan") for y, sd in zip(ys, sds)]
                    upper = [min(1.0, y + sd) if not math.isnan(y) else float("nan") for y, sd in zip(ys, sds)]
                    ax.fill_between(xs, lower, upper, alpha=0.2)
            ax.set_xlabel("progress (bin center)")
            ax.set_ylabel("occupancy (unique_indices / table_size)")
            if not args.no_title:
                ax.set_title(f"NT{t} progress occupancy")
            ax.legend()
            fig.tight_layout()
            fig.savefig(pdf_dir / f"progress_occupancy_NT{t}.pdf", bbox_inches="tight")
            plt.close(fig)

    print(f"plots: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

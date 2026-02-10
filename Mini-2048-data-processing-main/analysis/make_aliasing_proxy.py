#!/usr/bin/env python3
"""Alias/proxy stats from board_data state logs (3x3 mini2048).

Compute proxy for representation aliasing using final boards per game.
Outputs per (train_seed, eval_seed, NT, sym) stats and slide-ready plots.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - numpy is optional but expected
    np = None

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover - matplotlib expected
    raise SystemExit(f"ERROR: matplotlib required: {exc}")

try:
    from scipy import stats as spstats  # type: ignore
except Exception:
    spstats = None


GAMEOVER_RE = re.compile(r"score:\s*(\d+)")
PROGRESS_RE = re.compile(r"progress:\s*(\d+)")
NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compute aliasing proxy stats from board_data state.txt (final boards)."
        )
    )
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root",
    )
    p.add_argument("--train-seed-start", type=int, default=None)
    p.add_argument("--train-seed-end", type=int, default=None)
    p.add_argument("--train-seeds", default="", help="comma/space list")
    p.add_argument("--eval-seed-start", type=int, default=None)
    p.add_argument("--eval-seed-end", type=int, default=None)
    p.add_argument("--eval-seeds", default="", help="comma/space list")
    p.add_argument("--tuples", default="4,6", help="comma-separated tuples")
    p.add_argument("--sym-list", default="sym,notsym", help="comma-separated")
    p.add_argument(
        "--out-dir",
        default="",
        help="output directory (default: analysis_outputs_v2/<run>/aliasing_proxy)",
    )
    p.add_argument("--pdf", action="store_true", help="also save pdf")
    p.add_argument(
        "--perf",
        choices=["score", "reach-exp"],
        default="score",
        help="performance metric for scatter",
    )
    p.add_argument(
        "--reach-exp",
        type=int,
        default=9,
        help="tile exponent for reach-exp performance",
    )
    p.add_argument("--progress-start", type=int, default=None)
    p.add_argument("--progress-end", type=int, default=None)
    p.add_argument("--occupancy", action="store_true", help="compute occupancy")
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


def list_train_seeds(run_dir: Path) -> List[int]:
    seeds: List[int] = []
    for p in run_dir.glob("seed*"):
        if p.is_dir() and p.name.startswith("seed"):
            try:
                seeds.append(int(p.name[4:]))
            except ValueError:
                continue
    return sorted(seeds)


def list_eval_seeds(run_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in run_dir.glob("seed*/NT*_*/*"):
        if not p.is_dir():
            continue
        if p.name.startswith("eval_seed"):
            try:
                evals.append(int(p.name[9:]))
            except ValueError:
                continue
    return sorted(set(evals))


def d4_maps() -> List[Tuple[int, ...]]:
    # row-major indices 0..8
    return [
        (0, 1, 2, 3, 4, 5, 6, 7, 8),  # identity
        (6, 3, 0, 7, 4, 1, 8, 5, 2),  # rot90
        (8, 7, 6, 5, 4, 3, 2, 1, 0),  # rot180
        (2, 5, 8, 1, 4, 7, 0, 3, 6),  # rot270
        (2, 1, 0, 5, 4, 3, 8, 7, 6),  # mirror LR
        (6, 7, 8, 3, 4, 5, 0, 1, 2),  # mirror TB
        (0, 3, 6, 1, 4, 7, 2, 5, 8),  # diag main
        (8, 5, 2, 7, 4, 1, 6, 3, 0),  # diag anti
    ]


def apply_map(board: Sequence[int], mp: Sequence[int]) -> Tuple[int, ...]:
    return tuple(board[i] for i in mp)


def canonical_board(board: Sequence[int]) -> Tuple[int, ...]:
    return min(apply_map(board, mp) for mp in d4_maps())


def parse_final_boards(
    state_path: Path,
    progress_start: Optional[int] = None,
    progress_end: Optional[int] = None,
) -> Tuple[List[Tuple[int, ...]], List[int], List[int]]:
    boards: List[Tuple[int, ...]] = []
    scores: List[int] = []
    progresses: List[int] = []
    last_board: Optional[Tuple[int, ...]] = None
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn:"):
                if last_board is not None:
                    m = GAMEOVER_RE.search(line)
                    p = PROGRESS_RE.search(line)
                    score = int(m.group(1)) if m else 0
                    if p:
                        prog = int(p.group(1))
                    else:
                        # progress can be derived from the final board (sum tile values / 2)
                        prog_sum = 0
                        for v in last_board:
                            if v != 0:
                                prog_sum += 1 << v
                        prog = prog_sum // 2
                    if progress_start is not None or progress_end is not None:
                        if progress_start is not None and prog < progress_start:
                            last_board = None
                            continue
                        if progress_end is not None and prog > progress_end:
                            last_board = None
                            continue
                    boards.append(last_board)
                    scores.append(score)
                    if prog is not None:
                        progresses.append(prog)
                last_board = None
                continue
            parts = line.split()
            if len(parts) != 9:
                continue
            try:
                vals = tuple(int(x) for x in parts)
            except ValueError:
                continue
            last_board = vals
    return boards, scores, progresses


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
        # decide if this line should be considered
        if in_nt4a:
            if want_nt4a and not in_else:
                pass
            elif (not want_nt4a) and in_else:
                pass
            else:
                continue
        # grab pos block
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
        if not nums:
            continue
        # Ignore trailing comment numbers; only take tuple_size entries.
        if len(nums) < tuple_size:
            continue
        pos.append([int(n) for n in nums[:tuple_size]])
    return pos


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


def tuple_index(board: Sequence[int], pos: Sequence[int], c: int = 11) -> int:
    idx = 0
    for p in pos:
        idx = idx * c + board[p]
    return idx


def mean_sd(vals: Sequence[float]) -> Tuple[float, float]:
    if not vals:
        return float("nan"), float("nan")
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


def ci95(vals: Sequence[float]) -> Tuple[float, float]:
    if not vals:
        return float("nan"), float("nan")
    m, sd = mean_sd(vals)
    if len(vals) < 2:
        return m, m
    se = sd / math.sqrt(len(vals))
    tcrit = 1.96
    if spstats is not None:
        tcrit = float(spstats.t.ppf(0.975, df=len(vals) - 1))
    return m - tcrit * se, m + tcrit * se


def paired_tests(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float]:
    if spstats is None or not a or not b:
        return float("nan"), float("nan")
    t_p = float(spstats.ttest_rel(a, b).pvalue)
    try:
        w_p = float(spstats.wilcoxon(a, b).pvalue)
    except Exception:
        w_p = float("nan")
    return t_p, w_p


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
        eval_seeds = parse_seed_list(args.eval_seeds)
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds = list_eval_seeds(run_dir)

    out_dir = Path(args.out_dir) if args.out_dir else (
        Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "aliasing_proxy"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # tuple definitions
    tuple_pos: Dict[Tuple[int, str], List[List[int]]] = {}
    for t in tuples:
        for s in syms:
            tuple_pos[(t, s)] = tuple_definitions(t, s, args.nt4a)

    # data structures
    stats = []
    missing = []
    sample_printed = False

    for tr in train_seeds:
        for ev in eval_seeds:
            for t in tuples:
                for s in syms:
                    base = run_dir / f"seed{tr}" / f"NT{t}_{s}"
                    state_path = base / f"eval_seed{ev}" / "state.txt"
                    if not state_path.exists():
                        state_path = base / "state.txt"
                    if not state_path.exists():
                        missing.append((tr, ev, t, s, str(state_path)))
                        continue

                    boards, scores, progresses = parse_final_boards(
                        state_path, args.progress_start, args.progress_end
                    )
                    if not sample_printed:
                        print("sample state path:", state_path)
                        print("sample board:", boards[0] if boards else None)
                        if progresses:
                            print("sample progress:", progresses[0])
                        if args.progress_start is not None:
                            print(
                                f"progress filter: [{args.progress_start}, {args.progress_end}]"
                            )
                        sample_printed = True

                    u_board = set()
                    u_phi = set()
                    occ_set = [set() for _ in range(len(tuple_pos[(t, s)]))]
                    for b in boards:
                        cb = canonical_board(b)
                        u_board.add(cb)
                        phi = []
                        for idx, pos in enumerate(tuple_pos[(t, s)]):
                            tidx = tuple_index(cb, pos)
                            phi.append(tidx)
                            if args.occupancy:
                                occ_set[idx].add(tidx)
                        u_phi.add(tuple(phi))

                    u_board_n = len(u_board)
                    u_phi_n = len(u_phi)
                    collision = 1.0 - (u_phi_n / u_board_n) if u_board_n else float("nan")
                    alias = (u_board_n / u_phi_n) if u_phi_n else float("nan")

                    occ_ratio = float("nan")
                    if args.occupancy and tuple_pos[(t, s)]:
                        total = 11 ** t
                        occ_ratio = sum(len(ss) / total for ss in occ_set) / len(occ_set)

                    perf = float("nan")
                    if args.perf == "score":
                        if scores:
                            perf = sum(scores) / len(scores)
                    else:
                        # reach-exp using final board max tile exp
                        k = args.reach_exp
                        if boards:
                            cnt = 0
                            for b in boards:
                                if max(b) >= k:
                                    cnt += 1
                            perf = cnt / len(boards)

                    stats.append(
                        {
                            "train_seed": tr,
                            "eval_seed": ev,
                            "tuple": t,
                            "sym": s,
                            "n_games": len(boards),
                            "u_board": u_board_n,
                            "u_phi": u_phi_n,
                            "collision": collision,
                            "alias": alias,
                            "perf": perf,
                            "occupancy": occ_ratio,
                        }
                    )

    # report missing
    if missing:
        print("Missing state.txt (showing up to 20):")
        for row in missing[:20]:
            print("  ", row)

    # write per (train, eval) stats
    csv_path = out_dir / "aliasing_stats.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "train_seed",
                "eval_seed",
                "tuple",
                "sym",
                "n_games",
                "u_board",
                "u_phi",
                "collision",
                "alias",
                "perf",
                "occupancy",
            ],
        )
        w.writeheader()
        for r in stats:
            w.writerow(r)
    print("saved:", csv_path)

    # aggregate per train_seed (mean over eval_seed)
    by_train: Dict[Tuple[int, int, str], List[Dict[str, float]]] = defaultdict(list)
    for r in stats:
        key = (r["train_seed"], r["tuple"], r["sym"])
        by_train[key].append(r)

    train_rows = []
    for (tr, t, s), rows in by_train.items():
        coll_vals = [float(x["collision"]) for x in rows if not math.isnan(x["collision"])]
        perf_vals = [float(x["perf"]) for x in rows if not math.isnan(x["perf"])]
        occ_vals = [float(x["occupancy"]) for x in rows if not math.isnan(x["occupancy"])]
        coll_mean = sum(coll_vals) / len(coll_vals) if coll_vals else float("nan")
        perf_mean = sum(perf_vals) / len(perf_vals) if perf_vals else float("nan")
        occ_mean = sum(occ_vals) / len(occ_vals) if occ_vals else float("nan")
        train_rows.append(
            {
                "train_seed": tr,
                "tuple": t,
                "sym": s,
                "collision_mean": coll_mean,
                "perf_mean": perf_mean,
                "occupancy_mean": occ_mean,
            }
        )

    # paired tests per tuple between sym vs notsym
    summary_path = out_dir / "aliasing_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "tuple",
                "metric",
                "sym_mean",
                "sym_ci_low",
                "sym_ci_high",
                "notsym_mean",
                "notsym_ci_low",
                "notsym_ci_high",
                "paired_t_p",
                "wilcoxon_p",
            ]
        )
        for t in tuples:
            sym_vals = [r["collision_mean"] for r in train_rows if r["tuple"] == t and r["sym"] == "sym"]
            not_vals = [r["collision_mean"] for r in train_rows if r["tuple"] == t and r["sym"] == "notsym"]
            s_mean, s_sd = mean_sd(sym_vals)
            n_mean, n_sd = mean_sd(not_vals)
            s_ci = ci95(sym_vals)
            n_ci = ci95(not_vals)
            t_p, w_p = paired_tests(sym_vals, not_vals)
            w.writerow(
                [
                    t,
                    "collision",
                    f"{s_mean:.6f}",
                    f"{s_ci[0]:.6f}",
                    f"{s_ci[1]:.6f}",
                    f"{n_mean:.6f}",
                    f"{n_ci[0]:.6f}",
                    f"{n_ci[1]:.6f}",
                    f"{t_p:.6g}",
                    f"{w_p:.6g}",
                ]
            )
    print("saved:", summary_path)

    # Figure 1: collision by condition
    fig, axes = plt.subplots(1, len(tuples), figsize=(6 * len(tuples), 5), sharey=True)
    if len(tuples) == 1:
        axes = [axes]
    for ax, t in zip(axes, tuples):
        for xi, s in enumerate(syms):
            vals = [
                r["collision_mean"]
                for r in train_rows
                if r["tuple"] == t and r["sym"] == s
            ]
            if not vals:
                continue
            x = [xi + (i - (len(vals) - 1) / 2) * 0.03 for i in range(len(vals))]
            ax.scatter(x, vals, alpha=0.6, label=s)
            m, _ = mean_sd(vals)
            lo, hi = ci95(vals)
            ax.errorbar([xi], [m], yerr=[[m - lo], [hi - m]], fmt="o", color="black")
        ax.set_xticks(range(len(syms)))
        ax.set_xticklabels(syms)
        ax.set_title(f"NT{t} collision")
        ax.set_ylabel("collision")
    fig.tight_layout()
    fig_path = out_dir / "collision_compare.png"
    fig.savefig(fig_path, dpi=200)
    if args.pdf:
        fig.savefig(out_dir / "collision_compare.pdf")
    print("saved:", fig_path)

    # Figure 2: perf vs collision scatter
    fig2, axes2 = plt.subplots(1, len(tuples), figsize=(6 * len(tuples), 5), sharey=False)
    if len(tuples) == 1:
        axes2 = [axes2]
    for ax, t in zip(axes2, tuples):
        for s in syms:
            xs = [
                r["collision_mean"]
                for r in train_rows
                if r["tuple"] == t and r["sym"] == s
            ]
            ys = [
                r["perf_mean"]
                for r in train_rows
                if r["tuple"] == t and r["sym"] == s
            ]
            ax.scatter(xs, ys, label=s, alpha=0.7)
        ax.set_title(f"NT{t} perf vs collision")
        ax.set_xlabel("collision")
        ax.set_ylabel(args.perf)
        ax.legend()
    fig2.tight_layout()
    fig2_path = out_dir / "perf_vs_collision.png"
    fig2.savefig(fig2_path, dpi=200)
    if args.pdf:
        fig2.savefig(out_dir / "perf_vs_collision.pdf")
    print("saved:", fig2_path)

    # Optional occupancy plot
    if args.occupancy:
        fig3, axes3 = plt.subplots(1, len(tuples), figsize=(6 * len(tuples), 5), sharey=True)
        if len(tuples) == 1:
            axes3 = [axes3]
        for ax, t in zip(axes3, tuples):
            for xi, s in enumerate(syms):
                vals = [
                    r["occupancy_mean"]
                    for r in train_rows
                    if r["tuple"] == t and r["sym"] == s
                ]
                if not vals:
                    continue
                x = [xi + (i - (len(vals) - 1) / 2) * 0.03 for i in range(len(vals))]
                ax.scatter(x, vals, alpha=0.6, label=s)
                m, _ = mean_sd(vals)
                lo, hi = ci95(vals)
                ax.errorbar([xi], [m], yerr=[[m - lo], [hi - m]], fmt="o", color="black")
            ax.set_xticks(range(len(syms)))
            ax.set_xticklabels(syms)
            ax.set_title(f"NT{t} occupancy")
            ax.set_ylabel("occupancy ratio")
        fig3.tight_layout()
        fig3_path = out_dir / "occupancy_compare.png"
        fig3.savefig(fig3_path, dpi=200)
        if args.pdf:
            fig3.savefig(out_dir / "occupancy_compare.pdf")
        print("saved:", fig3_path)

    # Slide summary
    print("\nSlide summary (draft):")
    for t in tuples:
        sym_vals = [r["collision_mean"] for r in train_rows if r["tuple"] == t and r["sym"] == "sym"]
        not_vals = [r["collision_mean"] for r in train_rows if r["tuple"] == t and r["sym"] == "notsym"]
        if sym_vals and not_vals:
            s_mean, _ = mean_sd(sym_vals)
            n_mean, _ = mean_sd(not_vals)
            rel = "higher" if s_mean > n_mean else "lower"
            print(f"- NT{t}: collision(sym) is {rel} than notsym ({s_mean:.3f} vs {n_mean:.3f})")
    print("- Proxy is based on final boards only (not all states), but useful for condition comparison.")

    if spstats is None:
        print("NOTE: scipy not available; paired t-test / wilcoxon p-values are NaN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    if args.progress_start is not None and args.progress_end is None:
        raise SystemExit("ERROR: --progress-end is required when --progress-start is set.")
    if args.progress_end is not None and args.progress_start is None:
        raise SystemExit("ERROR: --progress-start is required when --progress-end is set.")
    if args.progress_start is not None and args.progress_end is not None:
        if args.progress_start > args.progress_end:
            raise SystemExit("ERROR: progress range is invalid (start > end).")

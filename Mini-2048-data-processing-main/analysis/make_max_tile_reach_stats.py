#!/usr/bin/env python3
import argparse
import csv
import math
import re
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, List, Optional, Tuple

NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")


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


def parse_max_exps(state_path: Path) -> List[int]:
    max_list: List[int] = []
    cur_max = -1
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn:"):
                if cur_max >= 0:
                    max_list.append(cur_max)
                cur_max = -1
                continue
            vals = list(map(int, line.split()))
            if vals:
                v = max(vals)
                if v > cur_max:
                    cur_max = v
    if cur_max >= 0:
        max_list.append(cur_max)
    return max_list


def quantile_sorted(vals: List[int], p: float) -> Optional[int]:
    if not vals:
        return None
    n = len(vals)
    idx = int(math.ceil(p * n) - 1)
    if idx < 0:
        idx = 0
    if idx >= n:
        idx = n - 1
    return vals[idx]


def iter_state_path(
    run_dir: Path, train_seed: int, eval_seed: int, tuple_id: str, sym: str, state_file: str
) -> Path:
    base = run_dir / f"seed{train_seed}" / f"NT{tuple_id}_{sym}"
    state = base / f"eval_seed{eval_seed}" / state_file
    if not state.exists():
        # fallback to non-eval_seed layout
        state = base / state_file
    return state


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "train_seed×eval_seed×NT×sym の maxタイル統計（到達確率/分位）をCSV出力"
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
    p.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    p.add_argument("--eval-seed-start", type=int, default=None)
    p.add_argument("--eval-seed-end", type=int, default=None)
    p.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    p.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    p.add_argument("--sym-list", default="", help="comma-separated sym list (default: auto)")
    p.add_argument(
        "--state-file",
        default="state.txt",
        help="state file name (default: state.txt)",
    )
    p.add_argument(
        "--reach-exp",
        type=int,
        default=9,
        help="target exponent k for reach probability (2^k) (default: 9)",
    )
    p.add_argument(
        "--split-nt",
        action="store_true",
        help="also write per-NT csvs under reach_prob/ and quantiles/",
    )
    p.add_argument(
        "--out-dir",
        default="",
        help="output dir (default: analysis_outputs_v2/<run_name>/tile_stats)",
    )
    args = p.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    # train seeds
    if args.train_seeds:
        raw = args.train_seeds.replace(",", " ").split()
        train_seeds = [int(x) for x in raw if x.strip()]
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    # eval seeds
    if args.eval_seeds:
        raw = args.eval_seeds.replace(",", " ").split()
        eval_seeds = [int(x) for x in raw if x.strip()]
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds = list_eval_seeds(run_dir)
        if not eval_seeds:
            eval_seeds = train_seeds

    # tuples/syms
    if args.tuples:
        tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    else:
        tuples, _syms = list_tuple_sym(run_dir)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    else:
        _tuples, syms = list_tuple_sym(run_dir)

    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "tile_stats"
    )
    reach_dir = out_dir / "reach_prob"
    quant_dir = out_dir / "quantiles"
    reach_dir.mkdir(parents=True, exist_ok=True)
    quant_dir.mkdir(parents=True, exist_ok=True)
    reach_path = reach_dir / f"tile_reach_prob_2pow{args.reach_exp}.csv"
    quant_path = quant_dir / "tile_max_exp_quantiles.csv"

    with ExitStack() as stack:
        f_reach = stack.enter_context(reach_path.open("w", newline="", encoding="utf-8"))
        f_quant = stack.enter_context(quant_path.open("w", newline="", encoding="utf-8"))
        w_reach = csv.writer(f_reach)
        w_quant = csv.writer(f_quant)
        header_reach = [
            "train_seed",
            "eval_seed",
            "tuple",
            "sym",
            "n_games",
            "reach_exp",
            "p_reach",
        ]
        header_quant = [
            "train_seed",
            "eval_seed",
            "tuple",
            "sym",
            "n_games",
            "median",
            "p25",
            "p75",
            "p90",
        ]
        w_reach.writerow(header_reach)
        w_quant.writerow(header_quant)

        reach_nt_writers: Dict[str, csv.writer] = {}
        quant_nt_writers: Dict[str, csv.writer] = {}
        if args.split_nt:
            for t in tuples:
                r_path = reach_dir / f"NT{t}_tile_reach_prob_2pow{args.reach_exp}.csv"
                q_path = quant_dir / f"NT{t}_tile_max_exp_quantiles.csv"
                rf = stack.enter_context(r_path.open("w", newline="", encoding="utf-8"))
                qf = stack.enter_context(q_path.open("w", newline="", encoding="utf-8"))
                rw = csv.writer(rf)
                qw = csv.writer(qf)
                rw.writerow(header_reach)
                qw.writerow(header_quant)
                reach_nt_writers[t] = rw
                quant_nt_writers[t] = qw

        for tr in train_seeds:
            for ev in eval_seeds:
                for t in tuples:
                    for s in syms:
                        state = iter_state_path(run_dir, tr, ev, t, s, args.state_file)
                        if not state.exists():
                            row_reach = [tr, ev, f"NT{t}", s, 0, args.reach_exp, ""]
                            row_quant = [tr, ev, f"NT{t}", s, 0, "", "", "", ""]
                            w_reach.writerow(row_reach)
                            w_quant.writerow(row_quant)
                            if args.split_nt:
                                reach_nt_writers[t].writerow(row_reach)
                                quant_nt_writers[t].writerow(row_quant)
                            continue
                        max_exps = parse_max_exps(state)
                        n = len(max_exps)
                        if n == 0:
                            row_reach = [tr, ev, f"NT{t}", s, 0, args.reach_exp, ""]
                            row_quant = [tr, ev, f"NT{t}", s, 0, "", "", "", ""]
                            w_reach.writerow(row_reach)
                            w_quant.writerow(row_quant)
                            if args.split_nt:
                                reach_nt_writers[t].writerow(row_reach)
                                quant_nt_writers[t].writerow(row_quant)
                            continue
                        reach = sum(1 for v in max_exps if v >= args.reach_exp) / n
                        vals = sorted(max_exps)
                        med = quantile_sorted(vals, 0.5)
                        p25 = quantile_sorted(vals, 0.25)
                        p75 = quantile_sorted(vals, 0.75)
                        p90 = quantile_sorted(vals, 0.9)
                        row_reach = [tr, ev, f"NT{t}", s, n, args.reach_exp, f"{reach:.6f}"]
                        row_quant = [tr, ev, f"NT{t}", s, n, med, p25, p75, p90]
                        w_reach.writerow(row_reach)
                        w_quant.writerow(row_quant)
                        if args.split_nt:
                            reach_nt_writers[t].writerow(row_reach)
                            quant_nt_writers[t].writerow(row_quant)

    print(f"saved: {reach_path}")
    print(f"saved: {quant_path}")
    if args.split_nt:
        print(f"saved per-NT CSVs under: {reach_dir}")
        print(f"saved per-NT CSVs under: {quant_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def parse_state_file(state_path: Path) -> Tuple[int, int, List[int]]:
    unique = set()
    total_states = 0
    max_list: List[int] = []
    cur_max: Optional[int] = None
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn"):
                if cur_max is not None:
                    max_list.append(cur_max)
                cur_max = None
                continue
            vals = line.split()
            if len(vals) != 9:
                continue
            ints = tuple(int(v) for v in vals)
            total_states += 1
            unique.add(ints)
            m = max(ints)
            if cur_max is None or m > cur_max:
                cur_max = m
    return len(unique), total_states, max_list


def mean_sd(vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not vals:
        return None, None
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


def aggregate_eval_seeds(
    eval_stats: List[Dict],
    kmin: int,
    kmax: int,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Dict[int, Tuple[Optional[float], Optional[float]]], List[int]]:
    if not eval_stats:
        return None, None, None, None, {}, []
    uniq_vals = [s["unique"] for s in eval_stats]
    ratio_vals = [s["ratio"] for s in eval_stats if s["ratio"] is not None]
    uniq_mean, uniq_sd = mean_sd(uniq_vals)
    ratio_mean, ratio_sd = mean_sd(ratio_vals)

    probs_by_k: Dict[int, Tuple[Optional[float], Optional[float]]] = {}
    for k in range(kmin, kmax + 1):
        vals = [s["prob"].get(k, 0.0) for s in eval_stats if s["games"] > 0]
        m, sd = mean_sd(vals)
        probs_by_k[k] = (m, sd)
    games_list = [s["games"] for s in eval_stats]
    return uniq_mean, uniq_sd, ratio_mean, ratio_sd, probs_by_k, games_list


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Unique board counts and max-tile probabilities from board_data/state.txt"
    )
    ap.add_argument("--run-name", required=True)
    ap.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root",
    )
    ap.add_argument(
        "--output-dir",
        default="",
        help="output dir (default: analysis_outputs/<run_name>/board_stats)",
    )
    ap.add_argument("--train-seed-start", type=int, default=None)
    ap.add_argument("--train-seed-end", type=int, default=None)
    ap.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    ap.add_argument("--eval-seed-start", type=int, default=None)
    ap.add_argument("--eval-seed-end", type=int, default=None)
    ap.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    ap.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    ap.add_argument("--sym-list", default="", help="comma-separated sym list (default: auto)")
    ap.add_argument(
        "--normalize",
        action="store_true",
        help="add unique_ratio columns (unique/total_states)",
    )
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
        tuples, _syms = list_tuple_sym(run_dir)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    else:
        _tuples, syms = list_tuple_sym(run_dir)

    # Collect per train_seed / NT / sym / eval_seed stats
    per_train: Dict[int, Dict[Tuple[str, str], List[Dict]]] = defaultdict(lambda: defaultdict(list))
    global_max_vals: List[int] = []

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
                    unique_count, total_states, max_list = parse_state_file(state)
                    games = len(max_list)
                    if total_states == 0 and games == 0:
                        continue
                    ratio = (unique_count / total_states) if total_states > 0 else None
                    cnt = Counter(max_list)
                    prob = {}
                    if games > 0:
                        for k, v in cnt.items():
                            prob[k] = v / games
                    per_train[tr][(t, s)].append(
                        {
                            "unique": unique_count,
                            "total_states": total_states,
                            "ratio": ratio,
                            "games": games,
                            "prob": prob,
                        }
                    )
                    global_max_vals.extend(max_list)

    if not global_max_vals:
        raise SystemExit("ERROR: no games found in state.txt")
    kmin, kmax = min(global_max_vals), max(global_max_vals)

    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("/HDD/momiyama2/data/study/analysis_outputs") / args.run_name / "board_stats"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # unique_board_count_seed.csv
    uniq_cols = []
    ratio_cols = []
    for t in tuples:
        for s in syms:
            base = f"NT{t}_{s}"
            uniq_cols.extend([f"{base}_unique_mean", f"{base}_unique_sd"])
            if args.normalize:
                ratio_cols.extend([f"{base}_unique_ratio_mean", f"{base}_unique_ratio_sd"])
    unique_path = out_dir / "unique_board_count_seed.csv"
    with unique_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["train_seed"] + uniq_cols + ratio_cols
        writer.writerow(header)
        for tr in train_seeds:
            row = [tr]
            for t in tuples:
                for s in syms:
                    stats = per_train[tr].get((t, s), [])
                    uniq_mean, uniq_sd, ratio_mean, ratio_sd, _probs, _games = aggregate_eval_seeds(
                        stats, kmin, kmax
                    )
                    row.append(f"{uniq_mean:.4f}" if uniq_mean is not None else "")
                    row.append(f"{uniq_sd:.4f}" if uniq_sd is not None else "")
                    if args.normalize:
                        row.append(f"{ratio_mean:.6f}" if ratio_mean is not None else "")
                        row.append(f"{ratio_sd:.6f}" if ratio_sd is not None else "")
            writer.writerow(row)

    # max_tile_prob_seed.csv
    prob_cols = []
    for t in tuples:
        for s in syms:
            for k in range(kmin, kmax + 1):
                prob_cols.append(f"NT{t}_{s}_pmax_2^{k}_mean")
                prob_cols.append(f"NT{t}_{s}_pmax_2^{k}_sd")
    max_tile_path = out_dir / "max_tile_prob_seed.csv"
    with max_tile_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["train_seed"] + prob_cols)
        for tr in train_seeds:
            row = [tr]
            for t in tuples:
                for s in syms:
                    stats = per_train[tr].get((t, s), [])
                    _um, _us, _rm, _rs, probs, _games = aggregate_eval_seeds(stats, kmin, kmax)
                    for k in range(kmin, kmax + 1):
                        m, sd = probs.get(k, (None, None))
                        row.append(f"{m:.6f}" if m is not None else "")
                        row.append(f"{sd:.6f}" if sd is not None else "")
            writer.writerow(row)

    # unique_board_count_nt_sym_mean.csv
    mean_path = out_dir / "unique_board_count_nt_sym_mean.csv"
    with mean_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["NT", "sym", "unique_mean", "unique_sd"]
        if args.normalize:
            header += ["unique_ratio_mean", "unique_ratio_sd"]
        writer.writerow(header)
        for t in tuples:
            for s in syms:
                vals = []
                ratio_vals = []
                for tr in train_seeds:
                    stats = per_train[tr].get((t, s), [])
                    uniq_mean, _uniq_sd, ratio_mean, _ratio_sd, _probs, _games = aggregate_eval_seeds(
                        stats, kmin, kmax
                    )
                    if uniq_mean is not None:
                        vals.append(uniq_mean)
                    if ratio_mean is not None:
                        ratio_vals.append(ratio_mean)
                m, sd = mean_sd(vals)
                row = [f"NT{t}", s, f"{m:.4f}" if m is not None else "", f"{sd:.4f}" if sd is not None else ""]
                if args.normalize:
                    rm, rsd = mean_sd(ratio_vals)
                    row += [f"{rm:.6f}" if rm is not None else "", f"{rsd:.6f}" if rsd is not None else ""]
                writer.writerow(row)

    print(f"saved: {unique_path}")
    print(f"saved: {max_tile_path}")
    print(f"saved: {mean_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

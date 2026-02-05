#!/usr/bin/env python3
import argparse
import csv
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCORE_RE = re.compile(r"score:\s*(\d+)")
NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")


def parse_scores(state_path: Path) -> List[int]:
    scores: List[int] = []
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("gameover_turn:"):
                m = SCORE_RE.search(line)
                if m:
                    scores.append(int(m.group(1)))
    return scores


def mean_sd(vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not vals:
        return None, None
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(max(var, 0.0))


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


def list_eval_seeds(run_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in run_dir.glob("seed*/NT*_*/*"):
        if not p.is_dir():
            continue
        es = parse_eval_seed_dir(p.name)
        if es is not None and es not in evals:
            evals.append(es)
    return sorted(evals)


def iter_state_paths(
    run_dir: Path, train_seed: int, eval_seed: int, tuples: List[str], syms: List[str]
) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    for t in tuples:
        for s in syms:
            key = f"NT{t}_{s}"
            base = run_dir / f"seed{train_seed}" / f"NT{t}_{s}"
            state = base / f"eval_seed{eval_seed}" / "state.txt"
            if not state.exists():
                # fallback to non-eval_seed layout
                state = base / "state.txt"
            paths[key] = state
    return paths


def build_rows(
    run_dir: Path,
    train_seeds: List[int],
    eval_seeds: List[int],
    tuples: List[str],
    syms: List[str],
    include_cell_sd: bool,
) -> Tuple[
    List[Dict[str, str]],
    List[str],
    Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]],
]:
    if include_cell_sd:
        cols = [f"NT{t}_{s}_mean" for t in tuples for s in syms] + [
            f"NT{t}_{s}_sd" for t in tuples for s in syms
        ]
    else:
        cols = [f"NT{t}_{s}" for t in tuples for s in syms]

    rows: List[Dict[str, str]] = []
    stats: Dict[Tuple[int, int, str, str], Tuple[Optional[float], Optional[float], int]] = {}
    for tr in train_seeds:
        for ev in eval_seeds:
            row: Dict[str, str] = {"train_seed": str(tr), "eval_seed": str(ev)}
            paths = iter_state_paths(run_dir, tr, ev, tuples, syms)
            for t in tuples:
                for s in syms:
                    key = f"NT{t}_{s}"
                    state = paths[key]
                    if not state.exists():
                        if include_cell_sd:
                            row[f"{key}_mean"] = ""
                            row[f"{key}_sd"] = ""
                        else:
                            row[key] = ""
                        stats[(tr, ev, t, s)] = (None, None, 0)
                        continue
                    scores = parse_scores(state)
                    if not scores:
                        if include_cell_sd:
                            row[f"{key}_mean"] = ""
                            row[f"{key}_sd"] = ""
                        else:
                            row[key] = ""
                        stats[(tr, ev, t, s)] = (None, None, 0)
                        continue
                    mean, sd = mean_sd(scores)
                    stats[(tr, ev, t, s)] = (mean, sd, len(scores))
                    if include_cell_sd:
                        row[f"{key}_mean"] = f"{mean:.4f}" if mean is not None else ""
                        row[f"{key}_sd"] = f"{sd:.4f}" if sd is not None else ""
                    else:
                        row[key] = f"{mean:.4f}" if mean is not None else ""
            rows.append(row)
    return rows, cols, stats


def summarize(rows: List[Dict[str, str]], cols: List[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    mean_row = {"train_seed": "mean", "eval_seed": ""}
    sd_row = {"train_seed": "sd", "eval_seed": ""}
    for c in cols:
        vals = [float(r[c]) for r in rows if r.get(c)]
        if not vals:
            mean_row[c] = ""
            sd_row[c] = ""
            continue
        m = sum(vals) / len(vals)
        if len(vals) >= 2:
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            sd = math.sqrt(max(var, 0.0))
        else:
            sd = 0.0
        mean_row[c] = f"{m:.4f}"
        sd_row[c] = f"{sd:.4f}"
    return mean_row, sd_row


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "train_seed×eval_seed の平均スコアをCSVに出力（board_dataのstate.txtから集計）"
        )
    )
    p.add_argument("--run-name", required=True)
    p.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
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
    p.add_argument("--output", default="", help="output csv path")
    p.add_argument(
        "--cell-sd",
        action="store_true",
        help="include per-cell SD columns (NT*_sym_mean + NT*_sym_sd)",
    )
    p.add_argument(
        "--long",
        action="store_true",
        help="also write long-format CSV (train_seed, eval_seed, tuple, sym, mean, sd, n_games)",
    )
    p.add_argument(
        "--output-long",
        default="",
        help="output long-format CSV path (implies --long)",
    )
    args = p.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    # train seeds
    train_seeds: List[int] = []
    if args.train_seeds:
        raw = args.train_seeds.replace(",", " ").split()
        train_seeds = [int(x) for x in raw if x.strip()]
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    # eval seeds
    eval_seeds: List[int] = []
    if args.eval_seeds:
        raw = args.eval_seeds.replace(",", " ").split()
        eval_seeds = [int(x) for x in raw if x.strip()]
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds = list(range(args.eval_seed_start, args.eval_seed_end + 1))
    else:
        eval_seeds = list_eval_seeds(run_dir)
        if not eval_seeds:
            # fallback: assume eval_seed == train_seed
            eval_seeds = train_seeds

    # tuples / syms
    if args.tuples:
        tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    else:
        tuples, _syms = list_tuple_sym(run_dir)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
    else:
        _tuples, syms = list_tuple_sym(run_dir)

    rows, cols, stats = build_rows(run_dir, train_seeds, eval_seeds, tuples, syms, args.cell_sd)
    mean_row, sd_row = summarize(rows, cols)

    output = (
        Path(args.output)
        if args.output
        else board_root
        / args.run_name
        / "score_train_eval_matrix.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["train_seed", "eval_seed"] + cols)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(mean_row)
        writer.writerow(sd_row)
    print(f"wrote: {output}")
    if args.output_long:
        args.long = True
    if args.long:
        long_output = (
            Path(args.output_long)
            if args.output_long
            else board_root / args.run_name / "score_train_eval_matrix_long.csv"
        )
        long_output.parent.mkdir(parents=True, exist_ok=True)
        with long_output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["train_seed", "eval_seed", "tuple", "sym", "mean", "sd", "n_games"])
            for tr in train_seeds:
                for ev in eval_seeds:
                    for t in tuples:
                        for s in syms:
                            mean, sd, n_games = stats.get((tr, ev, t, s), (None, None, 0))
                            writer.writerow(
                                [
                                    tr,
                                    ev,
                                    f"NT{t}",
                                    s,
                                    f"{mean:.4f}" if mean is not None else "",
                                    f"{sd:.4f}" if sd is not None else "",
                                    n_games,
                                ]
                            )
        print(f"wrote: {long_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from graph.common import PlayerData, tuple_label  # noqa: E402


GAME_RE = re.compile(r"game[^0-9]*([0-9]+)", re.IGNORECASE)


def parse_eval_games(path: Path) -> List[Tuple[int, List[Tuple[List[float], int]]]]:
    games: List[Tuple[int, List[Tuple[List[float], int]]]] = []
    cur: List[Tuple[List[float], int]] = []
    cur_game_id: Optional[int] = None

    def push():
        nonlocal cur, cur_game_id
        if cur:
            gid = cur_game_id if cur_game_id is not None else len(games) + 1
            games.append((gid, cur))
        cur = []
        cur_game_id = None

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            lower = s.lower()
            if lower.startswith("game") or lower.startswith("gameover_turn"):
                if cur:
                    push()
                m = GAME_RE.search(s)
                if m:
                    cur_game_id = int(m.group(1))
                continue
            parts = s.split()
            if len(parts) < 5:
                continue
            try:
                evals = list(map(float, parts[:4]))
                prg = int(float(parts[4]))
            except ValueError:
                continue
            cur.append((evals, prg))
    if cur:
        push()
    if not games and cur:
        games.append((1, cur))
    return games


def calc_rel_error(pp_evals: List[float], pr_evals: List[float]) -> float:
    valid = [ev for ev in pp_evals if ev > -1e5]
    if not valid:
        return 0.0
    bad_eval = min(valid)
    pp_idx = max(range(len(pp_evals)), key=lambda i: pp_evals[i])
    pr_idx = max(range(len(pr_evals)), key=lambda i: pr_evals[i])
    denom = pp_evals[pp_idx] - bad_eval
    if denom == 0:
        return 0.0
    sub = pp_evals[pr_idx] - pp_evals[pp_idx]
    return sub / denom


def list_train_seeds(run_dir: Path) -> List[int]:
    seeds: List[int] = []
    for p in run_dir.glob("seed*"):
        if p.is_dir() and p.name[4:].isdigit():
            seeds.append(int(p.name[4:]))
    return sorted(seeds)


def list_eval_seeds(nt_dir: Path) -> List[int]:
    evals: List[int] = []
    for p in nt_dir.glob("eval_seed*"):
        if p.is_dir() and p.name[9:].isdigit():
            evals.append(int(p.name[9:]))
    return sorted(evals)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="err-relが大きいprogressをゲームごとに上位抽出"
    )
    ap.add_argument("--run-name", required=True)
    ap.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data_v2",
        help="board_data root",
    )
    ap.add_argument("--train-seed-start", type=int, default=None)
    ap.add_argument("--train-seed-end", type=int, default=None)
    ap.add_argument("--train-seeds", default="", help="space/comma-separated train seeds")
    ap.add_argument("--eval-seed-start", type=int, default=None)
    ap.add_argument("--eval-seed-end", type=int, default=None)
    ap.add_argument("--eval-seeds", default="", help="space/comma-separated eval seeds")
    ap.add_argument("--tuples", default="", help="comma-separated tuples (default: auto)")
    ap.add_argument("--sym-list", default="", help="comma-separated sym list (default: auto)")
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--output", default="", help="output csv path")
    args = ap.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"ERROR: run_name dir not found: {run_dir}")

    # set BOARD_DATA_ROOT so PlayerData uses correct root
    os.environ["BOARD_DATA_ROOT"] = str(board_root)

    # train seeds
    if args.train_seeds:
        train_seeds = [int(x) for x in args.train_seeds.replace(",", " ").split() if x.strip()]
    elif args.train_seed_start is not None and args.train_seed_end is not None:
        train_seeds = list(range(args.train_seed_start, args.train_seed_end + 1))
    else:
        train_seeds = list_train_seeds(run_dir)

    # tuples/syms
    tuples: List[str] = []
    syms: List[str] = []
    if args.tuples:
        tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
    else:
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
        tuples = sorted(tuples, key=lambda x: int(x))
        syms = sorted(syms)
    if args.sym_list:
        syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]

    # eval seeds
    eval_seeds_fixed: Optional[List[int]] = None
    if args.eval_seeds:
        eval_seeds_fixed = [int(x) for x in args.eval_seeds.replace(",", " ").split() if x.strip()]
    elif args.eval_seed_start is not None and args.eval_seed_end is not None:
        eval_seeds_fixed = list(range(args.eval_seed_start, args.eval_seed_end + 1))

    out_path = (
        Path(args.output)
        if args.output
        else Path("/HDD/momiyama2/data/study/analysis_outputs_v2")
        / args.run_name
        / "err_rel_top_progress.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        import csv

        w = csv.writer(f)
        w.writerow(
            [
                "train_seed",
                "eval_seed",
                "tuple",
                "sym",
                "game_id",
                "rank",
                "progress",
                "rel_error",
                "abs_rel_error",
            ]
        )

        for tr in train_seeds:
            for t in tuples:
                for s in syms:
                    nt_dir = run_dir / f"seed{tr}" / f"NT{t}_{s}"
                    if not nt_dir.exists():
                        continue
                    if eval_seeds_fixed is not None:
                        eval_seeds = eval_seeds_fixed
                    else:
                        eval_seeds = list_eval_seeds(nt_dir)
                        if not eval_seeds:
                            eval_seeds = [None]
                    for ev in eval_seeds:
                        target = nt_dir if ev is None else nt_dir / f"eval_seed{ev}"
                        if not target.exists():
                            continue
                        pd = PlayerData(target, {})
                        try:
                            pp_path = pd.pp_eval_state
                            pr_path = pd.eval_file
                        except FileNotFoundError:
                            continue
                        pp_games = parse_eval_games(pp_path)
                        pr_games = parse_eval_games(pr_path)
                        game_n = min(len(pp_games), len(pr_games))
                        for i in range(game_n):
                            pp_gid, pp_steps = pp_games[i]
                            pr_gid, pr_steps = pr_games[i]
                            gid = pp_gid if pp_gid is not None else (pr_gid if pr_gid is not None else i + 1)
                            step_n = min(len(pp_steps), len(pr_steps))
                            best_by_prg: Dict[int, float] = {}
                            for j in range(step_n):
                                pp_evals, pp_prg = pp_steps[j]
                                pr_evals, _pr_prg = pr_steps[j]
                                rel = calc_rel_error(pp_evals, pr_evals)
                                prev = best_by_prg.get(pp_prg)
                                if prev is None or abs(rel) > abs(prev):
                                    best_by_prg[pp_prg] = rel
                            ranked = sorted(best_by_prg.items(), key=lambda x: abs(x[1]), reverse=True)
                            for rank, (prg, rel) in enumerate(ranked[: args.top_n], start=1):
                                w.writerow(
                                    [
                                        tr,
                                        "" if ev is None else ev,
                                        f"NT{tuple_label(pd, int(t))}",
                                        s,
                                        gid,
                                        rank,
                                        prg,
                                        f"{rel:.6f}",
                                        f"{abs(rel):.6f}",
                                    ]
                                )

    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import csv
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


SCORE_RE = re.compile(r"score:\s*(\d+)")
NT_DIR_RE = re.compile(r"^NT(?P<tuple>\d+)_(?P<sym>sym|notsym)$")
EVFILE_RE = re.compile(
    r"(?P<tuple>\d+)tuple_(?P<sym>sym|notsym)_data_(?P<seed>\d+)_(?P<stage>\d+)\.dat$"
)


def parse_scores(state_path: Path) -> List[int]:
    scores: List[int] = []
    with state_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("gameover_turn:"):
                m = SCORE_RE.search(line)
                if m:
                    scores.append(int(m.group(1)))
    return scores


def parse_seed(dir_name: str) -> Optional[int]:
    if not dir_name.startswith("seed"):
        return None
    try:
        return int(dir_name[4:])
    except ValueError:
        return None


def parse_tuple_sym_dirs(run_dir: Path) -> Tuple[List[str], List[str]]:
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


def parse_seeds_from_dat(run_dir: Path) -> List[int]:
    seeds: List[int] = []
    for p in run_dir.glob("seed*"):
        if p.is_dir():
            seed = parse_seed(p.name)
            if seed is not None:
                seeds.append(seed)
    return sorted(seeds)


def parse_seeds_from_board(run_dir: Path) -> List[int]:
    return parse_seeds_from_dat(run_dir)


def collect_dat_index(run_dir: Path, stage: int):
    tuples: List[str] = []
    syms: List[str] = []
    seeds: List[int] = []
    # map (seed, tuple, sym) -> evfile path
    index = {}
    for evfile in run_dir.glob("seed*/NT*_*/*.dat"):
        m = EVFILE_RE.match(evfile.name)
        if not m:
            continue
        if int(m.group("stage")) != stage:
            continue
        seed = int(m.group("seed"))
        t = m.group("tuple")
        s = m.group("sym")
        if t not in tuples:
            tuples.append(t)
        if s not in syms:
            syms.append(s)
        if seed not in seeds:
            seeds.append(seed)
        index[(seed, t, s)] = evfile
    tuples = sorted(tuples, key=lambda x: int(x))
    syms = sorted(syms)
    seeds = sorted(seeds)
    return tuples, syms, seeds, index


def calc_rows_from_board(run_dir: Path, tuples: List[str], syms: List[str]):
    rows = []
    seeds = parse_seeds_from_board(run_dir)
    for seed in seeds:
        row = {"seed": seed}
        for t in tuples:
            for s in syms:
                state = run_dir / f"seed{seed}" / f"NT{t}_{s}" / "state.txt"
                key = f"NT{t}_{s}"
                if not state.exists():
                    row[key] = ""
                    continue
                scores = parse_scores(state)
                if not scores:
                    row[key] = ""
                    continue
                mean = sum(scores) / len(scores)
                row[key] = f"{mean:.4f}"
        rows.append(row)
    return rows


def calc_rows_from_dat(
    dat_root: Path,
    run_name: str,
    tuples: List[str],
    syms: List[str],
    seeds: List[int],
    ev_index: dict,
    stage: int,
    game_count: int,
    single_stage: bool,
):
    run_dir = dat_root / run_name

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    base_nt = repo_root / "Mini-2048-data-processing-main" / "NT"
    play_nt = base_nt / "play_nt"
    play_nt_ns = base_nt / "play_nt_ns"

    if not play_nt.exists():
        subprocess.run(
            ["g++", "Play_NT_player.cpp", "-O3", "-std=c++20", "-o", "play_nt"],
            cwd=str(base_nt),
            check=True,
        )
    if not play_nt_ns.exists():
        subprocess.run(
            [
                "g++",
                "Play_NT_player.cpp",
                "-O3",
                "-std=c++20",
                "-DSINGLE_STAGE",
                "-o",
                "play_nt_ns",
            ],
            cwd=str(base_nt),
            check=True,
        )

    player_bin = play_nt_ns if single_stage else play_nt
    tmp_root = Path(tempfile.mkdtemp(prefix="nt_eval_"))
    tmp_run = "tmp_eval"

    rows = []
    try:
        for seed in seeds:
            row = {"seed": seed}
            for t in tuples:
                for s in syms:
                    key = f"NT{t}_{s}"
                    evfile = ev_index.get((seed, t, s))
                    if not evfile:
                        row[key] = ""
                        continue
                    args = [
                        str(player_bin),
                        str(seed),
                        str(game_count),
                        str(evfile),
                        s,
                        t,
                        "--run-name",
                        tmp_run,
                        "--board-root",
                        str(tmp_root),
                    ]
                    if single_stage:
                        args.append("--single-stage")
                    subprocess.run(args, check=True)

                    state = (
                        tmp_root
                        / tmp_run
                        / f"seed{seed}"
                        / f"NT{t}_{s}"
                        / "state.txt"
                    )
                    if not state.exists():
                        row[key] = ""
                        continue
                    scores = parse_scores(state)
                    if not scores:
                        row[key] = ""
                        continue
                    mean = sum(scores) / len(scores)
                    row[key] = f"{mean:.4f}"

                    data_dir = state.parent
                    if data_dir.exists():
                        shutil.rmtree(data_dir, ignore_errors=True)
            rows.append(row)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    return rows


def calc_mean_sd(rows: list, cols: List[str]):
    means = {"seed": "mean"}
    sds = {"seed": "sd"}
    for c in cols:
        vals = [float(r[c]) for r in rows if r.get(c)]
        if not vals:
            means[c] = ""
            sds[c] = ""
            continue
        m = sum(vals) / len(vals)
        if len(vals) >= 2:
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            sd = math.sqrt(max(var, 0.0))
        else:
            sd = 0.0
        means[c] = f"{m:.4f}"
        sds[c] = f"{sd:.4f}"
    return means, sds


def main() -> int:
    parser = argparse.ArgumentParser(
        description="seed×条件の平均/SD をCSVに集計する（board_data or dat 直実行）"
    )
    parser.add_argument("--run-name", required=True, help="run_name")
    parser.add_argument(
        "--mode",
        choices=["dat", "board"],
        default="dat",
        help="input mode: dat (default) or board",
    )
    parser.add_argument(
        "--dat-root",
        default="/HDD/momiyama2/data/study/ntuple_dat",
        help="ntuple_dat root (dat mode only)",
    )
    parser.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root (board mode / output path)",
    )
    parser.add_argument(
        "--ev-stages",
        default="",
        help="comma-separated stage list (dat mode, required)",
    )
    parser.add_argument(
        "--game-count",
        type=int,
        default=100,
        help="game count per eval (dat mode, default: 100)",
    )
    parser.add_argument(
        "--nostage",
        action="store_true",
        help="use single-stage (nostage) mode",
    )
    parser.add_argument(
        "--tuples",
        default="",
        help="comma-separated tuples (default: auto from directory)",
    )
    parser.add_argument(
        "--sym-list",
        default="",
        help="comma-separated sym list (default: auto from directory)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="output csv path (default: <board_root>/<run_name>/score_seed_matrix.csv)",
    )
    args = parser.parse_args()

    board_root = Path(args.board_root)
    run_dir_board = board_root / args.run_name

    if args.mode == "dat":
        if not args.ev_stages:
            raise SystemExit("ERROR: --ev-stages is required in dat mode.")
        stages = [s.strip() for s in args.ev_stages.split(",") if s.strip()]
        if len(stages) != 1:
            raise SystemExit("ERROR: --ev-stages must be a single stage in dat mode.")
        stage = int(stages[0])
        dat_root = Path(args.dat_root)
        run_dir_dat = dat_root / args.run_name
        auto_tuples, auto_syms, auto_seeds, ev_index = collect_dat_index(
            run_dir_dat, stage
        )
        tuples = (
            [t.strip() for t in args.tuples.split(",") if t.strip()]
            if args.tuples
            else auto_tuples
        )
        syms = (
            [s.strip() for s in args.sym_list.split(",") if s.strip()]
            if args.sym_list
            else auto_syms
        )
        seeds = auto_seeds
        rows = calc_rows_from_dat(
            dat_root,
            args.run_name,
            tuples,
            syms,
            seeds,
            ev_index,
            stage,
            args.game_count,
            args.nostage,
        )
    else:
        if args.tuples:
            tuples = [t.strip() for t in args.tuples.split(",") if t.strip()]
        else:
            tuples, _syms = parse_tuple_sym_dirs(run_dir_board)
        if args.sym_list:
            syms = [s.strip() for s in args.sym_list.split(",") if s.strip()]
        else:
            _tuples, syms = parse_tuple_sym_dirs(run_dir_board)
        rows = calc_rows_from_board(run_dir_board, tuples, syms)

    cols = [f"NT{t}_{s}" for t in tuples for s in syms]
    means, sds = calc_mean_sd(rows, cols)

    output = (
        Path(args.output)
        if args.output
        else run_dir_board / "score_seed_matrix.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["seed"] + cols)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(means)
        writer.writerow(sds)
    print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

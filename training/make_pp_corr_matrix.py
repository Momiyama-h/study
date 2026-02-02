#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np

try:
    from scipy.stats import spearmanr as scipy_spearmanr  # type: ignore
except Exception:
    scipy_spearmanr = None


def read_eval_values(path: Path) -> list[float]:
    text = path.read_text("utf-8")
    text = re.sub(r"game.*\n?", "", text)
    vals: list[float] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            vals.append(float(line.split()[0]))
        except ValueError:
            continue
    return vals


def read_eval_txt_max_values(path: Path) -> list[float]:
    text = path.read_text("utf-8")
    text = re.sub(r"game.*\n?", "", text)
    vals: list[float] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            evals = [float(parts[i]) for i in range(4)]
        except ValueError:
            continue
        vals.append(max(evals))
    return vals


def rankdata(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    uniq, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    for i, cnt in enumerate(counts):
        if cnt > 1:
            idx = np.where(inv == i)[0]
            ranks[idx] = ranks[idx].mean()
    return ranks


def spearman_corr(x: list[float], y: list[float]) -> tuple[float, float]:
    n = min(len(x), len(y))
    if n < 2:
        return math.nan, math.nan
    x = x[:n]
    y = y[:n]
    if scipy_spearmanr is not None:
        rho, p = scipy_spearmanr(x, y)
        return float(rho), float(p)
    rx = rankdata(np.asarray(x, dtype=float))
    ry = rankdata(np.asarray(y, dtype=float))
    if np.std(rx) == 0 or np.std(ry) == 0:
        return math.nan, math.nan
    rho = float(np.corrcoef(rx, ry)[0, 1])
    return rho, math.nan


def parse_tuple_sym(name: str) -> tuple[int, str, str] | None:
    m = re.match(r"^NT(\d+)([A-Za-z]*)_(sym|notsym)$", name)
    if not m:
        return None
    num = int(m.group(1))
    suffix = m.group(2)
    sym = m.group(3)
    label = f"NT{num}{suffix}_{sym}"
    return num, suffix, label


def safe_name(rel_path: Path) -> str:
    safe = str(rel_path).replace("\\", "/").strip("/")
    return safe.replace("/", "__")


def game_count_from_meta(meta_path: Path) -> int | None:
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text("utf-8"))
    except Exception:
        return None
    for key in ("game_count", "game_counts", "gamecount", "games"):
        if key in meta:
            try:
                return int(meta[key])
            except Exception:
                return None
    return None


def resolve_pp_eval(
    board_root: Path,
    target_dir: Path,
    eval_prefix: str,
    pp_local_name: str,
) -> Path | None:
    local_pp = target_dir / pp_local_name
    if local_pp.exists():
        return local_pp

    rel_path = target_dir.relative_to(board_root)
    game_count = game_count_from_meta(target_dir / "meta.json")
    seed = None
    for part in rel_path.parts:
        if part.startswith("seed"):
            try:
                seed = int(part[4:])
            except ValueError:
                seed = None
            break

    if game_count is not None and seed is not None:
        structured = (
            board_root
            / "PP"
            / f"game_counts{game_count}"
            / f"seed{seed}"
            / f"{eval_prefix}-{safe_name(rel_path)}.txt"
        )
        if structured.exists():
            return structured

    legacy = board_root / "PP" / f"{eval_prefix}-{safe_name(rel_path)}.txt"
    if legacy.exists():
        return legacy
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--board-root", default="/HDD/momiyama2/data/study/board_data")
    ap.add_argument("--tuples", default="", help="comma-separated tuple numbers (optional)")
    ap.add_argument("--sym-list", default="sym,notsym")
    ap.add_argument("--seed-start", type=int, default=None)
    ap.add_argument("--seed-end", type=int, default=None)
    ap.add_argument(
        "--eval-kind",
        choices=("after", "state", "eval"),
        default="after",
        help="use eval-after-state (after), eval-state (state), or eval.txt max (eval)",
    )
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    board_root = Path(args.board_root)
    run_dir = board_root / args.run_name
    if not run_dir.exists():
        raise SystemExit(f"run_name not found: {run_dir}")

    if args.eval_kind == "after":
        nt_eval_name = "eval-after-state.txt"
        nt_eval_mode = "after"
        pp_eval_prefix = "eval-after-state"
        pp_local_name = "pp-eval-after-state.txt"
        suffix = "after"
    elif args.eval_kind == "state":
        nt_eval_name = "eval-state.txt"
        nt_eval_mode = "state"
        pp_eval_prefix = "eval-state"
        pp_local_name = "pp-eval-state.txt"
        suffix = "state"
    else:
        nt_eval_name = "eval.txt"
        nt_eval_mode = "eval"
        pp_eval_prefix = "eval-after-state"
        pp_local_name = "pp-eval-after-state.txt"
        suffix = "evaltxt"

    tuple_filter = set()
    if args.tuples:
        for t in args.tuples.split(","):
            t = t.strip()
            if not t:
                continue
            tuple_filter.add(int(t))

    sym_list = [s.strip() for s in args.sym_list.split(",") if s.strip()]

    seeds: list[int] = []
    if args.seed_start is not None and args.seed_end is not None:
        seeds = list(range(args.seed_start, args.seed_end + 1))
    else:
        for p in run_dir.glob("seed*"):
            if p.is_dir() and p.name.startswith("seed"):
                try:
                    seeds.append(int(p.name[4:]))
                except ValueError:
                    continue
        seeds = sorted(seeds)

    # collect condition list
    conds: list[tuple[int, str, str]] = []
    cond_set = set()
    for seed in seeds:
        seed_dir = run_dir / f"seed{seed}"
        if not seed_dir.exists():
            continue
        for nt_dir in seed_dir.glob("NT*_*"):
            if not nt_dir.is_dir():
                continue
            parsed = parse_tuple_sym(nt_dir.name)
            if parsed is None:
                continue
            num, suffix_txt, label = parsed
            if tuple_filter and num not in tuple_filter:
                continue
            if label.split("_", 1)[1] not in sym_list:
                continue
            if label not in cond_set:
                cond_set.add(label)
                conds.append((num, suffix_txt, label))
    conds.sort(key=lambda x: (x[0], x[1], x[2]))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = (
            Path("/HDD/momiyama2/data/study/analysis_outputs")
            / args.run_name
            / "pp_corr"
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"pp_corr_spearman_{suffix}.csv"

    header = ["seed"]
    for _, _, label in conds:
        header.append(f"{label}_rho")
        header.append(f"{label}_p")

    if scipy_spearmanr is None:
        print("WARNING: scipy not available; p-value will be NaN", flush=True)

    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for seed in seeds:
            row: list[object] = [seed]
            seed_dir = run_dir / f"seed{seed}"
            for _, _, label in conds:
                nt_dir = seed_dir / label
                nt_eval_path = nt_dir / nt_eval_name
                pp_eval_path = None
                if nt_dir.exists():
                    pp_eval_path = resolve_pp_eval(
                        board_root, nt_dir, pp_eval_prefix, pp_local_name
                    )
                if not nt_eval_path.exists() or pp_eval_path is None:
                    row.extend([math.nan, math.nan])
                    continue
                if nt_eval_mode == "eval":
                    nt_vals = read_eval_txt_max_values(nt_eval_path)
                else:
                    nt_vals = read_eval_values(nt_eval_path)
                pp_vals = read_eval_values(pp_eval_path)
                rho, p = spearman_corr(pp_vals, nt_vals)
                row.extend([rho, p])
            w.writerow(row)

    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

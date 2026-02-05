#!/usr/bin/env python3
import os
import argparse
import glob
import csv
from collections import Counter, defaultdict


def parse_file(path: str):
    max_list = []
    cur_max = -1
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("gameover_turn"):
                if cur_max >= 0:
                    max_list.append(cur_max)
                cur_max = -1
                continue
            vals = list(map(int, line.split()))
            if vals:
                cur_max = max(cur_max, max(vals))
    return max_list


def main():
    ap = argparse.ArgumentParser(
        description="Aggregate max tile probabilities by NT and sym/notsym from state.txt"
    )
    ap.add_argument("--run-name", required=True, help="run_name under board_data")
    ap.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root",
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help="output dir (default: analysis_outputs/<run_name>/tile_stats)",
    )
    args = ap.parse_args()

    files = glob.glob(
        os.path.join(args.board_root, args.run_name, "seed*", "NT*_*/state.txt")
    )
    files += glob.glob(
        os.path.join(args.board_root, args.run_name, "seed*", "NT*_*/eval_seed*/state.txt")
    )
    if not files:
        raise SystemExit("no state.txt found")

    groups = defaultdict(list)  # (NT, sym) -> max_list
    for f in files:
        dir_path = os.path.dirname(f)
        base = os.path.basename(dir_path)
        if base.startswith("eval_seed"):
            nt_sym = os.path.basename(os.path.dirname(dir_path))
        else:
            nt_sym = base
        parts = nt_sym.split("_", 1)
        if len(parts) != 2:
            continue
        nt, sym = parts
        groups[(nt, sym)].extend(parse_file(f))

    all_vals = [v for vs in groups.values() for v in vs]
    if not all_vals:
        raise SystemExit("no games parsed")
    kmin, kmax = min(all_vals), max(all_vals)

    out_dir = args.out_dir
    if not out_dir:
        out_dir = os.path.join(
            "/HDD/momiyama2/data/study/analysis_outputs",
            args.run_name,
            "tile_stats",
        )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tile_prob_by_nt_sym.csv")

    with open(out_path, "w", newline="") as fw:
        w = csv.writer(fw)
        header = ["NT", "sym", "games"] + [
            f"p_max_2^{k}" for k in range(kmin, kmax + 1)
        ]
        w.writerow(header)
        for (nt, sym) in sorted(groups.keys()):
            vals = groups[(nt, sym)]
            total = len(vals)
            cnt = Counter(vals)
            row = [nt, sym, total] + [cnt.get(k, 0) / total for k in range(kmin, kmax + 1)]
            w.writerow(row)

    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()

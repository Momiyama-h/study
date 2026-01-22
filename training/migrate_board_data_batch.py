#!/usr/bin/env python3
import argparse
import re
import shutil
from pathlib import Path


def load_map(path: Path) -> list[tuple[str, re.Pattern]]:
    items: list[tuple[str, re.Pattern]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid map line (need: run_name regex): {line}")
        run_name, regex = parts
        items.append((run_name, re.compile(regex)))
    if not items:
        raise ValueError("Map file is empty.")
    return items


def match_run_name(name: str, rules: list[tuple[str, re.Pattern]]) -> str | None:
    for run_name, pattern in rules:
        if pattern.search(name):
            return run_name
    return None


def move_board_data(board_root: Path, rules: list[tuple[str, re.Pattern]], dry_run: bool) -> int:
    pattern = re.compile(r"_([46])(sym|notsym)_seed(\d+)_g")
    moved = 0
    for parent in board_root.iterdir():
        if not parent.is_dir():
            continue
        if parent.name == "PP":
            continue
        run_name = match_run_name(parent.name, rules)
        if not run_name:
            continue
        m = pattern.search(parent.name)
        if not m:
            continue
        tuple_num, sym, seed = m.groups()
        src = parent / f"NT{tuple_num}_{sym}"
        if not src.is_dir():
            continue
        dst = board_root / run_name / f"seed{seed}" / f"NT{tuple_num}_{sym}"
        if dst.exists() and any(dst.iterdir()):
            print(f"SKIP (dest not empty): {dst}")
            continue
        print(f"{src} -> {dst}")
        if dry_run:
            moved += 1
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.move(str(item), dst / item.name)
        if not any(src.iterdir()):
            src.rmdir()
        if not any(parent.iterdir()):
            parent.rmdir()
        moved += 1
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy board_data layout into run_name/seed/NT*_* layout."
    )
    parser.add_argument(
        "--board-root",
        default="/HDD/momiyama2/data/study/board_data",
        help="board_data root directory",
    )
    parser.add_argument(
        "--map",
        required=True,
        help="Mapping file: <run_name> <regex> per line",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print moves without changing files",
    )
    args = parser.parse_args()

    board_root = Path(args.board_root)
    if not board_root.exists():
        raise SystemExit(f"board_root not found: {board_root}")

    rules = load_map(Path(args.map))
    moved = move_board_data(board_root, rules, args.dry_run)
    print(f"Done. moved={moved} (dry_run={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

EVFILE_RE = re.compile(
    r"(?P<tuple>\d+)tuple_(?P<sym>sym|notsym)_data_(?P<seed>\d+)_(?P<stage>\d+)\.dat"
)


def make_safe_name(path_str: str) -> str:
    safe = path_str.replace("\\", "/").strip("/")
    return safe.replace("/", "__")


def parse_evfile(evfile: str) -> dict:
    name = Path(evfile).name
    match = EVFILE_RE.search(name)
    if not match:
        raise ValueError(f"evfile名が想定と一致しません: {name}")
    data = match.groupdict()
    return {
        "tuple": int(data["tuple"]),
        "sym": data["sym"],
        "seed": int(data["seed"]),
        "stage": int(data["stage"]),
        "evfile": name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="evfile名からmeta.jsonを作成するユーティリティ",
    )
    parser.add_argument("data_dir", type=str, help="データディレクトリ")
    parser.add_argument("evfile", type=str, help="evfileパス or ファイル名")
    parser.add_argument(
        "--board-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "board_data"),
        help="board_dataの基点ディレクトリ",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="meta.jsonが存在する場合に上書きする",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    board_dir = Path(args.board_dir).resolve()
    meta = parse_evfile(args.evfile)

    try:
        rel = data_dir.relative_to(board_dir)
        rel_str = str(rel)
        meta["relpath"] = rel_str
        meta["id"] = make_safe_name(rel_str)
    except ValueError:
        meta["relpath"] = str(data_dir)
        meta["id"] = make_safe_name(data_dir.name)

    meta_path = data_dir / "meta.json"
    if meta_path.exists() and not args.force:
        raise FileExistsError(f"{meta_path} が存在します。--forceで上書きできます。")

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
    print(f"wrote: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    parser.add_argument(
        "--game-count",
        type=int,
        default=None,
        help="評価ゲーム数（meta.jsonに記録）",
    )
    parser.add_argument(
        "--tuple-label",
        type=str,
        default=None,
        help="tuple表示用ラベル（例: 4a, 4b, 4, 5, 6）",
    )
    parser.add_argument(
        "--eval-seed",
        type=int,
        default=None,
        help="評価用seed（未指定ならディレクトリ名/seedから推定）",
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
    if args.game_count is not None:
        meta["game_count"] = int(args.game_count)
    if args.tuple_label is not None and args.tuple_label != "":
        meta["tuple_label"] = str(args.tuple_label)

    # train/eval seed handling
    meta["train_seed"] = meta.get("seed")
    eval_seed = args.eval_seed
    if eval_seed is None:
        # try to infer from relpath (eval_seedN)
        try:
            parts = rel_str.split("/")
        except Exception:
            parts = []
        for part in parts:
            if part.startswith("eval_seed"):
                try:
                    eval_seed = int(part.replace("eval_seed", ""))
                    break
                except ValueError:
                    pass
    if eval_seed is None and meta.get("seed") is not None:
        eval_seed = int(meta["seed"])
    if eval_seed is not None:
        meta["eval_seed"] = eval_seed

    meta_path = data_dir / "meta.json"
    if meta_path.exists() and not args.force:
        raise FileExistsError(f"{meta_path} が存在します。--forceで上書きできます。")

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
    print(f"wrote: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

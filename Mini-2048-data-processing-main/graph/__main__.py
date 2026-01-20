import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt

from . import (
    accuracy,
    boxplot,
    error_abs,
    error_rel,
    histgram,
    scatter,
    survival,
    survival_diff,
    acc_diff,
    scatter_v2,
    evals,
    progress_eval_accuracy,
)
from .common import PlayerData, board_dir, BASE_DIR, make_safe_name
__version__ = "1.5.0"


def read_config(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def write_config(path: Path, config: dict) -> None:
    path.write_text(json.dumps(config, indent=4, ensure_ascii=False), "utf-8")


def discover_data_dirs(root: Path, recursive: bool) -> list[Path]:
    if not root.exists():
        return []
    if recursive:
        eval_files = root.rglob("eval.txt")
        dirs = {p.parent for p in eval_files}
        return sorted(dirs, key=lambda p: str(p))
    return [d for d in root.iterdir() if d.is_dir()]


def get_config(board_data_dirs: list[Path]):
    if config_path.exists():
        config = read_config(config_path)
        for d in board_data_dirs:
            rel = d.relative_to(board_dir)
            key = make_safe_name(rel)
            if key not in config:
                config[key] = {
                    "label": str(rel),
                    "color": None,
                    "linestyle": "solid",
                    "order": 0,
                }
        # orderを追記したのでorder keyが存在しない場合
        for d in config.values():
            if "order" not in d:
                d["order"] = 0
    else:
        config = {
            make_safe_name(d.relative_to(board_dir)): {
                "label": str(d.relative_to(board_dir)),
                "color": None,
                "linestyle": "solid",
            }
            for d in board_data_dirs
        }

    write_config(config_path, config)
    return config


def normalize_sym(value):
    if isinstance(value, bool):
        return "sym" if value else "notsym"
    if isinstance(value, str):
        return value.lower()
    return None


def matches_meta(pd: PlayerData) -> bool:
    if not (args.seed or args.stage or args.tuple or args.sym):
        return True
    meta = pd.meta
    if not meta:
        return False

    def as_int(value):
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if args.seed and as_int(meta.get("seed")) not in args.seed:
        return False
    if args.stage and as_int(meta.get("stage")) not in args.stage:
        return False
    if args.tuple and as_int(meta.get("tuple")) not in args.tuple:
        return False
    if args.sym and normalize_sym(meta.get("sym")) != args.sym:
        return False
    return True


def get_files(config: dict, board_data_dirs: list[Path]) -> list[PlayerData]:
    is_include_PP = args.graph in (
        "surv",
        "surv-diff",
        "histgram",
        "evals",
        "boxplot-eval",
    )

    data = []
    for d in board_data_dirs:
        rel = d.relative_to(board_dir)
        rel_str = str(rel)
        if not re.search(intersection_match, rel_str):
            continue
        if re.search(exclude_match, rel_str):
            continue
        if not is_include_PP and rel.parts and rel.parts[0] == "PP":
            continue
        pd = PlayerData(d, config)
        if not matches_meta(pd):
            continue
        data.append(pd)
    print(f"対象のディレクトリ数: {len(data)}")
    # dataをPlayerData.configのorderでソート
    data.sort(key=lambda pd: pd.config.get("order", 0))
    return data


arg_parser = argparse.ArgumentParser(
    prog="graph",
    usage="uv run python -m %(prog)s [options]",
    description="指定したオプションに応じてグラフを描画するプログラム。詳細はREADME.mdを参照。",
)
arg_parser.add_argument(
    "graph",
    choices=[
        "acc",
        "acc-diff",
        "err-rel",
        "err-abs",
        "surv",
        "surv-diff",
        "scatter",
        "scatter_v2",
        "histgram",
        "evals",
        "boxplot-eval",
        "pea",
    ],
    help="実行するグラフを指定する。",
)
arg_parser.add_argument(
    "--output",
    "-o",
    type=str,
    help="出力先を指定する。",
)
file_group = arg_parser.add_mutually_exclusive_group()
file_group.add_argument(
    "--exclude",
    nargs="+",
    default=[],
    help="除外するディレクトリ名を指定する。",
)
file_group.add_argument(
    "--intersection",
    nargs="+",
    default=[],
    help="対象を指定したディレクトリのみに絞る。",
)
arg_parser.add_argument(
    "--config",
    type=str,
    help="設定ファイルのパスを指定する。現在は未使用。",
)
arg_parser.add_argument(
    "--is-show",
    action="store_true",
    help="グラフ作成完了時に表示する。",
)
arg_parser.add_argument(
    "--recursive",
    action="store_true",
    help="board_data配下を再帰的に探索する。",
)
arg_parser.add_argument(
    "--seed",
    nargs="+",
    type=int,
    help="meta.jsonのseedで絞り込む。",
)
arg_parser.add_argument(
    "--stage",
    nargs="+",
    type=int,
    help="meta.jsonのstageで絞り込む。",
)
arg_parser.add_argument(
    "--tuple",
    nargs="+",
    type=int,
    help="meta.jsonのtupleで絞り込む。",
)
arg_parser.add_argument(
    "--sym",
    choices=["sym", "notsym"],
    help="meta.jsonのsymで絞り込む。",
)
boxplot_group = arg_parser.add_mutually_exclusive_group()
boxplot_group.add_argument(
    "--min-progress",
    type=int,
    default=1,
    help="箱ひげ図の最小progress値を指定する（boxplot系のみ）。",
)
boxplot_group.add_argument(
    "--max-progress",
    type=int,
    default=250,
    help="箱ひげ図の最大progress値を指定する（boxplot系のみ）。",
)
boxplot_group.add_argument(
    "--bin-width",
    type=int,
    default=10,
    help="箱ひげ図のビン幅を指定する（boxplot系のみ）。",
)
arg_parser.add_argument(
    "--version",
    "-v",
    action="version",
    version=f"""
    %(prog)s version {__version__}
""",
)

args = arg_parser.parse_args()
exclude_match = re.compile("|".join(args.exclude + ["sample"]))
intersection_match = re.compile("|".join(args.intersection))
board_data_dirs = discover_data_dirs(board_dir, args.recursive)
output_dir = BASE_DIR.parent / "output"
output_dir.mkdir(exist_ok=True)

config_path = BASE_DIR / "config.json"
config = get_config(board_data_dirs)
player_data_list = get_files(config, board_data_dirs)

if args.graph == "acc":
    output_name = args.output if args.output else "accuracy.pdf"

    result = accuracy.calc_accuracy_data(
        player_data_list=player_data_list,
    )
elif args.graph == "acc-diff":
    output_name = args.output if args.output else "acc-diff.pdf"

    result = acc_diff.acc_diff_plot(
        player_data_list=player_data_list,
    )
elif args.graph == "err-rel":
    output_name = args.output if args.output else "error_rel.pdf"

    result = error_rel.calc_rel_error_data(
        player_data_list=player_data_list,
    )
elif args.graph == "err-abs":
    output_name = args.output if args.output else "error_abs.pdf"

    result = error_abs.calc_abs_error_data(
        player_data_list=player_data_list,
    )
elif args.graph == "surv":
    output_name = args.output if args.output else "survival.pdf"

    result = survival.calc_survival_rate_data(
        player_data_list=player_data_list,
    )
elif args.graph == "surv-diff":
    output_name = args.output if args.output else "survival-diff.pdf"

    result = survival_diff.calc_survival_diff_rate_data(
        player_data_list=player_data_list,
    )
elif args.graph == "histgram":
    output_name = args.output if args.output else "histgram.pdf"

    result = histgram.plot_histgram(
        player_data_list=player_data_list,
        output=output_dir / output_name,
        is_show=args.is_show,
    )
elif args.graph == "scatter":
    output_name = args.output if args.output else "scatter.pdf"

    result = scatter.plot_scatter(
        player_data_list=player_data_list,
        output=output_dir / output_name,
        is_show=args.is_show,
    )
elif args.graph == "scatter_v2":
    output_name = args.output if args.output else "scatter.pdf"

    result = scatter_v2.plot_scatter(
        player_data_list=player_data_list,
        output=output_dir / output_name,
        is_show=args.is_show,
    )
elif args.graph == "evals":
    output_name = args.output if args.output else "evals.pdf"

    result = evals.calc_eval_data(
        player_data_list=player_data_list,
        output=output_dir / output_name,
        is_show=args.is_show,
    )
elif args.graph == "boxplot-eval":
    output_name = args.output if args.output else "boxplot_eval.pdf"

    result = boxplot.plot_boxplot_eval_ratios(
        player_data_list=player_data_list,
        output=output_dir / output_name,
        is_show=args.is_show,
        min_progress=args.min_progress,
        max_progress=args.max_progress,
        bin_width=args.bin_width,
    )
elif args.graph == "pea":
    output_name = args.output if args.output else "boxplot_pea.pdf"

    result = progress_eval_accuracy.create_progress_eval_accuracy_plot(
        player_data_list=player_data_list,
        pp_eval_file=board_dir / "PP" / "eval.txt",
        output=output_dir / output_name,
        is_show=args.is_show,
        min_progress=args.min_progress,
        max_progress=args.max_progress,
        bin_width=args.bin_width,
    )

if result:
    for k, v in result.data.items():
        k_config = config.get(k, {})
        if "order" in k_config:
            del k_config["order"]
        plt.plot(v.x, v.y, **k_config)
    handles, labels = plt.gca().get_legend_handles_labels()
    sorted_pairs = sorted(zip(labels, handles), key=lambda x: x[0])
    labels, handles = zip(*sorted_pairs)

    plt.xlabel(result.x_label)
    plt.ylabel(result.y_label)
    plt.legend(handles, labels)  # ソート後の順番で凡例を設定
    plt.tight_layout()  # 追加：はみ出しを防ぐ
    plt.savefig(output_dir / output_name)
    if args.is_show:
        plt.show()

from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import random
import numpy as np
from .common import (
    get_eval_and_hand_progress,
    PlayerData,
    GraphData,
    PlotData,
    moving_average,
    tuple_sym_stage,
)


def calc_eval_data(
    player_data_list: list[PlayerData],
    output: Path,
    is_show: bool = True,
):
    # 各プレイヤータイプに対して一度だけラベルを使用するために追跡する辞書
    used_labels = {}

    for i, pd in enumerate(player_data_list):
        pr_eval_and_hand_progress = get_eval_and_hand_progress(pd.eval_file)
        abs_err_dict = defaultdict(list)

        pr_eval_and_hand_progress = random.sample(pr_eval_and_hand_progress, 1000)
        for pr_eval in pr_eval_and_hand_progress:
            abs_err_dict[pr_eval.prg].append(pr_eval.evals[pr_eval.idx[0]])
        for key, value in abs_err_dict.items():
            # 散布図の設定を作成
            scatter_params = pd.config.copy()
            scatter_params["color"] = (
                scatter_params["color"] if scatter_params["color"] else f"C{i % 10}"
            )
            # 初めて出現したプレイヤータイプでない場合はラベルを非表示に
            if pd.name in used_labels:
                scatter_params["label"] = "_nolegend_"  # これで凡例に表示されなくなる
            else:
                used_labels[pd.name] = True

            plt.scatter(
                [key] * len(value),
                value,
                s=5,
                alpha=0.5,
                color=scatter_params["color"],
                label=scatter_params.get("label", pd.name),
            )
    # グリッドを追加
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.xlabel("progress")
    plt.ylabel("player")
    plt.legend()
    plt.tight_layout()  # 追加：はみ出しを防ぐ

    save_path = output.with_stem(f"{output.stem}")
    plt.savefig(save_path)
    print(f"{save_path} saved.")
    if is_show:
        plt.show()
    plt.close()
    return None


def _calc_eval_curve(player_data: PlayerData) -> GraphData:
    pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)
    eval_dict = defaultdict(list)
    for pr_eval in pr_eval_and_hand_progress:
        eval_dict[pr_eval.prg].append(pr_eval.evals[pr_eval.idx[0]])
    eval_mean = {
        prg: np.mean(vals)
        for prg, vals in sorted(eval_dict.items(), key=lambda x: x[0])
    }
    return GraphData(
        x=moving_average(list(eval_mean.keys()), 5).tolist(),
        y=moving_average(list(eval_mean.values()), 5).tolist(),
    )


def calc_eval_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    grouped: dict[tuple[int, str, int | None], list[GraphData]] = defaultdict(list)
    for player_data in player_data_list:
        info = tuple_sym_stage(player_data)
        if info is None:
            continue
        grouped[info].append(_calc_eval_curve(player_data))

    result = PlotData(
        x_label="progress",
        y_label="eval mean",
        data={},
    )
    for (tuple_v, sym, stage), curves in grouped.items():
        if not curves:
            continue
        min_len = min(len(c.x) for c in curves)
        if min_len == 0:
            continue
        xs = [np.mean([c.x[i] for c in curves]) for i in range(min_len)]
        ys = [np.mean([c.y[i] for c in curves]) for i in range(min_len)]
        label = f"NT{tuple_v}_{sym}_mean"
        if stage is not None:
            label += f"_st{stage}"
        result.data[label] = GraphData(x=xs, y=ys)
    return result

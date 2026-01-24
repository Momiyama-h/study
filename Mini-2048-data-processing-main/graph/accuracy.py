from collections import defaultdict
from pathlib import Path

import numpy as np

from .common import (
    EvalAndHandProgress,
    GraphData,
    PlotData,
    get_eval_and_hand_progress,
    moving_average,
    PlayerData,
    tuple_sym_stage,
)


def calc_accuracy(
    pp_ehp: EvalAndHandProgress,
    pr_ehp: EvalAndHandProgress,
):
    pp_best_moves = set(pp_ehp.idx)
    pr_best_moves = set(pr_ehp.idx)

    # playerの最善手のうち、perfect playerの最善手と一致するものの数
    common_moves = pp_best_moves.intersection(pr_best_moves)

    # プレイヤーの最善手総数で割る
    return len(common_moves) / len(pr_ehp.idx)


def _calc_accuracy_curve(player_data: PlayerData) -> GraphData:
    pp_eval_and_hand_progress = get_eval_and_hand_progress(
        player_data.pp_eval_state
    )
    pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

    assert len(pp_eval_and_hand_progress) == len(
        pr_eval_and_hand_progress
    ), f"データ数が異なります。{len(pp_eval_and_hand_progress)=}, {len(pr_eval_and_hand_progress)=}"

    acc_dict = defaultdict(list)

    for pp_eval, pr_eval in zip(
        pp_eval_and_hand_progress, pr_eval_and_hand_progress
    ):
        acc_dict[pp_eval.prg].append(calc_accuracy(pp_eval, pr_eval))
    # 平均を取る
    acc = {
        prg: np.mean(err_list)
        for prg, err_list in sorted(acc_dict.items(), key=lambda x: x[0])
    }
    return GraphData(
        x=moving_average(list(acc.keys()), 10).tolist(),
        y=moving_average(list(acc.values()), 10).tolist(),
    )


def calc_accuracy_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    最善手率をプロットする。
    """
    result = PlotData(
        x_label="progress",
        y_label="accuracy",
        data={pd.name: None for pd in player_data_list},
    )
    for player_data in player_data_list:
        result.data[player_data.name] = _calc_accuracy_curve(player_data)
    return result


def calc_accuracy_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    seedごとの平均曲線をさらに平均してプロットする。
    """
    grouped: dict[tuple[int, str, int | None], list[GraphData]] = defaultdict(list)
    for player_data in player_data_list:
        info = tuple_sym_stage(player_data)
        if info is None:
            continue
        grouped[info].append(_calc_accuracy_curve(player_data))

    result = PlotData(
        x_label="progress",
        y_label="accuracy_mean",
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

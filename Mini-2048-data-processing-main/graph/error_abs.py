from collections import defaultdict
from pathlib import Path

import numpy as np

from .common import (
    GraphData,
    PlotData,
    get_eval_and_hand_progress,
    moving_average,
    PlayerData,
    tuple_sym_stage,
)


def calc_abs_error_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    絶対誤差をプロットする。
    """
    result = PlotData(
        x_label="progress",
        y_label="rel error",
        data={pd.name: "" for pd in player_data_list},
    )
    for player_data in player_data_list:
        pp_eval_and_hand_progress = get_eval_and_hand_progress(
            player_data.pp_eval_state
        )
        pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

        assert len(pp_eval_and_hand_progress) == len(
            pr_eval_and_hand_progress
        ), f"データ数が異なります。{len(pp_eval_and_hand_progress)=}, {len(pr_eval_and_hand_progress)=}"

        abs_err_dict = defaultdict(list)

        for pp_eval, pr_eval in zip(
            pp_eval_and_hand_progress, pr_eval_and_hand_progress
        ):
            abs_err_dict[pp_eval.prg].append(
                pp_eval.evals[pr_eval.idx[0]] - pp_eval.evals[pp_eval.idx[0]]
            )
        # 平均を取る
        abs_err = {
            prg: np.mean(err_list)
            for prg, err_list in sorted(abs_err_dict.items(), key=lambda x: x[0])
        }
        result.data[player_data.name] = GraphData(
            x=moving_average(list(abs_err.keys()), 5).tolist(),
            y=moving_average(list(abs_err.values()), 5).tolist(),
        )
    return result


def _calc_abs_error_curve(player_data: PlayerData) -> GraphData:
    pp_eval_and_hand_progress = get_eval_and_hand_progress(
        player_data.pp_eval_state
    )
    pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

    assert len(pp_eval_and_hand_progress) == len(
        pr_eval_and_hand_progress
    ), f"データ数が異なります。{len(pp_eval_and_hand_progress)=}, {len(pr_eval_and_hand_progress)=}"

    abs_err_dict = defaultdict(list)
    for pp_eval, pr_eval in zip(
        pp_eval_and_hand_progress, pr_eval_and_hand_progress
    ):
        abs_err_dict[pp_eval.prg].append(
            pp_eval.evals[pr_eval.idx[0]] - pp_eval.evals[pp_eval.idx[0]]
        )
    abs_err = {
        prg: np.mean(err_list)
        for prg, err_list in sorted(abs_err_dict.items(), key=lambda x: x[0])
    }
    return GraphData(
        x=moving_average(list(abs_err.keys()), 5).tolist(),
        y=moving_average(list(abs_err.values()), 5).tolist(),
    )


def calc_abs_error_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    grouped: dict[tuple[int, str, int | None], list[GraphData]] = defaultdict(list)
    for player_data in player_data_list:
        info = tuple_sym_stage(player_data)
        if info is None:
            continue
        grouped[info].append(_calc_abs_error_curve(player_data))

    result = PlotData(
        x_label="progress",
        y_label="abs error mean",
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

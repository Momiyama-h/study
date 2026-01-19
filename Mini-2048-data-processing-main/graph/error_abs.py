from collections import defaultdict
from pathlib import Path

import numpy as np

from .common import (
    GraphData,
    PlotData,
    get_eval_and_hand_progress,
    moving_average,
    PlayerData,
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

import re
from collections import Counter
from pathlib import Path

import numpy as np

from .common import GraphData, PlotData, PlayerData, tuple_sym_stage


def calc_survival_diff_rate_data(
    player_data_list: list[PlayerData],
):
    """
    パーフェクトプレイヤとの生存率の差をプロットする。
    """

    pp_state_file = Path("board_data/PP/state.txt")
    text = pp_state_file.read_text()
    progress_text = re.findall(r"progress: (\d+)", text)
    progresses = [int(progress) for progress in progress_text]

    droped_counter = Counter(progresses)
    max_value = len(progresses)
    pp_survival_rate = []

    result = PlotData(
        x_label="progress",
        y_label="difference in survival rate for PP",
        data={pd.name: None for pd in player_data_list},
    )

    for i in range(max(progresses) + 10):
        max_value -= droped_counter[i]
        pp_survival_rate.append(max_value / len(progresses))
    # 上でパーフェクトプレイヤの生存率を計算したので、差を計算する

    for pd in player_data_list:
        state_file = pd.state_file
        if state_file == pp_state_file:
            continue
        text = state_file.read_text()
        progress_text = re.findall(r"progress: (\d+)", text)
        progresses = [int(progress) for progress in progress_text]

        droped_counter = Counter(progresses)
        max_value = len(progresses)
        diff_survival_rate = []

        for i in range(max(progresses) + 10):
            max_value -= droped_counter[i]
            diff_survival_rate.append(
                abs(max_value / len(progresses) - pp_survival_rate[i])
            )

        result.data[pd.name] = GraphData(
            x=list(range(len(diff_survival_rate))),
            y=diff_survival_rate,
        )
    return result


def _calc_pp_survival_rate():
    pp_state_file = Path("board_data/PP/state.txt")
    text = pp_state_file.read_text()
    # progress_text = re.findall(r"progress: (\\d+)", text)
    progress_text = re.findall(r"progress: (\d+)", text)
    progresses = [int(progress) for progress in progress_text]

    droped_counter = Counter(progresses)
    max_value = len(progresses)
    pp_survival_rate = []
    for i in range(max(progresses) + 10):
        max_value -= droped_counter[i]
        pp_survival_rate.append(max_value / len(progresses))
    return pp_survival_rate


def _calc_survival_diff_curve(pd: PlayerData, pp_survival_rate: list[float]) -> GraphData:
    state_file = pd.state_file
    text = state_file.read_text()
    # progress_text = re.findall(r"progress: (\\d+)", text)
    progress_text = re.findall(r"progress: (\d+)", text)
    progresses = [int(progress) for progress in progress_text]

    droped_counter = Counter(progresses)
    max_value = len(progresses)
    diff_survival_rate = []

    for i in range(max(progresses) + 10):
        max_value -= droped_counter[i]
        diff_survival_rate.append(
            abs(max_value / len(progresses) - pp_survival_rate[i])
        )
    return GraphData(
        x=list(range(len(diff_survival_rate))),
        y=diff_survival_rate,
    )


def calc_survival_diff_mean_data(
    player_data_list: list[PlayerData],
):
    pp_survival_rate = _calc_pp_survival_rate()
    grouped: dict[tuple[int, str, int | None], list[GraphData]] = {}
    for pd in player_data_list:
        info = tuple_sym_stage(pd)
        if info is None:
            continue
        grouped.setdefault(info, []).append(_calc_survival_diff_curve(pd, pp_survival_rate))

    result = PlotData(
        x_label="progress",
        y_label="difference in survival rate for PP mean",
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

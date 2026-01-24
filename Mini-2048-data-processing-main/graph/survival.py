import re
from collections import Counter
from pathlib import Path

import numpy as np

from .common import GraphData, PlotData, PlayerData, tuple_sym_stage


def calc_survival_rate_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    生存率をプロットする。
    """
    result = PlotData(
        x_label="progress",
        y_label="survival rate",
        data={pd.name: None for pd in player_data_list},
    )
    for pd in player_data_list:
        text = pd.state_file.read_text()
        progress_text = re.findall(r"progress: (\d+)", text)
        progresses = [int(progress) for progress in progress_text]

        droped_counter = Counter(progresses)
        max_value = len(progresses)
        survival_rate = []

        for i in range(max(progresses) + 10):
            max_value -= droped_counter[i]
            survival_rate.append(max_value / len(progresses))

        result.data[pd.name] = GraphData(
            x=list(range(len(survival_rate))),
            y=survival_rate,
        )
    return result


def _calc_survival_curve(pd: PlayerData) -> GraphData:
    text = pd.state_file.read_text()
    progress_text = re.findall(r"progress: (\\d+)", text)
    progresses = [int(progress) for progress in progress_text]

    droped_counter = Counter(progresses)
    max_value = len(progresses)
    survival_rate = []

    for i in range(max(progresses) + 10):
        max_value -= droped_counter[i]
        survival_rate.append(max_value / len(progresses))

    return GraphData(
        x=list(range(len(survival_rate))),
        y=survival_rate,
    )


def calc_survival_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    grouped: dict[tuple[int, str, int | None], list[GraphData]] = {}
    for pd in player_data_list:
        info = tuple_sym_stage(pd)
        if info is None:
            continue
        grouped.setdefault(info, []).append(_calc_survival_curve(pd))

    result = PlotData(
        x_label="progress",
        y_label="survival rate mean",
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

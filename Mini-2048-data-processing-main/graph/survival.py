import re
from collections import Counter
from pathlib import Path

import numpy as np

from .common import GraphData, PlotData, PlayerData, tuple_label, tuple_sym_stage


def _calc_survival_rate_from_file(state_file: Path) -> GraphData:
    text = state_file.read_text()
    progress_text = re.findall(r"progress: (\d+)", text)
    progresses = [int(progress) for progress in progress_text]

    if not progresses:
        raise ValueError(f"{state_file} に progress がありません。state.txt を確認してください。")

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


def calc_survival_rate_data(
    player_data_list: list[PlayerData],
    include_pp: bool = False,
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
        result.data[pd.name] = _calc_survival_rate_from_file(pd.state_file)

    if include_pp:
        # Add PP survival rate once per unique PP state file (seed/game_count)
        pp_paths: dict[Path, str] = {}
        for pd in player_data_list:
            pp_path = pd.pp_state_file
            if pp_path not in pp_paths:
                # Label by seed if possible, otherwise generic "PP"
                seed_label = "PP"
                parent = pp_path.parent.name
                if parent.startswith("seed"):
                    seed_label = f"PP_{parent}"
                pp_paths[pp_path] = seed_label

        for pp_path, label in pp_paths.items():
            result.data[label] = _calc_survival_rate_from_file(pp_path)
    return result


def _calc_survival_curve(pd: PlayerData) -> GraphData:
    return _calc_survival_rate_from_file(pd.state_file)


def calc_survival_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    grouped: dict[
        tuple[int, str, int | None], list[tuple[PlayerData, GraphData]]
    ] = {}
    for pd in player_data_list:
        info = tuple_sym_stage(pd)
        if info is None:
            continue
        grouped.setdefault(info, []).append((pd, _calc_survival_curve(pd)))

    result = PlotData(
        x_label="progress",
        y_label="survival rate mean",
        data={},
    )
    for (tuple_v, sym, stage), items in grouped.items():
        if not items:
            continue
        curves = [c for _, c in items]
        min_len = min(len(c.x) for c in curves)
        if min_len == 0:
            continue
        xs = [np.mean([c.x[i] for c in curves]) for i in range(min_len)]
        ys = [np.mean([c.y[i] for c in curves]) for i in range(min_len)]
        label = f"NT{tuple_label(items[0][0], tuple_v)}_{sym}_mean"
        if stage is not None:
            label += f"_st{stage}"
        result.data[label] = GraphData(x=xs, y=ys)
    return result

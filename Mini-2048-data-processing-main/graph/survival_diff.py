import re
from collections import Counter
from pathlib import Path

from .common import GraphData, PlotData, PlayerData


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

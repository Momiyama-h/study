import re
from collections import Counter
from pathlib import Path

from .common import GraphData, PlotData, PlayerData


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

import re
from pathlib import Path

import matplotlib.pyplot as plt
from .common import PlayerData

BINS = 100


def plot_histgram(
    player_data_list: list[PlayerData],
    output: Path,
    is_show: bool = True,
):
    """
    得点分布をプロットする。
    """
    for pd in player_data_list:
        text = pd.state_file.read_text()
        score_txt = re.findall(r"score: (\d+)", text)
        scores = [int(score) for score in score_txt]

        plt.hist(scores, bins=BINS)
        plt.xlabel("score")
        plt.ylabel("frequency")
        plt.savefig(output.with_stem(f"{output.stem}-{pd.name}"))
        if is_show:
            plt.show()
        plt.close()
    return None

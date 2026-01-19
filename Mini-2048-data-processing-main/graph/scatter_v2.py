import random
import re
from pathlib import Path

import matplotlib.pyplot as plt

from .common import get_eval_and_hand_progress, PlayerData


def get_evals(eval_file: Path):
    eval_txt = eval_file.read_text("utf-8")
    subed_eval_txt = re.sub(r"game.*\n?", "", eval_txt)
    eval_lines = subed_eval_txt.splitlines()
    return [float(line) for line in eval_lines]


def plot_scatter(
    player_data_list: list[PlayerData],
    output: Path,
    is_show: bool = True,
):
    """
    パーフェクトプレイヤとプレイヤーの評価値の散布図をプロットする。
    """

    for i, pd in enumerate(player_data_list):
        pp_evals = get_evals(pd.pp_eval_after_state)
        pr_eval_and_hand_progress = get_eval_and_hand_progress(pd.eval_file)

        assert len(pp_evals) == len(
            pr_eval_and_hand_progress
        ), f"データ数が異なります。{len(pp_evals)=}, {len(pr_eval_and_hand_progress)=}"

        scatter_data = [
            (ev, pr_eval.evals[pr_eval.idx[0]])
            for ev, pr_eval in zip(pp_evals, pr_eval_and_hand_progress)
        ]
        # 1000個のデータをランダムで取得
        scatter_data = random.sample(scatter_data, 1500)

        # 散布図のdotの大きさを指定
        plt.scatter(
            [d[0] for d in scatter_data],
            [d[1] for d in scatter_data],
            s=5,
            label=pd.config.get("label", pd.name),
            color=pd.config.get("color", None),
        )
        # 直線を引く
    plt.plot(
        [0, 6000],
        [0, 6000],
        color="black",
        linestyle="dashed",
    )
    plt.xlabel("perfect")
    plt.ylabel("player")
    plt.legend()
    plt.tight_layout()
    save_path = output.with_stem(f"{output.stem}_v2")
    plt.savefig(save_path)
    print(f"{save_path} saved.")
    if is_show:
        plt.show()
    plt.close()
    return None

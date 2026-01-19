import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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
)


def calc_accuracy(
    pp_ehp: EvalAndHandProgress,
    pr_ehp: EvalAndHandProgress,
):
    count = 0
    for pp_eval in pp_ehp.idx:
        for pr_eval in pr_ehp.idx:
            if pp_eval == pr_eval:
                count += 1
    return count / len(pr_ehp.idx)


def acc_diff_plot(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    最善手率の差分を計算し、プロットする。
    """
    result = PlotData(
        x_label="progress",
        y_label="accuracy",
        data={},
    )

    for player_data in player_data_list:
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

        result.data[player_data.name] = GraphData(
            x=moving_average(list(acc.keys()), 10).tolist(),  # スムージング
            y=moving_average(list(acc.values()), 10).tolist(),
        )

    # 差分を計算

    if len(player_data_list) < 2:
        raise ValueError("少なくとも2つの player_data_list が必要です。")

    first = player_data_list[0]
    second = player_data_list[1]

    result2 = PlotData(
        x_label="progress",
        y_label="accuracy difference",
        data={first.name + "-" + second.name: GraphData(x=[], y=[])},
    )

    x_values_first = result.data[first.name].x
    x_values_second = result.data[second.name].x
    y_values_first = result.data[first.name].y
    y_values_second = result.data[second.name].y

    diff_x = []
    diff_y = []

    # x 値を統一しながら処理
    for x1, y1 in zip(x_values_first, y_values_first):
        if x1 in x_values_second:
            index2 = x_values_second.index(x1)
            y2 = y_values_second[index2]
        else:
            y2 = 0  # 存在しない場合は0

        diff_x.append(x1)
        diff_y.append(y1 - y2)

    for x2, y2 in zip(x_values_second, y_values_second):
        if x2 not in x_values_first:
            y1 = 0  # 存在しない場合は0
            diff_x.append(x2)
            diff_y.append(y1 - y2)

    # 結果を保存
    result2.data[first.name + "-" + second.name] = GraphData(
        x=diff_x,
        y=diff_y,
    )

    # y=0 を基準に色分け
    colors = ["blue" if y > 0 else "red" for y in diff_y]

    # プロットを作成
    plt.figure()
    plt.axhline(y=0, color="black", linestyle="--", linewidth=1.0)  # y=0 の基準線
    plt.scatter(
        diff_x,
        diff_y,
        c=colors,
        s=10,
        label=f"{first.config.get('label')} - {second.config.get('label')}",
    )
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="blue",
            markersize=8,
            label=f"{first.config.get('label')} > {second.config.get('label')}",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="red",
            markersize=8,
            label=f"{second.config.get('label')} > {first.config.get('label')}",
        ),
    ]
    plt.legend(handles=legend_elements)
    plt.plot(diff_x, diff_y, linestyle="-", alpha=0.5)

    plt.xlabel("Progress")
    plt.ylabel("Accuracy Difference")
    plt.title("Accuracy Difference Plot (Colored by Sign)")
    # plt.legend()
    plt.grid()
    plt.savefig("output/acc_diff_plot.pdf")
    # plt.show()

    # 出力を確認
    # print(f"result2.x: {result2.data[first_key + '-' + second_key].x}")
    # print(f"result2.y: {result2.data[first_key + '-' + second_key].y}")

    return None

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

from .common import (
    EvalAndHandProgress,
    GraphData,
    PlotData,
    get_eval_and_hand_progress,
    moving_average,
)


def calc_accuracy(
    pp_ehp: EvalAndHandProgress,
    pr_ehp: EvalAndHandProgress,
):
    """
    最善手率を計算する
    プレイヤーの最善手のうち、何割がperfect playerの最善手と一致しているかを計算
    """
    # perfect playerの最善手セット
    pp_best_moves = set(pp_ehp.idx)
    # playerの最善手セット
    pr_best_moves = set(pr_ehp.idx)

    # playerの最善手のうち、perfect playerの最善手と一致するものの数
    common_moves = pp_best_moves.intersection(pr_best_moves)
    assert (
        len(common_moves) / len(pr_ehp.idx)
    ) <= 1, f"Accuracy計算エラー: 一致率が1を超えています。{len(common_moves)=}, {len(pr_ehp.idx)=}"
    # プレイヤーの最善手総数で割る
    return len(common_moves) / len(pr_ehp.idx)


def create_progress_eval_accuracy_plot(
    perfect_eval_files: list[Path],
    player_eval_files: list[Path],
    pp_eval_file: Path,
    min_progress: int = 0,
    max_progress: int = 250,
    bin_width: int = 10,
    output: Path = Path("output/progress_eval_accuracy.pdf"),
    config: dict = {},
    is_show: bool = False,
):
    """
    横軸progress、縦軸eval ratio（PPプレイヤーのみ）とaccuracyのグラフを作成する
    複数のプレイヤーのaccuracyを同一グラフに表示する
    """
    # PPプレイヤー自身のデータを読み込み（eval ratio用）
    pp_eval_and_hand_progress = get_eval_and_hand_progress(pp_eval_file)

    # 1. PPプレイヤーのeval ratioデータを準備
    pp_progress_data = defaultdict(list)

    for eval_data in pp_eval_and_hand_progress:
        if min_progress <= eval_data.prg <= max_progress:
            valid_evals = [eval for eval in eval_data.evals if eval > -10000000000]
            if len(valid_evals) >= 2:
                max_val = max(valid_evals)
                min_val = min(valid_evals)
                if max_val != 0:
                    ratio = min_val / max_val
                    pp_progress_data[eval_data.prg].append(ratio)

    # 2. 各プレイヤーのAccuracyデータを準備
    player_acc_data = {}

    for perfect_eval_file, player_eval_file in zip(
        perfect_eval_files, player_eval_files
    ):
        # プレイヤーごとのデータを読み込み
        perfect_eval_and_hand_progress = get_eval_and_hand_progress(perfect_eval_file)
        player_eval_and_hand_progress = get_eval_and_hand_progress(player_eval_file)

        # model_nameをconfigから取得
        model_name = player_eval_file.parent.name
        model_label = config.get(model_name, {}).get("label", model_name)

        assert len(perfect_eval_and_hand_progress) == len(
            player_eval_and_hand_progress
        ), f"データ数が異なります。{len(perfect_eval_and_hand_progress)=}, {len(player_eval_and_hand_progress)=}"

        acc_dict = defaultdict(list)
        for pp_eval, pr_eval in zip(
            perfect_eval_and_hand_progress, player_eval_and_hand_progress
        ):
            if min_progress <= pp_eval.prg <= max_progress:
                acc_dict[pp_eval.prg].append(calc_accuracy(pp_eval, pr_eval))

        # accuracyの平均を取る
        acc_data = {
            prg: np.mean(acc_list)
            for prg, acc_list in sorted(acc_dict.items(), key=lambda x: x[0])
        }
        player_acc_data[model_label] = acc_data

    # 箱ひげ図用のビンデータを準備（PPのeval ratioのみ）
    if not pp_progress_data:
        print(
            f"Progress範囲 {min_progress}-{max_progress} に有効なPPデータがありません"
        )
        return None

    # 箱ひげ図用のビンデータを準備（PPのeval ratioのみ）
    if not pp_progress_data:
        print(
            f"Progress範囲 {min_progress}-{max_progress} に有効なPPデータがありません"
        )
        return None

    bins = []
    bin_labels = []
    bin_data = []
    bin_centers = []

    for bin_start in range(min_progress, max_progress + 1, bin_width):
        bin_end = min(bin_start + bin_width - 1, max_progress)
        bin_ratios = []

        for progress in range(bin_start, bin_end + 1):
            if progress in pp_progress_data:
                bin_ratios.extend(pp_progress_data[progress])

        if bin_ratios:
            bins.append((bin_start, bin_end))
            bin_labels.append(f"{bin_start}-{bin_end}")
            bin_data.append(bin_ratios)
            bin_centers.append((bin_start + bin_end) / 2)

    if not bin_data:
        print("箱ひげ図用のビンに有効なデータがありません")
        return None

    # 3. グラフ作成
    output_file = output.with_stem(f"{output.stem}_multi_player")

    fig, ax1 = plt.subplots(figsize=(16, 8))

    # 箱ひげ図を描画（PP Eval Ratio）
    # positionsパラメータでbin_centersの位置に箱ひげ図を配置
    box_plot = ax1.boxplot(
        bin_data, positions=bin_centers, widths=bin_width * 0.8, patch_artist=True
    )
    ax1.set_xlabel("Progress")
    ax1.set_ylabel("PP Eval Ratio (Max-Min)/Max", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.grid(True, alpha=0.3)
    # eval ratioを0-1の範囲に設定してaccuracyと合わせる
    ax1.set_ylim(0, 1)

    # 箱ひげ図の色を設定
    for patch in box_plot["boxes"]:
        patch.set_facecolor("lightblue")
        patch.set_alpha(0.7)
        patch.set_edgecolor("blue")

    # 中央値線を強調
    for median in box_plot["medians"]:
        median.set_color("darkblue")
        median.set_linewidth(2)

    # x軸の目盛りを設定（箱ひげ図に合わせて）
    ax1.set_xticks(bin_centers)
    ax1.set_xticklabels(bin_labels, rotation=45, ha="right")  # 斜めにして重なりを防ぐ

    # 第二のy軸を作成して各プレイヤーのAccuracyをプロット
    ax2 = ax1.twinx()

    # 色とマーカーのリスト
    colors = [
        "red",
        "green",
        "orange",
        "purple",
        "brown",
        "pink",
        "gray",
        "olive",
        "cyan",
    ]

    legend_elements = [
        plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor="lightblue",
            edgecolor="blue",
            alpha=0.7,
            label="PP Eval Ratio (Box Plot)",
        )
    ]

    for i, (model_label, acc_data) in enumerate(player_acc_data.items()):
        color = colors[i % len(colors)]

        # progressとaccuracyのリストを作成（min_progress～max_progressの範囲のみ）
        progress_list = [
            prg for prg in acc_data.keys() if min_progress <= prg <= max_progress
        ]
        accuracy_list = [acc_data[prg] for prg in progress_list]
        for acc in accuracy_list:
            assert (
                acc <= 1
            ), f"Accuracy計算エラー: 一致率が1を超えています。{acc=}, {model_label=}"

        # 点を打たずに線のみでプロット
        line2 = ax2.plot(
            progress_list,
            accuracy_list,
            color=color,
            linestyle="-",
            linewidth=2,
            label=f"Accuracy ({model_label})",
        )

        legend_elements.append(
            plt.Line2D(
                [0], [0], color=color, linewidth=2, label=f"Accuracy ({model_label})"
            )
        )

    ax2.set_ylabel("Accuracy", color="black")
    ax2.tick_params(axis="y", labelcolor="black")

    # 左軸の範囲を取得して右軸に合わせる（箱ひげ図の先端も見やすくするため）
    ax1_ylim = ax1.get_ylim()
    ax2.set_ylim(ax1_ylim)  # 右軸を左軸の範囲に合わせる

    # 凡例を追加
    ax1.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(0.02, 0.98))

    # x軸の範囲を設定（両方とも同じ範囲に）
    ax1.set_xlim(min_progress, max_progress)
    ax2.set_xlim(min_progress, max_progress)

    plt.tight_layout()
    plt.savefig(output_file, bbox_inches="tight")

    if is_show:
        plt.show()
    else:
        plt.close()

    print(
        f"Progress vs Eval Ratio (Box Plot) & Multi-Player Accuracyグラフを {output_file} に保存しました"
    )
    print(f"Progress範囲: {min_progress}-{max_progress}, ビン幅: {bin_width}")
    print(f"箱ひげ図のビン数: {len(bin_data)}")
    print(f"プレイヤー数: {len(player_acc_data)}")

    # 統計情報を表示
    for i, (bin_range, data) in enumerate(zip(bins, bin_data)):
        mean_ratio = np.mean(data)
        std_ratio = np.std(data)
        median_ratio = np.median(data)
        print(
            f"PP Eval Ratioビン {bin_range[0]}-{bin_range[1]}: {len(data)} データポイント, 平均: {mean_ratio:.4f}, 中央値: {median_ratio:.4f}, 標準偏差: {std_ratio:.4f}"
        )

    for model_label, acc_data in player_acc_data.items():
        if acc_data:
            acc_values = list(acc_data.values())
            acc_min = min(acc_values)
            acc_max = max(acc_values)
            acc_mean = np.mean(acc_values)
            print(
                f"{model_label} Accuracyの範囲: {acc_min:.4f} - {acc_max:.4f}, 平均: {acc_mean:.4f}"
            )

    return None

from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
import numpy as np
import re
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Literal

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class AnalysisConfig:
    """分析設定を管理するクラス"""

    # ファイル設定
    data_file: Path

    # Progress範囲設定
    min_progress: int = 0
    max_progress: int = 250
    bin_width: int = 10

    # 評価値計算設定
    ratio_type: Literal["min_div_max", "2nd_max_div_max"] = "2nd_max_div_max"
    normalization: Literal["none", "min_max", "relative_position", "sigmoid"] = "none"

    # 出力設定
    output_dir: str = "output"

    @property
    def model_name(self) -> str:
        """data_fileの親ディレクトリ名からmodel_nameを自動取得"""
        return self.data_file.parent.name

    @property
    def ratio_description(self) -> str:
        """比率の説明文を返す"""
        base_desc = "2nd Max/Max" if self.ratio_type == "2nd_max_div_max" else "Min/Max"
        if self.normalization == "none":
            return base_desc
        elif self.normalization == "min_max":
            return f"{base_desc} (MinMax Normalized)"
        elif self.normalization == "relative_position":
            return f"{base_desc} (Relative Position)"
        elif self.normalization == "sigmoid":
            return f"{base_desc} (Sigmoid Normalized)"
        return base_desc

    @property
    def output_suffix(self) -> str:
        """出力ファイル名のサフィックスを生成"""
        ratio_suffix = "2ndmax" if self.ratio_type == "2nd_max_div_max" else "minmax"
        norm_suffix = "" if self.normalization == "none" else f"_{self.normalization}"
        return f"{self.model_name}_{self.min_progress}-{self.max_progress}_bin{self.bin_width}_{ratio_suffix}{norm_suffix}"


@dataclass
class EvalAndHandProgress:
    evals: list[float]  # 長さ4のリスト
    prg: int  # progress

    @property
    def valid_evals_sorted(self) -> list[float]:
        """有効な評価値を降順でソートしたリストを返す"""
        return sorted(
            [eval for eval in self.evals if eval > -10000000000], reverse=True
        )

    @property
    def idx(self) -> list[int]:
        """
        evalsの最大値のindexのリストを返す。
        """
        max_eval = max(self.evals)
        return [i for i, eval in enumerate(self.evals) if eval == max_eval]

    @property
    def second_max_value(self) -> float:
        """有効な評価値の2番目に大きい値を返す"""
        sorted_evals = self.valid_evals_sorted
        if len(sorted_evals) < 2:
            return float("-inf")

        # 重複を除去
        unique_evals = []
        for val in sorted_evals:
            if not unique_evals or val != unique_evals[-1]:
                unique_evals.append(val)

        if len(unique_evals) >= 2:
            return unique_evals[1]  # 2番目に大きい値
        else:
            # 全て同じ値の場合、最大値と同じ値を返す
            return unique_evals[0]

    def get_eval_ratio(
        self, ratio_type: str = "2nd_max_div_max", normalization: str = "none"
    ) -> float:
        """指定されたタイプの評価値比率を返す"""
        sorted_evals = self.valid_evals_sorted
        if len(sorted_evals) < 2:
            return float("nan")

        max_val = sorted_evals[0]
        min_val = sorted_evals[-1]

        # 基本的な比率を計算
        if ratio_type == "2nd_max_div_max":
            second_max_val = self.second_max_value
            if max_val == 0:
                raw_ratio = 0.0 if second_max_val == 0 else float("-inf")
            elif second_max_val == float("-inf"):
                raw_ratio = 1.0
            else:
                raw_ratio = second_max_val / max_val
        else:  # "min_div_max"
            if max_val == 0:
                raw_ratio = 0.0 if min_val == 0 else float("-inf")
            elif min_val < 0 or max_val < 0:
                raw_ratio = 0
            else:
                raw_ratio = min_val / max_val

        # 正規化を適用
        if normalization == "none" or not np.isfinite(raw_ratio):
            return raw_ratio
        elif normalization == "min_max":
            # Min-Max正規化: (value - min) / (max - min)
            if ratio_type == "2nd_max_div_max":
                if max_val == min_val:
                    return 1.0
                second_max_val = self.second_max_value
                return (second_max_val - min_val) / (max_val - min_val)
            else:  # min_div_max
                # min_div_maxの場合、最小値は常に0になるので意味がない
                # 代わりに、比率自体を[0,1]にクリップ
                return max(0.0, min(1.0, raw_ratio))
        elif normalization == "relative_position":
            # 相対位置正規化: より直感的な0-1スケール
            if ratio_type == "2nd_max_div_max":
                if max_val == min_val:
                    return 1.0
                second_max_val = self.second_max_value
                return (second_max_val - min_val) / (max_val - min_val)
            else:  # min_div_max
                return 0.0  # 最小値は常に最下位
        elif normalization == "sigmoid":
            # シグモイド正規化: 外れ値に対してロバスト
            return 1.0 / (1.0 + np.exp(-raw_ratio))

        return raw_ratio

    @property
    def is_valid(self) -> bool:
        """有効なデータかどうかを判定（有効な評価値が2つ以上あるか）"""
        return len(self.valid_evals_sorted) >= 2


def get_eval_and_hand_progress(eval_file: Path):
    """
    ファイルから
    評価値、選択した手、progressを取得する。
    """
    eval_txt = eval_file.read_text("utf-8")
    subed_eval_txt = re.sub(r"game.*\n?", "", eval_txt)
    eval_lines = subed_eval_txt.splitlines()
    eval_and_hand_progress = [
        EvalAndHandProgress(
            evals=list(map(float, line.split()[:4])),
            prg=int(
                float(line.split()[4])
            ),  # progress を double(float)で受け取ってから int に変換
        )
        for line in eval_lines
    ]
    return eval_and_hand_progress


def create_boxplot_by_progress_range(
    eval_and_hand_progress: List[EvalAndHandProgress], config: AnalysisConfig
):
    """
    設定に基づいてprogressの範囲でビンに分けて、評価値比率の箱ひげ図を作成する
    """
    # progressごとにデータを整理（指定範囲内のみ）
    progress_data = defaultdict(list)

    for eval_data in eval_and_hand_progress:
        # 有効なデータで、かつ指定範囲内のもののみを使用
        if (
            eval_data.is_valid
            and config.min_progress <= eval_data.prg <= config.max_progress
        ):
            ratio = eval_data.get_eval_ratio(config.ratio_type, config.normalization)
            if np.isfinite(ratio):
                progress_data[eval_data.prg].append(ratio)

    # ビンに分ける
    if not progress_data:
        print(
            f"Progress範囲 {config.min_progress}-{config.max_progress} に有効なデータがありません"
        )
        return

    bins = []
    bin_labels = []
    bin_data = []

    for bin_start in range(
        config.min_progress, config.max_progress + 1, config.bin_width
    ):
        bin_end = min(bin_start + config.bin_width - 1, config.max_progress)
        bin_ratios = []

        for progress in range(bin_start, bin_end + 1):
            if progress in progress_data:
                bin_ratios.extend(progress_data[progress])

        if bin_ratios:  # 空でないビンのみ追加
            bins.append((bin_start, bin_end))
            bin_labels.append(f"{bin_start}-{bin_end}")
            bin_data.append(bin_ratios)

    if not bin_data:
        print("ビンに有効なデータがありません")
        return

    # ファイル名とタイトルを生成
    output_path = f"{config.output_dir}/boxplot_progress_{config.output_suffix}.pdf"
    title = f"Box Plot of Evaluation Ratios by Progress (Range: {config.min_progress}-{config.max_progress})\n({config.model_name}, {config.ratio_description} Ratio, Bin Width: {config.bin_width})"

    # 箱ひげ図を作成
    plt.figure(figsize=(16, 8))
    plt.boxplot(bin_data, tick_labels=bin_labels)
    plt.xlabel("Progress Range")
    plt.ylabel(f"Evaluation Ratio ({config.ratio_description})")
    # plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()

    print(f"箱ひげ図を {output_path} に保存しました")
    print(
        f"Progress範囲: {config.min_progress}-{config.max_progress}, ビン幅: {config.bin_width}"
    )
    print(f"ビン数: {len(bin_data)}")
    for i, (bin_range, data) in enumerate(zip(bins, bin_data)):
        mean_ratio = np.mean(data)
        std_ratio = np.std(data)
        median_ratio = np.median(data)
        print(
            f"ビン {bin_range[0]}-{bin_range[1]}: {len(data)} データポイント, 平均: {mean_ratio:.4f}, 中央値: {median_ratio:.4f}, 標準偏差: {std_ratio:.4f}"
        )


def create_boxplot_by_max_eval(
    eval_and_hand_progress: List[EvalAndHandProgress],
    config: AnalysisConfig,
    num_bins: int = 250,
):
    """
    設定に基づいて最大評価値を基準にビンに分けて、評価値比率の箱ひげ図を作成する
    """
    # fontの設定
    # fontsize
    plt.rcParams["font.size"] = 15
    # 有効なデータを抽出
    valid_data = []
    for eval_data in eval_and_hand_progress:
        if eval_data.is_valid:
            ratio = eval_data.get_eval_ratio(config.ratio_type, config.normalization)
            if np.isfinite(ratio):
                valid_data.append((eval_data.valid_evals_sorted[0], ratio))

    if not valid_data:
        print("有効なデータがありません")
        return

    # 最大評価値でソート
    valid_data.sort(key=lambda x: x[0])
    max_values = [x[0] for x in valid_data]
    ratios = [x[1] for x in valid_data]

    min_val = min(max_values)
    max_val = max(max_values)
    # bin_edges = np.linspace(0, 5500, 50)
    bin_edges = list(range(0, 5600, 100))

    bin_data = []
    bin_labels = []

    for i in range(56 - 1):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]

        # このビンに含まれるデータを抽出
        bin_ratios = []
        for max_val, ratio in valid_data:
            if bin_start <= max_val <= bin_end:
                bin_ratios.append(ratio)

        if bin_ratios:  # 空でないビンのみ追加
            bin_data.append(bin_ratios)
            if bin_end % 1000 == 0:
                bin_labels.append(f"-{bin_end:.0f}")
            else:
                bin_labels.append("")

    if not bin_data:
        print("ビンに有効なデータがありません")
        return
    # 前半と後半に分割
    mid = len(bin_data) // 2
    halves = [
        ("first", bin_data[:mid], bin_labels[:mid], np.array(range(5, 30, 5)), 0),
        ("second", bin_data[mid:], bin_labels[mid:], np.array(range(30, 55, 5)), -27),
    ]

    for suffix, data_half, labels_half, positions_half, offset in halves:
        plt.figure(figsize=(8, 3))
        positions = [i - 0.5 for i in range(1, len(data_half) + 1)]
        box_plot = plt.boxplot(
            data_half,
            positions=positions,
            showfliers=False,
            widths=0.8,
        )

        # 軸ラベルやタイトル
        plt.xticks(positions_half + offset, positions_half * 100)
        plt.xlabel("Max Evaluation Value")
        plt.ylabel(f"Ratio ({config.ratio_description})")
        # plt.title(f"{title} ({suffix})")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_path = (
            f"{config.output_dir}/boxplot_maxeval_{suffix}_{config.output_suffix}.pdf"
        )
        plt.savefig(output_path)
        plt.show()

        print(f"箱ひげ図 ({suffix}) を {output_path} に保存しました")
        print(f"ビン数: {len(data_half)}")
        for i, (label, data) in enumerate(zip(labels_half, data_half)):
            mean_ratio = np.mean(data)
            std_ratio = np.std(data)
            print(
                f"[{suffix}] ビン {label or i}: {len(data)} データポイント, 平均比率: {mean_ratio:.4f}, 標準偏差: {std_ratio:.4f}"
            )


if __name__ == "__main__":

    # CNN_DEEPモデルの分析
    config = AnalysisConfig(
        data_file=Path("cp_board_data/PP/eval.txt"),
        # data_file=Path("board_data/[learning-toggle.py][model-DEEP][seed-1][symmetry-True][type-toggle]/eval.txt"),
        # data_file=Path("board_data/[learning-buffer.py][model-DEEP][seed-1][symmetry-True][freq-50]/eval.txt"),
        # data_file=Path(
        #     "board_data/[learning-nn.py][model-DEEP][seed-2][symmetry-True]/eval.txt"
        # ),
        min_progress=0,
        max_progress=250,
        bin_width=10,
        ratio_type="min_div_max",  # "min_div_max" or "2nd_max_div_max"
        normalization="off",
        output_dir="output",
    )

    if not config.data_file.exists():
        print(f"ファイルが見つかりません: {config.data_file}")
        exit(1)

    print(f"データを読み込み中... ({config.model_name})")
    eval_and_hand_progress = get_eval_and_hand_progress(config.data_file)
    print(f"読み込んだデータ数: {len(eval_and_hand_progress)}")

    # 基本統計情報を表示
    valid_data = []
    invalid_count = 0

    for eval_data in eval_and_hand_progress:
        if eval_data.is_valid:
            ratio = eval_data.get_eval_ratio(config.ratio_type, config.normalization)
            if np.isfinite(ratio):
                valid_data.append(
                    {
                        "ratio": ratio,
                        "progress": eval_data.prg,
                        "valid_moves": len(eval_data.valid_evals_sorted),
                    }
                )
        else:
            invalid_count += 1

    print(f"\n基本統計情報 ({config.model_name}):")
    print(f"有効なデータ数: {len(valid_data)}")
    print(f"無効なデータ数: {invalid_count}")
    print(f"比率計算方法: {config.ratio_description}")
    print(f"正規化手法: {config.normalization}")

    if valid_data:
        ratios = [d["ratio"] for d in valid_data]
        progress_values = [d["progress"] for d in valid_data]
        valid_moves_counts = [d["valid_moves"] for d in valid_data]

        # 各統計値を動的に計算
        max_eval_values = [
            eval_data.valid_evals_sorted[0]
            for eval_data in eval_and_hand_progress
            if eval_data.is_valid
        ]
        second_max_eval_values = [
            eval_data.second_max_value
            for eval_data in eval_and_hand_progress
            if eval_data.is_valid
        ]

        print(
            f"評価値比率（{config.ratio_description}） - 平均: {np.mean(ratios):.4f}, 標準偏差: {np.std(ratios):.4f}"
        )
        print(f"評価値比率 - 最小: {np.min(ratios):.4f}, 最大: {np.max(ratios):.4f}")
        print(f"評価値比率 - 中央値: {np.median(ratios):.4f}")
        print(f"Progress範囲: {min(progress_values)} - {max(progress_values)}")
        print(
            f"最大評価値範囲: {min(max_eval_values):.4f} - {max(max_eval_values):.4f}"
        )
        if config.ratio_type == "2nd_max_div_max":
            print(
                f"2番目最大評価値範囲: {min(second_max_eval_values):.4f} - {max(second_max_eval_values):.4f}"
            )
        print(f"有効な手の数 - 平均: {np.mean(valid_moves_counts):.2f}")

        # 評価値比率の分布をもう少し詳しく
        print(f"\n評価値比率（{config.ratio_description}）の分布:")
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            value = np.percentile(ratios, p)
            print(f"  {p}パーセンタイル: {value:.4f}")

        # Progress基準での箱ひげ図を作成
        print(
            f"\n1. Progress基準での箱ひげ図を作成中... ({config.min_progress}-{config.max_progress}, {config.bin_width}刻み)"
        )
        create_boxplot_by_progress_range(eval_and_hand_progress, config)

        # 最大評価値基準での箱ひげ図を作成
        print("\n2. 最大評価値基準での箱ひげ図を作成中...")
        create_boxplot_by_max_eval(
            eval_and_hand_progress, config
        )  # configから直接bin_widthを使用

        print("\n全ての箱ひげ図の作成が完了しました！")
        print(f"出力ファイル接頭辞: {config.output_suffix}")
        print("これらの箱ひげ図から、以下のような分析が可能です：")
        if config.ratio_type == "2nd_max_div_max":
            print("- Progressが進むにつれて2番目最大/最大の評価値比率がどう変化するか")
            print("- モデルの判断における最良手と次善手の評価値差の変化")
        else:
            print("- Progressが進むにつれて最小/最大の評価値比率がどう変化するか")
            print("- モデルの判断における最良手と最悪手の評価値差の変化")
        print("- 最大評価値の範囲によって評価値比率がどう分布するか")
    else:
        print("有効なデータがありませんでした。")

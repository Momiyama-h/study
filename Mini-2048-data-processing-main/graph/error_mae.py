from collections import defaultdict
import numpy as np

from .common import (
    GraphData,
    PlotData,
    get_eval_and_hand_progress,
    moving_average,
    PlayerData,
    tuple_label,
    tuple_sym_stage,
)


def _mae_list(pp_eval_and_hand_progress, pr_eval_and_hand_progress):
    mae_dict = defaultdict(list)
    for pp_eval, pr_eval in zip(
        pp_eval_and_hand_progress, pr_eval_and_hand_progress
    ):
        diff = pp_eval.evals[pr_eval.idx[0]] - pp_eval.evals[pp_eval.idx[0]]
        mae_dict[pp_eval.prg].append(abs(diff))
    return mae_dict


def calc_mae_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    絶対誤差（MAE）をプロットする。
    """
    result = PlotData(
        x_label="progress",
        y_label="mae",
        data={pd.name: "" for pd in player_data_list},
    )
    for player_data in player_data_list:
        pp_eval_and_hand_progress = get_eval_and_hand_progress(
            player_data.pp_eval_state
        )
        pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

        assert len(pp_eval_and_hand_progress) == len(
            pr_eval_and_hand_progress
        ), f"データ数が異なります。{len(pp_eval_and_hand_progress)=}, {len(pr_eval_and_hand_progress)=}"

        mae_dict = _mae_list(pp_eval_and_hand_progress, pr_eval_and_hand_progress)
        mae = {
            prg: np.mean(err_list)
            for prg, err_list in sorted(mae_dict.items(), key=lambda x: x[0])
        }
        result.data[player_data.name] = GraphData(
            x=moving_average(list(mae.keys()), 5).tolist(),
            y=moving_average(list(mae.values()), 5).tolist(),
        )
    return result


def _calc_mae_curve(player_data: PlayerData) -> GraphData:
    pp_eval_and_hand_progress = get_eval_and_hand_progress(
        player_data.pp_eval_state
    )
    pr_eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

    assert len(pp_eval_and_hand_progress) == len(
        pr_eval_and_hand_progress
    ), f"データ数が異なります。{len(pp_eval_and_hand_progress)=}, {len(pr_eval_and_hand_progress)=}"

    mae_dict = _mae_list(pp_eval_and_hand_progress, pr_eval_and_hand_progress)
    mae = {
        prg: np.mean(err_list)
        for prg, err_list in sorted(mae_dict.items(), key=lambda x: x[0])
    }
    return GraphData(
        x=moving_average(list(mae.keys()), 5).tolist(),
        y=moving_average(list(mae.values()), 5).tolist(),
    )


def calc_mae_mean_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    grouped: dict[
        tuple[int, str, int | None], list[tuple[PlayerData, GraphData]]
    ] = defaultdict(list)
    for player_data in player_data_list:
        info = tuple_sym_stage(player_data)
        if info is None:
            continue
        grouped[info].append((player_data, _calc_mae_curve(player_data)))

    result = PlotData(
        x_label="progress",
        y_label="mae mean",
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


def calc_mae_symdiff_data(
    player_data_list: list[PlayerData],
) -> PlotData:
    """
    seedごとに sym/notsym を同じグラフで比較できるように、
    symの分割をせずに短いラベルで出力する。
    """
    result = PlotData(
        x_label="progress",
        y_label="mae",
        data={},
    )
    for player_data in player_data_list:
        info = tuple_sym_stage(player_data)
        if info is None:
            continue
        tuple_v, sym, stage = info
        seed = player_data._seed_from_path()
        label = f"NT{tuple_label(player_data, tuple_v)}_{sym}"
        if seed is not None:
            label += f"_seed{seed}"
        if stage is not None:
            label += f"_st{stage}"
        result.data[label] = _calc_mae_curve(player_data)
    return result

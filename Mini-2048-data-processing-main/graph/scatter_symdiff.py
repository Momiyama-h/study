import random
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .common import PlayerData, get_eval_and_hand_progress


def get_evals(eval_file: Path) -> list[float]:
    eval_txt = eval_file.read_text("utf-8")
    subed_eval_txt = re.sub(r"game.*\n?", "", eval_txt)
    eval_lines = subed_eval_txt.splitlines()
    return [float(line) for line in eval_lines]


def _extract_info(pd: PlayerData) -> tuple[str | None, int | None, str | None, int | None]:
    meta = pd.meta or {}
    tuple_v = meta.get("tuple")
    sym = meta.get("sym")
    seed = meta.get("seed")
    stage = meta.get("stage")
    run_name = None

    parts = pd.rel_path.parts
    if parts:
        run_name = parts[0]

    if tuple_v is None or sym is None or seed is None:
        if len(parts) >= 3:
            seed_dir = parts[1]
            nt_dir = parts[2]
            if seed is None and seed_dir.startswith("seed"):
                seed = int(seed_dir.replace("seed", ""))
            if nt_dir.startswith("NT") and "_" in nt_dir:
                tuple_v = int(nt_dir[2])
                sym = nt_dir.split("_", 1)[1]

    return run_name, tuple_v, sym, seed, stage


def _scatter_points(pd: PlayerData, sample_size: int) -> tuple[list[float], list[float]]:
    pp_evals = get_evals(pd.pp_eval_after_state)
    pr_eval_and_hand_progress = get_eval_and_hand_progress(pd.eval_file)

    assert len(pp_evals) == len(
        pr_eval_and_hand_progress
    ), f"データ数が異なります。{len(pp_evals)=}, {len(pr_eval_and_hand_progress)=}"

    scatter_data = [
        (ev, pr_eval.evals[pr_eval.idx[0]])
        for ev, pr_eval in zip(pp_evals, pr_eval_and_hand_progress)
    ]
    if len(scatter_data) > sample_size:
        scatter_data = random.sample(scatter_data, sample_size)
    xs = [d[0] for d in scatter_data]
    ys = [d[1] for d in scatter_data]
    return xs, ys


def _plot_regression(xs: list[float], ys: list[float], color: str, label: str) -> None:
    if len(xs) < 2:
        return
    coeffs = np.polyfit(xs, ys, 1)
    x_min = min(xs)
    x_max = max(xs)
    x_line = np.array([x_min, x_max])
    y_line = coeffs[0] * x_line + coeffs[1]
    plt.plot(x_line, y_line, color=color, linestyle="solid", label=label)


def plot_scatter_symdiff(
    player_data_list: list[PlayerData],
    output: Path,
    is_show: bool = True,
    sample_size: int = 1500,
):
    """
    同一seed・同一タプルのsym/notsymを同じ散布図に重ねて描画する。
    """
    grouped: dict[tuple[str | None, int | None, int | None, int | None], dict[str, PlayerData]] = {}
    for pd in player_data_list:
        run_name, tuple_v, sym, seed, stage = _extract_info(pd)
        if tuple_v is None or sym is None or seed is None:
            continue
        if sym not in ("sym", "notsym"):
            continue
        key = (run_name, tuple_v, seed, stage)
        grouped.setdefault(key, {})[sym] = pd

    for (run_name, tuple_v, seed, stage), items in grouped.items():
        plt.figure()
        plt.plot([0, 6000], [0, 6000], color="gray", linestyle="dashed", label="y=x")

        for sym, color in (("sym", "tab:blue"), ("notsym", "tab:orange")):
            pd = items.get(sym)
            if pd is None:
                continue
            xs, ys = _scatter_points(pd, sample_size)
            plt.scatter(xs, ys, s=5, label=sym, color=color, alpha=0.6)
            _plot_regression(xs, ys, color=color, label=f"{sym} fit")

        plt.xlabel("perfect")
        plt.ylabel("player")
        plt.legend()
        plt.tight_layout()

        suffix = f"seed{seed}_NT{tuple_v}"
        if stage is not None:
            suffix += f"_st{stage}"
        save_path = output.with_stem(f"{output.stem}_{suffix}")
        plt.savefig(save_path)
        print(f"{save_path} saved.")
        if is_show:
            plt.show()
        plt.close()
    return None

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
board_dir = BASE_DIR.parent / "board_data"


def make_safe_name(rel_path: Path) -> str:
    safe = str(rel_path).replace("\\", "/").strip("/")
    return safe.replace("/", "__")


class PlayerData:
    def __init__(self, target_dir: Path, config: dict):
        self.rel_path = target_dir.relative_to(board_dir)
        self.safe_name = make_safe_name(self.rel_path)
        self.name = self.safe_name
        self.target_dir = target_dir
        self.pp_dir = board_dir / "PP"
        self.config = config[self.name] if config and self.name in config else {}
        self._meta_loaded = False
        self._meta_cache = None

    @property
    def state_file(self):
        state_file = self.target_dir / "state.txt"
        if not state_file.exists():
            raise FileNotFoundError(f"{state_file}が存在しません。")
        return state_file

    @property
    def eval_file(self):
        eval_file = self.target_dir / "eval.txt"
        if not eval_file.exists():
            raise FileNotFoundError(f"{eval_file}が存在しません。")
        return eval_file

    @property
    def pp_eval_state(self):
        local = self.target_dir / "eval-state.txt"
        if local.exists():
            return local
        pp: Path = self.pp_dir / f"eval-state-{self.name}.txt"
        if not pp.exists():
            raise FileNotFoundError(f"{pp}が存在しません。")
        return pp

    @property
    def pp_eval_after_state(self):
        local = self.target_dir / "eval-after-state.txt"
        if local.exists():
            return local
        pp: Path = self.pp_dir / f"eval-after-state-{self.name}.txt"
        if not pp.exists():
            raise FileNotFoundError(f"{pp}が存在しません。")
        return pp

    @property
    def meta(self):
        if not self._meta_loaded:
            self._meta_loaded = True
            meta_path = self.target_dir / "meta.json"
            if meta_path.exists():
                self._meta_cache = json.loads(meta_path.read_text("utf-8"))
        return self._meta_cache


def tuple_sym_stage(player_data: PlayerData):
    meta = player_data.meta or {}
    tuple_v = meta.get("tuple")
    sym = meta.get("sym")
    stage = meta.get("stage")
    if tuple_v is not None and sym is not None:
        return tuple_v, sym, stage
    parts = player_data.rel_path.parts
    if len(parts) >= 3:
        nt_dir = parts[2]
        if nt_dir.startswith("NT") and "_" in nt_dir:
            tuple_v = int(nt_dir[2])
            sym = nt_dir.split("_", 1)[1]
            return tuple_v, sym, stage
    return None


@dataclass
class EvalAndHandProgress:
    evals: list[float]  # 長さ4のリスト
    prg: int  # progress

    @property
    def idx(self) -> list[int]:
        """
        evalsの最大値のindexのリストを返す。
        """
        max_eval = max(self.evals)
        return [i for i, eval in enumerate(self.evals) if eval == max_eval]


@dataclass
class PlotData:
    x_label: str
    y_label: str
    data: dict[str, "GraphData"]


@dataclass
class GraphData:
    x: list[float]
    y: list[float]


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


def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode="valid")

import subprocess
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass
class EvalAndHandProgress:
    evals: list[float]  # 長さ4のリスト
    prg: int  # progress


def process_files_with_pattern(base_dir: Path, pattern: str):
    """
    ワイルドカードパターンに一致するディレクトリを処理し、
    指定されたコマンドを実行する。
    """
    matched_dirs = list(base_dir.glob(pattern))

    if not matched_dirs:
        print(f"No directories matched the pattern: {pattern}")
        return

    for directory in matched_dirs:
        if not directory.is_dir():
            print(f"Skipping {directory}, not a directory.")
            continue

        print(f"Processing directory: {directory}")

        # コマンドの実行
        run_command("./eval_state", directory)
        run_command("./eval_after_state", directory)

        print(f"Directory {directory.name} processed successfully.")


def run_command(command: str, directory: Path):
    """
    指定されたコマンドをディレクトリパスとともに実行する。
    """
    try:
        print(f"Running command: {command} {directory}")
        subprocess.run([command, str(directory)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command} {directory}")
        print(e)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <pattern>")
        print("Example: python3 script.py 'MCTS4/game_count100_evfile4tuple_data_9.dat_simulations3000_randomTurn0_expandcount50_c-1_Boltzmann0_expectimax0'")
        sys.exit(1)

    base_dir = Path("../board_data")
    pattern = sys.argv[1]

    process_files_with_pattern(base_dir, pattern)

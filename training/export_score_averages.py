import argparse
import csv
import re
from pathlib import Path


def parse_scores(filepath: Path) -> dict[int, int]:
    pattern = re.compile(r"game\s+(\d+)\s+finished\s+with\s+score\s+(\d+)")
    scores = {}
    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                game_id = int(match.group(1))
                score = int(match.group(2))
                scores[game_id] = score
    return scores


def calculate_averages(scores: dict[int, int], avescope: int) -> list[tuple[int, int, float, int]]:
    if not scores:
        return []

    max_game_id = max(scores.keys())
    results = []

    current_sum = 0
    current_count = 0
    start_game = 1

    for game_id in range(1, max_game_id + 1):
        if game_id in scores:
            current_sum += scores[game_id]
            current_count += 1

        if game_id % avescope == 0:
            if current_count > 0:
                avg = current_sum / current_count
                results.append((start_game, game_id, avg, current_count))
            start_game = game_id + 1
            current_sum = 0
            current_count = 0

    return results


def write_csv(rows: list[tuple[int, int, float, int]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start_game", "end_game", "avg_score", "count"])
        for start, end, avg, count in rows:
            writer.writerow([start, end, f"{avg:.6f}", count])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export average score per interval from training log."
    )
    parser.add_argument("--input", "-i", required=True, help="log file path")
    parser.add_argument("--output", "-o", required=True, help="output CSV path")
    parser.add_argument(
        "--avescope",
        "-a",
        type=int,
        default=1000,
        help="Averaging interval (default: 1000)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    scores = parse_scores(input_path)
    rows = calculate_averages(scores, args.avescope)
    write_csv(rows, output_path)

    print(f"wrote: {output_path}")
    print(f"games: {len(scores)}")
    print(f"rows: {len(rows)}")


if __name__ == "__main__":
    main()

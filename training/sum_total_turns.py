#!/usr/bin/env python3
"""Calculate sum of total_turns from tuple_learning_rate_log_202601132030.csv"""

import csv
import sys


def sum_total_turns_file(filepath):
    """Calculate sum of total_turns column from the specified CSV file."""
    total = 0
    count = 0
    
    try:
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    turns = int(row['total_turns'])
                    total += turns
                    count += 1
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping row due to error: {e}", file=sys.stderr)
                    continue
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None
    
    return total, count


# Specific file path
#filepath = "tuple_learning_rate_log_202601132030.csv"
#prev: filepath = "tuple_learning_rate_log_nosym_202601132030.csv"
filepath = "tuple_learning_rate_log_notsym_202601132030.csv"


result = sum_total_turns_file(filepath)
if result:
    total, count = result
    print(f"File: {filepath}")
    print(f"Number of rows: {count}")
    print(f"Sum of total_turns: {total:,}")
    if count > 0:
        print(f"Average turns/game: {total / count:.2f}")

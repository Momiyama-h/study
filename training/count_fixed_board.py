#!/usr/bin/env python3
"""Count occurrences of FIXED_BOARD pattern in board log CSV files.

FIXED_BOARD = {0, 1, 2, 0, 0, 1, 0, 0, 0}
"""

import csv
import argparse


# FIXED_BOARD pattern from the C++ code
FIXED_BOARD = [0, 1, 2, 0, 0, 1, 0, 0, 0]


def count_fixed_board_pattern(filepath):
    """Count how many times FIXED_BOARD pattern appears in the CSV file."""
    total_rows = 0
    matching_rows = 0
    
    try:
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                # Extract tile values
                tiles = [int(row[f'tile{i}']) for i in range(9)]
                
                # Check if it matches FIXED_BOARD
                if tiles == FIXED_BOARD:
                    matching_rows += 1
                    
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None, None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None, None
    
    return matching_rows, total_rows


def main():
    parser = argparse.ArgumentParser(
        description='Count FIXED_BOARD pattern occurrences in board log CSV files'
    )
    parser.add_argument('--sym', default='board_log.csv',
                        help='Path to symmetric board log CSV')
    # prev default: board_log_nosym.csv
    parser.add_argument('--nosym', default='board_log_notsym.csv',
                        help='Path to non-symmetric board log CSV')
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"FIXED_BOARD Pattern: {FIXED_BOARD}")
    print("=" * 60)
    
    # Analyze symmetric version
    sym_matches, sym_total = count_fixed_board_pattern(args.sym)
    
    # Analyze non-symmetric version
    nosym_matches, nosym_total = count_fixed_board_pattern(args.nosym)
    
    # Display results
    if sym_matches is not None:
        print(f"\nSymmetric version ({args.sym}):")
        print(f"  Total rows: {sym_total:,}")
        print(f"  FIXED_BOARD matches: {sym_matches:,}")
        if sym_total > 0:
            rate = (sym_matches / sym_total) * 100
            print(f"  Occurrence rate: {rate:.6f}%")
            print(f"  Ratio: 1 in {sym_total / sym_matches:.2f}" if sym_matches > 0 else "  Ratio: N/A (no matches)")
    
    if nosym_matches is not None:
        print(f"\nNon-symmetric version ({args.nosym}):")
        print(f"  Total rows: {nosym_total:,}")
        print(f"  FIXED_BOARD matches: {nosym_matches:,}")
        if nosym_total > 0:
            rate = (nosym_matches / nosym_total) * 100
            print(f"  Occurrence rate: {rate:.6f}%")
            print(f"  Ratio: 1 in {nosym_total / nosym_matches:.2f}" if nosym_matches > 0 else "  Ratio: N/A (no matches)")
    
    # Comparison
    if sym_matches is not None and nosym_matches is not None:
        print(f"\n{'─' * 60}")
        print("Comparison:")
        if sym_matches > 0 and nosym_matches > 0:
            ratio = sym_matches / nosym_matches
        print(f"  Matches ratio (sym/notsym): {ratio:.4f}")
        print("=" * 60)


if __name__ == '__main__':
    main()

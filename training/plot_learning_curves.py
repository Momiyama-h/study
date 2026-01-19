#!/usr/bin/env python3
"""Plot learning curves from tuple learning rate logs.

Creates a line graph with:
- X-axis: updatecounts
- Y-axis: err / aerr (ratio of err to average error)

Compares symmetric and non-symmetric versions.
"""

import argparse
import csv
import matplotlib.pyplot as plt


def load_csv_sym(filepath):
    """Load symmetric CSV and return lists of updatecounts and err/aerr ratio."""
    updatecounts = []
    ratios = []
    
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                uc = int(row['updatecounts'])
                aerr = float(row['aerr'])
                err = float(row['err'])
                
                # Avoid division by zero
                if aerr != 0:
                    ratio = err / aerr
                    updatecounts.append(uc)
                    ratios.append(ratio)
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping row in sym CSV due to error: {e}")
                continue
    
    return updatecounts, ratios


def load_csv_nosym(filepath):
    """Load non-symmetric CSV and return lists of uc_avg and err_avg/aerr_avg ratio."""
    updatecounts = []
    ratios = []
    
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                uc = float(row['uc_sum'])
                aerr = float(row['aerr_avg'])
                err = float(row['err_avg'])
                
                # Avoid division by zero
                if aerr != 0:
                    ratio = err / aerr
                    updatecounts.append(uc)
                    ratios.append(ratio)
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping row in notsym CSV due to error: {e}")
                continue
    
    return updatecounts, ratios


def plot_learning_curves(sym_csv, nosym_csv, output_file='learning_curves.png'):
    """Plot learning curves from symmetric and non-symmetric CSV files."""
    
    # Load data
    uc_sym, ratio_sym = load_csv_sym(sym_csv)
    uc_nosym, ratio_nosym = load_csv_nosym(nosym_csv)
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    
    # Plot lines
    plt.plot(uc_sym, ratio_sym, label='Symmetric (4tuples_sym)', 
             linewidth=1, marker='o', markersize=1, alpha=0.7)
    plt.plot(uc_nosym, ratio_nosym, label='Non-symmetric (4tuples_notsym)', 
             linewidth=1, marker='s', markersize=1, alpha=0.7)
    
    # Labels and title
    plt.xlabel('Update Counts', fontsize=12)
    plt.ylabel('err / aerr Ratio', fontsize=12)
    plt.title('Learning Curves: Error Ratio vs Update Counts', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Graph saved to: {output_file}")
    
    # Print statistics
    if uc_sym:
        print(f"\nSymmetric version:")
        print(f"  Data points: {len(uc_sym)}")
        print(f"  Update count range: {min(uc_sym)} - {max(uc_sym)}")
        print(f"  Ratio range: {min(ratio_sym):.6f} - {max(ratio_sym):.6f}")
    
    if uc_nosym:
        print(f"\nNon-symmetric version:")
        print(f"  Data points: {len(uc_nosym)}")
        print(f"  Update count range: {min(uc_nosym):.2f} - {max(uc_nosym):.2f}")
        print(f"  Ratio range: {min(ratio_nosym):.6f} - {max(ratio_nosym):.6f}")


def main():
    parser = argparse.ArgumentParser(description='Plot learning curves from tuple learning logs')
    parser.add_argument('--sym', default='tuple_learning_rate_log.csv',
                        help='Path to symmetric CSV file')
    # prev default: tuple_learning_rate_log_nosym.csv
    parser.add_argument('--nosym', default='tuple_learning_rate_log_notsym.csv',
                        help='Path to non-symmetric CSV file')
    parser.add_argument('--output', default='learning_curves.png',
                        help='Output file path (default: learning_curves.png)')
    args = parser.parse_args()
    
    plot_learning_curves(args.sym, args.nosym, args.output)


if __name__ == '__main__':
    main()

"""
Spinny Car Dataset Optimizer
============================

Aggregates year-by-year variant records into consolidated variant entries,
calculating `make_year_start`, `make_year_end`, and `total_years_produced`.
This significantly reduces dataset size and redundancy while preserving all
variant metadata.

Usage:
    python scripts/optimize_dataset.py [--input path/to/raw.xlsx] [--output path/to/optimized.xlsx]
"""

import os
import sys
import argparse
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "data", "processed", "optimized_spinny_master.xlsx")


def optimize_car_data(input_path: str, output_path: str):
    print(f"Loading dataset from: {input_path}")
    
    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        return False

    try:
        # 1. Load the dataset (Excel)
        df = pd.read_excel(input_path)
        print(f"Original Data Loaded: {len(df):,} rows")

        # 2. Define columns to exclude from grouping (dynamic time-based cols)
        exclude_cols = ['make_year']
        
        # Identify all other columns as identity columns
        identity_cols = [c for c in df.columns if c not in exclude_cols]
        
        print(f"Grouping by {len(identity_cols)} columns...")
        
        # 3. Sort by year to ensure ranges are calculated correctly
        if 'make_year' in df.columns and 'variant_id' in df.columns:
            df = df.sort_values(by=['variant_id', 'make_year'])

        # 4. Perform the Grouping
        # Group by specific identity columns to aggregate production years
        optimized_df = df.groupby(identity_cols, dropna=False).agg(
            make_year_start=('make_year', 'min'),
            make_year_end=('make_year', 'max'),
            total_years_produced=('make_year', 'count')
        ).reset_index()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # 5. Save the optimized data
        print(f"Saving optimized data to: {output_path}")
        optimized_df.to_excel(output_path, index=False)
        
        print("-" * 40)
        print("Optimization Complete!")
        print(f"Original Rows:   {len(df):,}")
        print(f"Optimized Rows:  {len(optimized_df):,}")
        reduction = len(df) / len(optimized_df) if len(optimized_df) > 0 else 0
        print(f"Reduction Ratio: {round(reduction, 2)}x smaller")
        print("-" * 40)
        return True

    except Exception as e:
        print(f"An error occurred during optimization: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize and consolidate raw Spinny car dataset.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to input raw Excel file")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to output optimized Excel file")
    args = parser.parse_args()

    optimize_car_data(args.input, args.output)
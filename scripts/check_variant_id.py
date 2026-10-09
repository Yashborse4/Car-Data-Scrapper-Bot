import pandas as pd
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")

if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        total_rows = len(df)
        unique_variant_ids = df['variant_id'].nunique()
        print(f"Total Rows: {total_rows}")
        print(f"Unique Variant IDs: {unique_variant_ids}")
        
        # Check if grouping by variant_id would allow reduction
        if unique_variant_ids < total_rows:
            print("GOOD: variant_id is shared across multiple rows (likely differing by year). Grouping by variant_id WILL reduce rows.")
            # Check a sample
            dup_vid = df[df.duplicated(subset=['variant_id'], keep=False)]
            if not dup_vid.empty:
                print("Sample of duplicated variant_id:")
                print(dup_vid[['variant_id', 'make_year', 'variant_name']].head())
        else:
            print("WARNING: variant_id is unique per row. Grouping by it will NOT reduce rows.")
            
    except Exception as e:
        print(f"Error: {e}")

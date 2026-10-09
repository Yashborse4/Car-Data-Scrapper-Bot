import pandas as pd
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        # Read only header and 5 rows
        df = pd.read_excel(file_path, nrows=5)
        print("--- Columns ---")
        print(list(df.columns))
        print("\n--- Data Types ---")
        print(df.dtypes)
    except Exception as e:
        print(f"Error reading excel: {e}")

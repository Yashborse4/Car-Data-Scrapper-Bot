import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")

try:
    print("Loading original data...")
    df = pd.read_excel(file_path)
    
    print(f"Total Rows: {len(df)}")
    print("-" * 30)

    # 1. Theoretical Minimum (Group by variant_id only)
    # This ignores ALL other metadata differences
    grp_basic = df.groupby(['variant_id', 'make_year']).size().reset_index()
    print(f"Unique (variant_id, make_year) combinations: {len(grp_basic)}")
    # If we group by variant_id and aggregate years:
    grp_vid = df.groupby(['variant_id']).size()
    print(f"Unique variant_ids: {len(grp_vid)}")
    print("-" * 30)

    # 2. Impact of specific columns on splitting
    # We will start with [variant_id] and add columns to see when count explodes
    base_cols = ['variant_id']
    
    # Columns to test for "noise"
    test_cols = [
        'brand_name', 'model_name', 'variant_name', 
        'fuel_type', 'transmission', 'body_type', 
        'discontinued_year', 'variant_full_name',
        'is_active', 'is_usable', 'is_verified'
    ]
    
    current_cols = base_cols.copy()
    last_count = len(grp_vid)
    
    print("Sequential Grouping Analysis:")
    print(f"Start: {last_count} rows (variant_id only)")
    
    for col in test_cols:
        current_cols.append(col)
        # Group by current set + make_year to simulate "rows per year", 
        # but wait, the goal is "rows per generation".
        # So we just group by current_cols and count unique combos
        curr_count = len(df.groupby(current_cols).size())
        
        diff = curr_count - last_count
        if diff > 0:
            print(f" + Adding '{col}' increased rows to {curr_count} (+{diff})")
            
            # If big jump, investigate
            if diff > 100:
                print(f"   !!! '{col}' caused a major split. Checking why...")
                # Find a case where variant_id is same but col differs
                # We need to find duplicates in (current_cols - col) that differ in col
                prev_cols = [c for c in current_cols if c != col]
                
                # Check 5 examples
                subset = df.groupby(prev_cols)[col].unique()
                split_cases = subset[subset.apply(len) > 1]
                if not split_cases.empty:
                    print(f"   Examples of '{col}' variation:")
                    for idx, val in split_cases.head(3).items():
                        print(f"     Group {idx}: {val}")

        last_count = curr_count

except Exception as e:
    import traceback
    traceback.print_exc()

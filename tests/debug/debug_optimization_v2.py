import pandas as pd

output_path = r'd:\Car Data Scrapper\output\optimized_spinny_master.xlsx'

try:
    df = pd.read_excel(output_path)
    print(f"Loaded Optimized Data: {len(df)} rows")
    
    # Check for a variant_id with multiple rows
    vid_counts = df['variant_id'].value_counts()
    top_vid = vid_counts.index[0]
    print(f"Top Variant ID: {top_vid} with {vid_counts.iloc[0]} rows")
    
    subset = df[df['variant_id'] == top_vid]
    
    # 1. Check for duplicates in the grouping columns
    # If there are NO varying columns, then these rows are exact duplicates in the output?
    # No, because aggregation happens. 
    # But if input had (A, 2010), (A, 2010), (A, 2010)
    # GroupBy(A) -> (A, start=2010, end=2010, count=3) -> ONE ROW.
    
    # So if we have multiple rows in OUTPUT for same variant_id, 
    # it means the GROUPING KEYS (identity_cols) were different.
    
    varying_cols = []
    for col in subset.columns:
        if col in ['make_year_start', 'make_year_end', 'total_years_produced']:
            continue # These are results of agg, they might differ if groups differ
        if subset[col].nunique() > 1:
            varying_cols.append(col)
            print(f"Column '{col}' varies! {subset[col].unique()}")

    if not varying_cols:
        print("Strange... No varying identity columns found? Then why didn't they group?")
        print(subset.head().to_string())
    
except Exception as e:
    import traceback
    traceback.print_exc()

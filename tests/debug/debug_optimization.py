import pandas as pd

output_path = r'd:\Car Data Scrapper\output\optimized_spinny_master.xlsx'

try:
    df = pd.read_excel(output_path)
    print(f"Loaded Optimized Data: {len(df)} rows")
    
    # Check for a variant_id with multiple rows
    vid_counts = df['variant_id'].value_counts()
    print("\nTop 5 Variant IDs by row count:")
    print(vid_counts.head())
    
    # Inspect one high-count variant_id
    top_vid = vid_counts.index[0]
    print(f"\nInspecting Variant ID: {top_vid}")
    subset = df[df['variant_id'] == top_vid]
    
    # Find columns that are NOT constant in this subset
    varying_cols = []
    for col in subset.columns:
        if subset[col].nunique() > 1:
            varying_cols.append(col)
            
    print(f"Columns that vary for Variant ID {top_vid}:")
    print(varying_cols)
    
    print("\n--- Sample Data for Varying Cols ---")
    print(subset[varying_cols + ['make_year_start', 'make_year_end']].head(10))

except Exception as e:
    print(f"Error: {e}")

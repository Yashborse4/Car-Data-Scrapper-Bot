import pandas as pd

output_path = r'd:\Car Data Scrapper\output\optimized_spinny_master.xlsx'

try:
    df = pd.read_excel(output_path)
    
    # Filter for variant_id 1628 (which we know has 351 rows)
    subset = df[df['variant_id'] == 1628]
    
    # Pick the first brand/model in this subset
    brand = subset['brand_name'].iloc[0]
    model = subset['model_name'].iloc[0]
    
    print(f"Drilling down: Variant 1628, Brand: {brand}, Model: {model}")
    
    deep_subset = subset[(subset['brand_name'] == brand) & (subset['model_name'] == model)]
    print(f"Rows for this Brand/Model: {len(deep_subset)}")
    
    if len(deep_subset) > 1:
        # Find varying columns in this deep subset
        print("Varying columns within this specific car:")
        for col in deep_subset.columns:
            if col in ['make_year_start', 'make_year_end', 'total_years_produced']: continue
            
            unique_vals = deep_subset[col].unique()
            if len(unique_vals) > 1:
                print(f" - {col}: {unique_vals}")
                
        # print sample
        print("\nSample Rows:")
        print(deep_subset.head(10).to_string())
    else:
        print("This specific Brand/Model has only 1 row. Logic seems correct for this case.")
        # Try to find a case where it FAILED
        # Group by [Brand, Model, Variant] and count
        print("\nSearching for split variants...")
        counts = df.groupby(['brand_name', 'model_name', 'variant_name']).size()
        repeats = counts[counts > 1]
        if not repeats.empty:
            print(f"Found {len(repeats)} variants split into multiple rows.")
            top_split = repeats.index[0]
            print(f"Inspecting split variant: {top_split}")
            
            split_df = df[(df['brand_name'] == top_split[0]) & 
                          (df['model_name'] == top_split[1]) & 
                          (df['variant_name'] == top_split[2])]
            
            for col in split_df.columns:
                 if col in ['make_year_start', 'make_year_end', 'total_years_produced']: continue
                 if split_df[col].nunique() > 1:
                     print(f" - {col}: {split_df[col].unique()}")
        else:
            print("No split variants found! Maybe 28k IS the unique count?")

except Exception as e:
    import traceback
    traceback.print_exc()

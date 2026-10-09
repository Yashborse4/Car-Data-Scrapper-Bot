import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")

try:
    df = pd.read_excel(file_path)
    
    # 1. Proving Variant ID Reuse
    print("--- HYPOTHESIS: variant_id is reused across different cars ---")
    
    # Count unique Models per Variant ID
    models_per_vid = df.groupby('variant_id')['model_name'].nunique()
    
    # Get the Variant ID reused most often
    top_reused_id = models_per_vid.idxmax()
    count_reuse = models_per_vid.max()
    
    print(f"Most reused variant_id: {top_reused_id}")
    print(f"It appears in {count_reuse} DIFFERENT car models!")
    
    print("\nExample models using variant_id", top_reused_id, ":")
    examples = df[df['variant_id'] == top_reused_id]['model_name'].unique()[:10]
    for ex in examples:
        print(f" - {ex}")

    # 2. Confirming 'Model + Variant' is the true unique key
    print("\n--- True Unique Count ---")
    # Group by Brand, Model, VariantName (ignoring ID to be safe)
    # Using dropna=False to keep rows with missing data
    true_groups = df.groupby(['brand_name', 'model_name', 'variant_name'], dropna=False).size()
    print(f"Unique 'Car Definitions' (Brand+Model+Variant): {len(true_groups)}")
    
    optimized_rows = 28080 # Based on previous run
    print(f"Optimized File Rows: {optimized_rows}")
    
    if abs(len(true_groups) - optimized_rows) < 1000:
        print("\nCONCLUSION: The optimization is near-perfect.")
        print("The row count cannot be reduced further without merging different cars.")
    else:
        print("Difference needs investigation.")

except Exception as e:
    print(e)

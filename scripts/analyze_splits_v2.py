import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(REPO_ROOT, "data", "raw", "spinny_car_master_20260110_203905.xlsx")

try:
    df = pd.read_excel(file_path)
    
    # 1. Check if variant_id is unique globally
    unique_vids = df['variant_id'].nunique()
    print(f"Unique Variant IDs: {unique_vids}")
    
    # 2. Check if variant_id is unique PER BRAND
    unique_brand_vid = df.groupby(['brand_name', 'variant_id']).size()
    print(f"Unique Brand+VariantID combos: {len(unique_brand_vid)}")
    
    # 3. Check if variant_id is unique PER MODEL
    unique_model_vid = df.groupby(['model_name', 'variant_id']).size()
    print(f"Unique Model+VariantID combos: {len(unique_model_vid)}")

    # 4. Check variance of 'discontinued_year'
    # How many rows if we IGNORE discontinued_year?
    cols_no_year = [c for c in df.columns if c not in ['make_year', 'discontinued_year']]
    grp_no_year = df.groupby(cols_no_year).size()
    print(f"Rows if we ignore discontinued_year: {len(grp_no_year)}")
    
    # 5. Check variance of 'variant_full_name'
    cols_no_name = [c for c in df.columns if c not in ['make_year', 'variant_full_name']]
    grp_no_name = df.groupby(cols_no_name).size()
    print(f"Rows if we ignore variant_full_name: {len(grp_no_name)}")

    # 6. Check variance of BOTH
    cols_clean = [c for c in df.columns if c not in ['make_year', 'discontinued_year', 'variant_full_name']]
    grp_clean = df.groupby(cols_clean).size()
    print(f"Rows if we ignore BOTH: {len(grp_clean)}")

except Exception as e:
    print(e)

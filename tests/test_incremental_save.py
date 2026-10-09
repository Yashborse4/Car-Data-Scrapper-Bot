import os
import sys
import shutil
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from spinny_scraper import save_incrementally

OUTPUT_FILE = "test_incremental.xlsx"

def test_incremental_save():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    # Batch 1
    rows1 = [
        {"variant_id": 1, "brand_name": "TestBrand", "model_name": "ModelA", "make_year": 2020},
        {"variant_id": 2, "brand_name": "TestBrand", "model_name": "ModelA", "make_year": 2021},
    ]
    print("Saving batch 1...")
    save_incrementally(rows1, OUTPUT_FILE)
    
    assert os.path.exists(OUTPUT_FILE)
    df1 = pd.read_excel(OUTPUT_FILE)
    print(f"Batch 1 saved. Rows: {len(df1)}")
    assert len(df1) == 2
    assert "brand_name" in df1.columns
    
    # Batch 2 (Appeal)
    rows2 = [
        {"variant_id": 3, "brand_name": "TestBrand", "model_name": "ModelB", "make_year": 2022},
    ]
    print("Saving batch 2...")
    save_incrementally(rows2, OUTPUT_FILE)
    
    df2 = pd.read_excel(OUTPUT_FILE)
    print(f"Batch 2 saved. Total Rows: {len(df2)}")
    assert len(df2) == 3
    assert df2.iloc[2]["model_name"] == "ModelB"
    
    print("✅ Incremental save verification passed!")
    
    # Cleanup
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

if __name__ == "__main__":
    test_incremental_save()

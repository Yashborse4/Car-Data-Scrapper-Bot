import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
import logging
import sys
import json

# Disable logging
logging.basicConfig(level=logging.CRITICAL)

from spinny_scraper import SpinnyAPIClient

def debug_bmw():
    client = SpinnyAPIClient()
    
    print("Fetching brands...")
    brands = client.get_all_brands()
    bmw = next((b for b in brands if "BMW" in b['display_name']), None)
    
    if not bmw:
        print("BMW not found!")
        return

    print(f"Scanning BMW (ID: {bmw['id']})...")
    
    # Check 2015, 2018
    for year in [2015, 2018]:
        print(f"\nYear {year}:")
        models = client.get_models(bmw['id'], year)
        if not models:
            print("  No models.")
            continue
            
        print(f"  Found {len(models)} models.")
        for model in models[:2]: # Check first 2 models
            print(f"    Checking Model: {model['display_name']} (ID: {model['id']})")
            variants = client.get_variants(model['id'], year)
            if variants:
                print(f"      Found {len(variants)} variants.")
                v = variants[0]
                print(f"      Example Variant: {v.get('display_name')}")
                print(f"      full_name: {v.get('full_name')}")
            else:
                print(f"      ⚠️ No variants found for this model.")

if __name__ == "__main__":
    debug_bmw()

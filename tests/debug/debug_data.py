import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from spinny_scraper import SpinnyAPIClient
import json

def debug_data():
    client = SpinnyAPIClient()
    
    print("--- BRANDS ---")
    brands = client.get_all_brands()
    print(f"Total Usable Brands: {len(brands)}")
    brand_names = [b['display_name'] for b in brands]
    print(f"Brands: {', '.join(brand_names)}")
    
    # Pick Audi to test
    target_brand = next((b for b in brands if "Audi" in b['display_name']), None)
    if not target_brand:
        print("Audi not found!")
        return

    print(f"\n--- MODELS for {target_brand['display_name']} (2020) ---")
    models = client.get_models(target_brand['id'], 2020)
    if not models:
        print("No models found for 2020")
        return
        
    target_model = models[0]
    print(f"Checking Model: {target_model['display_name']}")
    
    print(f"\n--- VARIANTS for {target_model['display_name']} ---")
    variants = client.get_variants(target_model['id'], 2020)
    
    if variants:
        v = variants[0]
        print(f"Keys in variant object: {list(v.keys())}")
        print(f"display_name: {v.get('display_name')}")
        print(f"name: {v.get('name')}")
        print(f"full_name: {v.get('full_name')}") # Check if this is None
        print(f"Raw Variant:\n{json.dumps(v, indent=2)}")
    else:
        print("No variants found")

if __name__ == "__main__":
    debug_data()

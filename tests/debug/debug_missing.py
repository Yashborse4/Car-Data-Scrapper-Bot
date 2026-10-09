import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
import logging
import sys

# Disable logging
logging.basicConfig(level=logging.CRITICAL)

from spinny_scraper import SpinnyAPIClient

def debug_missing_brands():
    client = SpinnyAPIClient()
    
    print("Fetching brands...")
    brands = client.get_all_brands()
    
    targets = ["BMW", "Datsun", "Ford"]
    
    for target in targets:
        brand = next((b for b in brands if b['display_name'] == target), None)
        if not brand:
            print(f"{target}: NOT FOUND in brands list")
            continue
            
        print(f"\nScanning {target} (ID: {brand['id']})...")
        found_any = False
        # Scan a few key years
        for year in [2015, 2018, 2020]:
            models = client.get_models(brand['id'], year)
            if models:
                print(f"  {year}: Found {len(models)} models (e.g. {models[0]['display_name']})")
                found_any = True
            else:
                print(f"  {year}: No models")
        
        if not found_any:
            print(f"⚠️ {target} appears to have NO models in sampled years!")

if __name__ == "__main__":
    debug_missing_brands()

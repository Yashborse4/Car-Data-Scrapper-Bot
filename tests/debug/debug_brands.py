import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
import logging
import sys

# Disable logging
logging.basicConfig(level=logging.CRITICAL)

from spinny_scraper import SpinnyAPIClient

def debug_data():
    client = SpinnyAPIClient()
    
    print("Fetching brands...")
    brands = client.get_all_brands()
    print(f"Total Usable Brands: {len(brands)}")
    
    brand_names = sorted([b['display_name'] for b in brands])
    print(f"Usable Brands List:\n{', '.join(brand_names)}")
    
    # Check specifically for BMW, Ford
    for name in ["Audi", "BMW", "Chevrolet", "Datsun", "Fiat", "Ford"]:
        present = name in brand_names
        print(f"{name}: {'✅ Present' if present else '❌ Missing'}")

if __name__ == "__main__":
    debug_data()

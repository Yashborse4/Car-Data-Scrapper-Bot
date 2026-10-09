
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from spinny_client import SpinnyClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_behavior():
    with SpinnyClient() as client:
        # 1. Get a Brand (e.g., Honda)
        brands = client.get_brands()
        honda_id = None
        for bid, name in brands.items():
            if "Honda" in name:
                honda_id = bid
                logger.info(f"Found Honda: ID {honda_id}")
                break
        
        if not honda_id:
            logger.error("Honda not found")
            return

        # 2. Get Models for a specific year (e.g., 2015)
        logger.info("Fetching models for Honda (2015)...")
        models_2015 = client.get_models(honda_id, 2015)
        
        target_model = None
        if models_2015:
            target_model = models_2015[0]
            logger.info(f"Checking Model: {target_model.get('display_name')} (ID: {target_model.get('id')})")
            
            # Check lifecycle data
            logger.info(f"Lifecycle Data in Model Response: Launch={target_model.get('launch_year')}, Discontinued={target_model.get('discontinued_year')}")
        else:
            logger.error("No models found for 2015")
            return

        if target_model:
            model_id = target_model.get('id')
            
            # 3. Test get_variants with year 2015
            logger.info(f"Fetching variants for Model {model_id} Year 2015...")
            variants_2015 = client.get_variants(model_id, 2015)
            logger.info(f"Variants found (2015): {len(variants_2015)}")
            if variants_2015:
                # Log first variant details
                v = variants_2015[0]
                logger.info(f"Sample Variant: {v.get('display_name')} (ID: {v.get('id')})")

            # 4. Test get_variants with year 2016 (does it return same IDs or different?)
            logger.info(f"Fetching variants for Model {model_id} Year 2016...")
            variants_2016 = client.get_variants(model_id, 2016)
            logger.info(f"Variants found (2016): {len(variants_2016)}")
             
            # Compare IDs
            ids_2015 = {v.get('id') for v in variants_2015}
            ids_2016 = {v.get('id') for v in variants_2016}
            
            common = ids_2015.intersection(ids_2016)
            logger.info(f"Common Variant IDs between years: {len(common)}")
            if len(common) == 0:
                logger.info("CONFIRMED: Variant IDs are year-specific.")
            else:
                logger.warning("WARNING: Variant IDs are shared across years (unexpected).")

if __name__ == "__main__":
    test_api_behavior()


import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from spinny_client import SpinnyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_no_year_variants():
    with SpinnyClient() as client:
        # Get Honda
        brands = client.get_brands()
        honda_id = 5 # known from previous logs
        
        # Get a model
        models = client.get_models(honda_id, 2015)
        if not models:
            logger.error("No models found")
            return
            
        model = models[0] # Amaze
        model_id = model['id']
        logger.info(f"Testing Model: {model.get('display_name')} (ID: {model_id})")
        
        # Try fetching variants WITHOUT year
        try:
            logger.info("Attempting get_variants_no_year...")
            # We need to bypass the client method wrapper if it enforces params, 
            # but let's check the client code first. 
            # The client code takes year as arg. We will call _make_request directly.
            
            endpoint = "/v3/api/catalogue/variant-list"
            params = {"model_id": model_id} # No make_year
            
            response = client._make_request(endpoint, params)
            results = response.get("results", [])
            
            logger.info(f"Variants found (No Year): {len(results)}")
            if results:
                logger.info(f"Sample: {results[0].get('display_name')}")
            else:
                logger.info("No variants returned when year is omitted.")
                
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    test_no_year_variants()

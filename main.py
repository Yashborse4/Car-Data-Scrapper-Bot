"""
Spinny Car Data Scraper - Main Entry Point
==========================================

This script scrapes all car data from Spinny catalog APIs using the optimized
2-phase approach (Model Discovery + Variant Fetching) with incremental Excel saves.
"""

import os
import sys
import logging
from datetime import datetime

# Add src/ to sys.path so modules in src can be imported directly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Ensure data and logs directories exist
os.makedirs(os.path.join(BASE_DIR, "data", "raw"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data", "processed"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

from spinny_scraper import scrape_spinny

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "scraper.log"), mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Spinny car data scraper."""
    start_time = datetime.now()
    logger.info(f"Scraper started at {start_time}")
    
    try:
        # Run the optimized scrape (handles logging, exporting, checkpoints internally)
        output_path = scrape_spinny(resume=True)
        
        if output_path:
            print(f"\n[SUCCESS] Data exported to: {output_path}")
        else:
            logger.warning("No data was scraped or process was interrupted.")
    
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user (Ctrl+C)")
        print("\n\n[WARNING] Scraper interrupted. Progress has been saved to checkpoint.")
        print("Run the script again to resume from where you left off.")
    
    except Exception as e:
        logger.exception(f"Fatal error during scraping: {e}")
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)
    
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Scraper finished. Duration: {duration}")
        print(f"\nTotal time: {duration}")


if __name__ == "__main__":
    main()

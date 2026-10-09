"""
Configuration settings for Spinny Car Data Scraper.
"""

# API Configuration
BASE_URL = "https://api.spinny.com"
MAKE_LIST_ENDPOINT = "/v3/api/catalogue/make-list"
MODEL_LIST_ENDPOINT = "/v3/api/catalogue/model-list"
VARIANT_LIST_ENDPOINT = "/v3/api/catalogue/variant-list"

# Request Headers
HEADERS = {
    "platform": "mweb_android",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://www.spinny.com",
    "referer": "https://www.spinny.com/",
}

# Rate Limiting Configuration
REQUEST_DELAY_SECONDS = 0.5  # Base delay between requests
JITTER_RANGE = 0.5  # Random jitter ± seconds
MAX_RETRIES = 10  # Maximum retry attempts
RETRY_BACKOFF_MULTIPLIER = 4  # Exponential backoff multiplier
MAX_RETRY_DELAY = 60  # Maximum delay between retries in seconds

# Scraping Configuration
YEAR_START = 2000
YEAR_END = 2025
DEFAULT_CITY = "bangalore"

# Output Configuration
OUTPUT_DIR = "output"
OUTPUT_FILENAME = "spinny_car_data.xlsx"
CHECKPOINT_FILENAME = "checkpoint.json"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

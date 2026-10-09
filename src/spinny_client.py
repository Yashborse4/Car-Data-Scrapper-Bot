"""
Spinny API Client with rate limiting and retry logic.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

import config

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is hit."""
    pass


class SpinnyClient:
    """
    API client for Spinny with built-in rate limiting and retry logic.
    
    Features:
    - Token bucket rate limiting
    - Exponential backoff with jitter
    - Connection pooling via session
    - Automatic retry on transient failures
    """
    
    def __init__(self):
        """Initialize the Spinny API client."""
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.last_request_time = 0
        self.request_count = 0
        
    def _wait_for_rate_limit(self) -> None:
        """
        Enforce rate limiting with jitter.
        Ensures minimum delay between requests with random variation.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate required delay with jitter
        base_delay = config.REQUEST_DELAY_SECONDS
        jitter = random.uniform(-config.JITTER_RANGE, config.JITTER_RANGE)
        required_delay = base_delay + jitter
        
        if elapsed < required_delay:
            sleep_time = required_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=config.RETRY_BACKOFF_MULTIPLIER,
            max=config.MAX_RETRY_DELAY
        ),
        retry=retry_if_exception_type((requests.RequestException, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with rate limiting and retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: When rate limit is hit (429)
            requests.RequestException: On network errors
        """
        self._wait_for_rate_limit()
        
        url = f"{config.BASE_URL}{endpoint}"
        logger.debug(f"Request #{self.request_count}: GET {url}")
        
        response = self.session.get(url, params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            logger.warning("Rate limit hit (429). Will retry with backoff.")
            raise RateLimitError("Rate limit exceeded")
        
        # Handle server errors (retry)
        if response.status_code >= 500:
            logger.warning(f"Server error ({response.status_code}). Will retry.")
            response.raise_for_status()
        
        # Handle client errors (don't retry)
        if response.status_code >= 400:
            logger.error(f"Client error ({response.status_code}): {response.text}")
            return {}
        
        return response.json()
    
    def get_brands(self) -> Dict[int, str]:
        """
        Get all brands as a dictionary mapping make_id to brand name.
        Uses the make-list API.
        
        Returns:
            Dictionary of {make_id: brand_name}
        """
        logger.info("Fetching brand list from make-list API...")
        
        response = self._make_request(config.MAKE_LIST_ENDPOINT)
        makes = response.get("results", [])
        
        brand_map = {}
        for make in makes:
            make_id = make.get("id")
            make_name = make.get("display_name")
            is_usable = make.get("is_usable", False)
            
            # Only include usable brands
            if make_id and make_name and is_usable:
                brand_map[make_id] = make_name
        
        logger.info(f"Found {len(brand_map)} usable brands out of {len(makes)} total")
        return brand_map
    
    def get_models(self, make_id: int, year: int) -> List[Dict[str, Any]]:
        """
        Get all models for a specific brand and year.
        
        Args:
            make_id: Brand ID
            year: Model year
            
        Returns:
            List of model dictionaries
        """
        logger.debug(f"Fetching models for make_id={make_id}, year={year}")
        params = {
            "make_id": make_id,
            "make_year": year,
        }
        
        response = self._make_request(config.MODEL_LIST_ENDPOINT, params)
        models = response.get("results", [])
        
        # Filter to only usable models
        usable_models = [m for m in models if m.get("is_usable", True)]
        logger.debug(f"Found {len(usable_models)} usable models for make_id={make_id}, year={year}")
        
        return usable_models
    
    def get_variants(self, model_id: int, year: int) -> List[Dict[str, Any]]:
        """
        Get all variants for a specific model and year.
        Handles pagination to get all results.
        
        Args:
            model_id: Model ID
            year: Model year
            
        Returns:
            List of variant dictionaries
        """
        logger.debug(f"Fetching variants for model_id={model_id}, year={year}")
        params = {
            "model_id": model_id,
            "make_year": year,
        }
        
        all_variants = []
        
        while True:
            response = self._make_request(config.VARIANT_LIST_ENDPOINT, params)
            variants = response.get("results", [])
            all_variants.extend(variants)
            
            # Check for next page
            next_url = response.get("next")
            if not next_url:
                break
                
            # Parse next URL to extract query parameters for the next request
            # Usually 'next' is a full URL, but we just want params or use the URL directly?
            # _make_request builds URL from endpoint. 
            # Safer way: update params with 'page' or just use the next_url directly if we refactor _make_request.
            # Easiest: Extract 'page' param from next_url
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                qs = parse_qs(parsed.query)
                if 'page' in qs:
                    params['page'] = qs['page'][0]
                else:
                    break
            except Exception as e:
                logger.warning(f"Failed to parse pagination URL: {e}")
                break
        
        logger.debug(f"Found {len(all_variants)} variants for model_id={model_id}, year={year}")
        return all_variants
    
    def close(self) -> None:
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info(f"Client closed. Total requests made: {self.request_count}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

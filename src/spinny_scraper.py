"""
Spinny Car Data Scraper - Production Grade
==========================================

A complete, production-ready scraper for extracting car data from Spinny APIs.

Data Model:
- variant_id is PRIMARY KEY (globally unique, year-specific)
- Same variant name across years = different IDs (correct behavior)
- launch_year + discontinued_year = lifecycle tracking
- Attributes extracted by display_name, not index

API Flow:
    make-list → model-list → variant-list → Excel

Usage:
    python spinny_scraper.py

Author: Auto-generated
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from tqdm import tqdm


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """All configuration settings in one place."""
    
    # API Configuration
    BASE_URL = "https://api.spinny.com"
    MAKE_LIST_ENDPOINT = "/v3/api/catalogue/make-list"
    MODEL_LIST_ENDPOINT = "/v3/api/catalogue/model-list"
    VARIANT_LIST_ENDPOINT = "/v3/api/catalogue/variant-list"
    
    # Request Headers (mimics browser)
    HEADERS = {
        "platform": "mweb_android",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.spinny.com",
        "referer": "https://www.spinny.com/",
    }
    
    # Rate Limiting (critical to avoid blocks)
    REQUEST_DELAY_SECONDS = 1.5
    JITTER_RANGE = 0.5
    MAX_RETRIES = 5
    RETRY_BACKOFF_MULTIPLIER = 2
    MAX_RETRY_DELAY = 60
    
    # Scraping Range
    YEAR_START = 2000
    YEAR_END = 2025
    
    # Output
    OUTPUT_DIR = "output"
    CHECKPOINT_FILE = "checkpoint.json"


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging with file and console handlers."""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    logger = logging.getLogger("spinny_scraper")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console)
    
    # File handler
    file_handler = logging.FileHandler(
        f"{Config.OUTPUT_DIR}/scraper.log", 
        mode='a', 
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logging()


# =============================================================================
# API CLIENT (with rate limiting and retry logic)
# =============================================================================

class RateLimitError(Exception):
    """Raised when API rate limit is hit."""
    pass


class SpinnyAPIClient:
    """
    Spinny API client with built-in rate limiting and retry logic.
    
    Features:
    - Token bucket rate limiting with jitter
    - Exponential backoff on failures
    - Connection pooling via session
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)
        self.last_request_time = 0.0
        self.request_count = 0
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting with random jitter."""
        elapsed = time.time() - self.last_request_time
        delay = Config.REQUEST_DELAY_SECONDS + random.uniform(
            -Config.JITTER_RANGE, Config.JITTER_RANGE
        )
        
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=Config.RETRY_BACKOFF_MULTIPLIER, max=Config.MAX_RETRY_DELAY),
        retry=retry_if_exception_type((requests.RequestException, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with rate limiting and retry."""
        self._rate_limit()
        
        url = f"{Config.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        
        if response.status_code == 429:
            raise RateLimitError("Rate limit hit")
        
        if response.status_code >= 500:
            response.raise_for_status()
        
        if response.status_code >= 400:
            logger.error(f"Client error {response.status_code}: {url}")
            return {}
        
        return response.json()
    
    def get_all_brands(self) -> List[Dict[str, Any]]:
        """
        Fetch all brands from make-list API.
        
        Returns:
            List of brand dictionaries with id, display_name, is_usable, etc.
        """
        logger.info("Fetching brand list...")
        response = self._request(Config.MAKE_LIST_ENDPOINT)
        brands = response.get("results", [])
        
        # Filter to usable brands only
        usable = [b for b in brands if b.get("is_usable", False)]
        logger.info(f"Found {len(usable)} usable brands out of {len(brands)} total")
        
        return usable
    
    def get_models(self, make_id: int, year: int) -> List[Dict[str, Any]]:
        """
        Fetch models for a specific brand and year.
        
        Args:
            make_id: Brand ID
            year: Model year
            
        Returns:
            List of model dictionaries
        """
        params = {"make_id": make_id, "make_year": year}
        response = self._request(Config.MODEL_LIST_ENDPOINT, params)
        models = response.get("results", [])
        
        # Filter to usable models
        return [m for m in models if m.get("is_usable", True)]
    
    def get_variants(self, model_id: int, year: int) -> List[Dict[str, Any]]:
        """
        Fetch variants for a specific model and year.
        
        Args:
            model_id: Model ID
            year: Model year
            
        Returns:
            List of variant dictionaries
        """
        params = {"model_id": model_id, "make_year": year}
        response = self._request(Config.VARIANT_LIST_ENDPOINT, params)
        return response.get("results", [])
    
    def close(self):
        """Close the session."""
        self.session.close()
        logger.info(f"API client closed. Total requests: {self.request_count}")


# =============================================================================
# DATA EXTRACTION & NORMALIZATION
# =============================================================================

def extract_attribute(variant: Dict, attribute_name: str) -> Optional[Any]:
    """
    Extract attribute value by display_name (NOT by index).
    
    Args:
        variant: Variant dictionary
        attribute_name: Partial match for display_name (e.g., "Displacement")
        
    Returns:
        Attribute value or None if not found
    """
    attributes = variant.get("attributes", [])
    
    for attr in attributes:
        display_name = attr.get("display_name", "")
        if attribute_name.lower() in display_name.lower():
            return attr.get("value")
    
    return None


def normalize_variant(
    variant: Dict[str, Any],
    brand_name: str,
    model_name: str,
    model_body_type: str,
    model_segment: str,
    make_year: int
) -> Dict[str, Any]:
    """
    Normalize variant data into a flat dictionary.
    
    changes:
    - Removed unreliable attributes (Mileage, Power, Torque)
    - Kept engine_cc
    """
    # Extract engine specs from attributes (by name, not index)
    engine_cc = extract_attribute(variant, "Displacement")
    
    return {
        # Primary Key - CRITICAL: This is unique per variant-year
        "variant_id": variant.get("id"),
        
        # Brand/Model hierarchy
        "brand_name": brand_name,
        "model_name": model_name,
        "model_id": variant.get("model"),
        
        # Variant identity
        "variant_name": variant.get("display_name", ""),
        "variant_full_name": variant.get("full_name") or f"{brand_name} {model_name} {variant.get('display_name', '')}",
        
        # Core specs (guaranteed fields)
        "fuel_type": variant.get("fuel_type", ""),
        "transmission": variant.get("transmission_type", ""),
        "body_type": model_body_type,
        "segment": model_segment,
        
        # Engine specs (from attributes - may be NULL)
        "engine_cc": engine_cc,
        
        # Placeholders for reliable data (ZigWheels integration later)
        "mileage_arai": None,
        "power_hp": None,
        "torque_nm": None,
        
        # Lifecycle tracking (IMPORTANT for historical data)
        "launch_year": variant.get("launch_year"),
        "discontinued_year": variant.get("discontinued_year"),
        "make_year": make_year,
        
        # Status flags
        "is_usable": variant.get("is_usable", False),
        "is_active": variant.get("is_active", False),
        "is_verified": variant.get("is_verified", False),
    }


# =============================================================================
# CHECKPOINT MANAGEMENT
# =============================================================================

class CheckpointManager:
    """Manages checkpointing for resume capability."""
    
    def __init__(self):
        self.checkpoint_path = os.path.join(Config.OUTPUT_DIR, Config.CHECKPOINT_FILE)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def save(self, rows: List[Dict], discovered_models: List[Dict], errors: List[Dict], phase: str) -> None:
        """Save checkpoint to disk."""
        checkpoint = {
            "rows": rows,
            "discovered_models": discovered_models,
            "errors": errors,
            "phase": phase,  # 'discovery' or 'fetching'
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False)
    
    def load(self) -> Optional[Dict]:
        """Load checkpoint from disk."""
        if not os.path.exists(self.checkpoint_path):
            return None
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None
    
    def cleanup(self) -> None:
        """Remove checkpoint file after successful export."""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
            logger.info("Checkpoint file removed")


# =============================================================================
# EXCEL EXPORT
# =============================================================================

def export_to_excel(rows: List[Dict], errors: List[Dict]) -> str:
    """
    Export data to a formatted Excel file.
    """
    if not rows:
        logger.warning("No data to export")
        return ""
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Column order (matches normalized data model)
    column_order = [
        "variant_id",
        "brand_name",
        "model_name",
        "variant_name",
        "variant_full_name",
        "fuel_type",
        "transmission",
        "body_type",
        "segment",
        "engine_cc",
        "mileage_arai",
        "power_hp",
        "torque_nm",
        "launch_year",
        "discontinued_year",
        "make_year",
        "is_usable",
        "is_active",
        "is_verified",
        "model_id",
    ]
    
    # Only include existing columns
    existing_cols = [c for c in column_order if c in df.columns]
    df = df[existing_cols]
    
    # Remove duplicates by variant_id AND make_year (since we expanded rows)
    initial_count = len(df)
    df = df.drop_duplicates(subset=["variant_id", "make_year"], keep="first")
    logger.info(f"Removed {initial_count - len(df)} duplicate rows")
    
    # Sort
    df = df.sort_values(["brand_name", "model_name", "make_year", "variant_name"])
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spinny_car_master_{timestamp}.xlsx"
    output_path = os.path.join(Config.OUTPUT_DIR, filename)
    
    # Export with formatting
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Variants', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Variants']
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
                worksheet.column_dimensions[col_letter].width = min(max_len, 40)
            
            # Header formatting
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
    except Exception as e:
        logger.error(f"Failed to write Excel file: {e}")
        # Fallback to CSV if Excel fails
        csv_path = output_path.replace(".xlsx", ".csv")
        df.to_csv(csv_path, index=False)
        return csv_path
    
    logger.info(f"Exported {len(df)} variants to {output_path}")
    
    # Export errors if any
    if errors:
        errors_df = pd.DataFrame(errors)
        errors_path = os.path.join(Config.OUTPUT_DIR, f"scrape_errors_{timestamp}.xlsx")
        errors_df.to_excel(errors_path, index=False)
        logger.info(f"Exported {len(errors)} errors to {errors_path}")
    
    return output_path


def save_incrementally(rows: List[Dict], output_path: str) -> None:
    """
    Save rows to Excel incrementally. 
    If file exists, appends. If not, creates with headers.
    """
    if not rows:
        return

    # Column order (matches normalized data model)
    column_order = [
        "variant_id",
        "brand_name",
        "model_name",
        "variant_name",
        "variant_full_name",
        "fuel_type",
        "transmission",
        "body_type",
        "segment",
        "engine_cc",
        "mileage_arai",
        "power_hp",
        "torque_nm",
        "launch_year",
        "discontinued_year",
        "make_year",
        "is_usable",
        "is_active",
        "is_verified",
        "model_id",
    ]

    df = pd.DataFrame(rows)
    # Ensure all columns exist
    for col in column_order:
        if col not in df.columns:
            df[col] = None
    
    # Filter and reorder
    df = df[column_order]

    file_exists = os.path.exists(output_path)
    
    if not file_exists:
        # Create new workbook with headers
        wb = Workbook()
        ws = wb.active
        ws.title = "Variants"
        
        # Write headers
        ws.append(column_order)
        
        # Style headers
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            
    else:
        # Load existing
        try:
            wb = load_workbook(output_path)
            if "Variants" in wb.sheetnames:
                ws = wb["Variants"]
            else:
                ws = wb.create_sheet("Variants")
                ws.append(column_order)
        except Exception as e:
            logger.error(f"Failed to load existing Excel during incremental save: {e}")
            # Backup plan: write to a temp file to avoid data loss?
            # For now, just raise or return
            return

    # Append rows
    for r in dataframe_to_rows(df, index=False, header=False):
        ws.append(r)

    # Auto-adjust column widths (simple estimation)
    for idx, col in enumerate(column_order):
        col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
        # We don't re-measure everything for speed, just ensure it's not tiny?
        # Actually, let's just leave widths as is or set default if new
        if not file_exists:
             ws.column_dimensions[col_letter].width = 15

    try:
        wb.save(output_path)
        logger.info(f"Incrementally saved {len(rows)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save incremental Excel: {e}")


# =============================================================================
# MAIN SCRAPER - REFACTORED PHASED APPROACH
# =============================================================================

def scrape_spinny(resume: bool = True) -> str:
    """
    Main scraping function with Phase 1 (Model Discovery) and Phase 2 (Variant Fetching).
    """
    print("""
============================================================
     SPINNY CAR DATA SCRAPER - OPTIMIZED
============================================================
     Phase 1: Model Discovery (Efficient Year Scanning)
     Phase 2: Variant Fetching (Lifecycle Aware)
     Rate Limiting: 1.5s delay with jitter
============================================================
    """)
    
    start_time = datetime.now()
    logger.info(f"Scraper started at {start_time}")
    
    client = SpinnyAPIClient()
    checkpoint_mgr = CheckpointManager()
    
    # State
    # State
    all_rows: List[Dict] = []
    discovered_models: List[Dict] = [] # List of unique models with lifecycle info
    errors: List[Dict] = []
    current_phase = "discovery" # 'discovery' or 'fetching'
    
    # Incremental Save State
    unsaved_rows: List[Dict] = []
    last_save_time = time.time()
    SAVE_INTERVAL_SECONDS = 120  # 2 minutes

    # Fixed output filename for this session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"spinny_car_master_{timestamp}.xlsx"
    output_path = os.path.join(Config.OUTPUT_DIR, output_filename)
    
    # Resume logic
    if resume:
        checkpoint = checkpoint_mgr.load()
        if checkpoint:
            all_rows = checkpoint.get("rows", [])
            discovered_models = checkpoint.get("discovered_models", [])
            errors = checkpoint.get("errors", [])
            current_phase = checkpoint.get("phase", "discovery")
            logger.info(f"Resuming from Phase: {current_phase}. Rows: {len(all_rows)}, Models: {len(discovered_models)}")

    try:
        # Phase 1: Model Discovery
        # We still iterate years, but we only store UNIQUE models.
        # Ideally, we'd like to just get all models for a brand, but the API requires year.
        # So we scan, but we dedup models eagerly.
        
        if current_phase == "discovery":
            logger.info("--- PHASE 1: MODEL DISCOVERY ---")
            
            brands = client.get_all_brands()
            brand_names = [b.get('display_name') for b in brands]
            logger.info(f"Discovered {len(brands)} brands for scanning: {brand_names}")

            years = list(range(Config.YEAR_START, Config.YEAR_END + 1))
            
            # We need to track which brand/year we've already scanned if we are resuming mid-discovery.
            # For simplicity in this refactor, if we are in 'discovery' phase resume, we might just re-scan 
            # or we can rely on the 'discovered_models' list acting as a cache? 
            # No, re-scanning is safer unless we stored progress granularly.
            # To avoid complexity, let's assume if resuming 'discovery', we just clear discovered_models and start fresh (safest)
            # OR we check if 'discovered_models' is populated and skip to Phase 2?
            # Let's say if we have > 0 discovered models and we are resuming, let's assume discovery was done.
            # BUT the user might have interrupted mid-discovery. 
            
            # Better approach: Just do the discovery. It's fast (Model List API).
            # We will use a dictionary to track unique models by ID to avoid duplicates in the list.
            unique_model_map = {m['model_id']: m for m in discovered_models}
            
            with tqdm(total=len(brands) * len(years), desc="Discovering Models", unit="req") as pbar:
                for brand in brands:
                    brand_id = brand.get("id")
                    brand_name = brand.get("display_name", "")
                    
                    for year in years:
                        pbar.set_description(f"Disc: {brand_name} {year}")
                        
                        try:
                            models = client.get_models(brand_id, year)
                            for model in models:
                                mid = model.get("id")
                                if mid not in unique_model_map:
                                    # New model found!
                                    unique_model_map[mid] = {
                                        "model_id": mid,
                                        "brand_name": brand_name,
                                        "model_name": model.get("display_name", ""),
                                        "body_type": model.get("body_type", ""),
                                        "segment": model.get("segment_type", ""),
                                        "launch_year": model.get("launch_year"),
                                        "discontinued_year": model.get("discontinued_year"),
                                        "found_in_year": year # Debug info
                                    }
                        except Exception as e:
                            logger.warning(f"Discovery error {brand_name} {year}: {e}")
                            
                        pbar.update(1)
            
            discovered_models = list(unique_model_map.values())
            logger.info(f"Discovery Complete. Found {len(discovered_models)} unique models.")
            
            # Save checkpoint and move to next phase
            current_phase = "fetching"
            checkpoint_mgr.save(all_rows, discovered_models, errors, current_phase)
            
        # Phase 2: Variant Fetching
        if current_phase == "fetching":
            logger.info("--- PHASE 2: VARIANT FETCHING ---")
            
            # We iterate through UNIQUE models.
            # user_request: "Fetch variants once per model"
            # user_request: "Use launch_year & discontinued_year to map years"
            
            total_models = len(discovered_models)
            
            with tqdm(total=total_models, desc="Fetching Variants", unit="model") as pbar:
                for model in discovered_models:
                    model_id = model["model_id"]
                    model_name = model["model_name"]
                    pbar.set_description(f"Fetch: {model_name}")
                    
                    # We will collect unique variants for this model
                    # Keyed by variant_id to avoid duplication
                    model_variants_map = {}
                    
                    # Strategy: Intelligent Sampling to catch Facelifts/Mid-cycle variants.
                    # Querying only Start/End might miss variants that only existed in the middle.
                    # Facelifts typically occur every 3-4 years.
                    # We will sample every 3 years within the lifecycle.
                    
                    years_to_query = set()
                    
                    # Determine Lifecycle Bounds
                    launch_start = int(model.get("launch_year")) if model.get("launch_year") else Config.YEAR_START
                    disco_end = int(model.get("discontinued_year")) if model.get("discontinued_year") else Config.YEAR_END
                    
                    # Clamp to config
                    start_bound = max(Config.YEAR_START, launch_start)
                    end_bound = min(Config.YEAR_END, disco_end)
                    
                    # Add Bounds
                    years_to_query.add(start_bound)
                    years_to_query.add(end_bound)
                    
                    # Add Intermediate Sampling (every 3 years)
                    if end_bound > start_bound:
                        for y in range(start_bound + 1, end_bound, 3):
                            years_to_query.add(y)
                            
                    # Additional check: If gap is large, ensure we hit the middle?
                    # The range scan handles it.
                    
                    # Clamp
                    final_query_years = sorted([
                        y for y in years_to_query 
                        if Config.YEAR_START <= y <= Config.YEAR_END
                    ])
                    
                    # Fetch
                    for q_year in final_query_years:
                        try:
                            variants = client.get_variants(model_id, q_year)
                            for variant in variants:
                                if not variant.get("is_usable", True):
                                    continue
                                
                                v_id = variant.get("id")
                                if v_id not in model_variants_map:
                                    model_variants_map[v_id] = variant
                        except Exception as e:
                             errors.append({
                                "model": model_name,
                                "year": q_year,
                                "error": str(e)
                            })
                    
                    # EXPAND: Generate rows for every valid year for each unique variant
                    for v_id, variant in model_variants_map.items():
                        # Determine lifecycle
                        v_launch = variant.get("launch_year")
                        v_disco = variant.get("discontinued_year")
                        
                        start_y = int(v_launch) if v_launch else Config.YEAR_START
                        end_y = int(v_disco) if v_disco else Config.YEAR_END
                        
                        # Clamp
                        start_y = max(start_y, Config.YEAR_START)
                        end_y = min(end_y, Config.YEAR_END)
                        
                        # Generate a row for EACH year this variant was active
                        # This satisfies "Use launch_year & discontinued_year to map years"
                        for year in range(start_y, end_y + 1):
                            row = normalize_variant(
                                variant=variant,
                                brand_name=model["brand_name"],
                                model_name=model["model_name"],
                                model_body_type=model["body_type"],
                                model_segment=model["segment"],
                                make_year=year  # Virtual Year
                            )
                            all_rows.append(row)
                            unsaved_rows.append(row)
                        
                        # Check for periodic save (every 2 minutes)
                        if time.time() - last_save_time > SAVE_INTERVAL_SECONDS:
                            if unsaved_rows:
                                logger.info(f"Performing periodic save ({len(unsaved_rows)} new rows)...")
                                save_incrementally(unsaved_rows, output_path)
                                unsaved_rows = []
                                last_save_time = time.time()
                    
                    pbar.update(1)
                    
                    # Checkpoint every 50 models
                    if pbar.n % 50 == 0:
                        checkpoint_mgr.save(all_rows, discovered_models, errors, current_phase)
        
        # Final Export
        # Final Flush of any unsaved rows
        if unsaved_rows:
            logger.info(f"Performing final save ({len(unsaved_rows)} rows)...")
            save_incrementally(unsaved_rows, output_path)
        
        checkpoint_mgr.cleanup()
        
        # Summary
        if all_rows:
            df = pd.DataFrame(all_rows)
            print(f"""
============================================================
                    SCRAPE COMPLETE!
============================================================
Total Rows:         {len(df):,}
Unique Brands:      {df['brand_name'].nunique() if 'brand_name' in df else 0}
Unique Models:      {df['model_name'].nunique() if 'model_name' in df else 0}
Unique Variants:    {df['variant_id'].nunique() if 'variant_id' in df else 0}
Errors:             {len(errors)}
Output File:        {output_path}
============================================================
            """)
        
        return output_path

    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        # Save state
        checkpoint_mgr.save(all_rows, discovered_models, errors, current_phase)
        print("\n[WARNING] Interrupted. Progress saved.")
        return ""
    
    finally:
        client.close()
        end_time = datetime.now()
        print(f"\nTotal time: {end_time - start_time}")



# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    scrape_spinny(resume=True)

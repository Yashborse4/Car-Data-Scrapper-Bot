"""
Spinny Car Data Scraper with checkpoint support and progress tracking.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
from tqdm import tqdm

import config
from spinny_client import SpinnyClient

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class SpinnyScraper:
    """
    Main scraper class for extracting car data from Spinny APIs.
    
    Features:
    - Progress tracking with tqdm
    - Checkpoint saving for resume capability
    - Data normalization
    - Excel export
    """
    
    def __init__(self):
        """Initialize the scraper."""
        self.client = SpinnyClient()
        self.all_rows: List[Dict[str, Any]] = []
        self.checkpoint_path = os.path.join(config.OUTPUT_DIR, config.CHECKPOINT_FILENAME)
        self.errors: List[Dict[str, Any]] = []
        
        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint from file if exists.
        
        Returns:
            Checkpoint data or None if not found
        """
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {len(checkpoint.get('rows', []))} rows")
                return checkpoint
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return None
    
    def save_checkpoint(self, current_brand_id: int, current_year: int) -> None:
        """
        Save current progress to checkpoint file.
        
        Args:
            current_brand_id: Currently processing brand ID
            current_year: Currently processing year
        """
        checkpoint = {
            "rows": self.all_rows,
            "current_brand_id": current_brand_id,
            "current_year": current_year,
            "timestamp": datetime.now().isoformat(),
            "errors": self.errors
        }
        
        try:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False)
            logger.debug(f"Checkpoint saved: {len(self.all_rows)} rows")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
    
    def extract_attribute(self, variant: Dict[str, Any], attribute_id: str) -> Any:
        """
        Extract an attribute value from variant's attributes list.
        
        Args:
            variant: Variant dictionary
            attribute_id: The attribute_id to search for (partial match)
            
        Returns:
            Attribute value or empty string if not found
        """
        attributes = variant.get("attributes", [])
        for attr in attributes:
            if attribute_id in attr.get("attribute_id", ""):
                return attr.get("value", "")
        return ""
    
    def normalize_variant(
        self,
        variant: Dict[str, Any],
        brand_name: str,
        model_name: str,
        model_body_type: str,
        year: int
    ) -> Dict[str, Any]:
        """
        Normalize variant data into a flat dictionary.
        
        Args:
            variant: Raw variant data from API
            brand_name: Brand name
            model_name: Model name
            model_body_type: Body type from model
            year: Make year (parameter passed to API)
            
        Returns:
            Normalized dictionary for DataFrame
        """
        # Extract engine CC from attributes
        engine_cc = self.extract_attribute(variant, "displacement")
        mileage = self.extract_attribute(variant, "mileage")
        
        return {
            "brand_name": brand_name,
            "model_name": model_name,
            "variant_name": variant.get("display_name", variant.get("name", "")),
            "full_name": variant.get("full_name", ""),
            "fuel_type": variant.get("fuel_type", ""),
            "transmission": variant.get("transmission_type", ""),
            "body_type": model_body_type,
            "engine_cc": engine_cc,
            "mileage_arai": mileage,
            "launch_year": variant.get("launch_year", ""),
            "make_year": year,
            "variant_id": variant.get("id", ""),
            "model_id": variant.get("model", ""),
            "is_usable": variant.get("is_usable", False),
        }
    
    def scrape_all(self, resume: bool = True, target_brands: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape all car data from Spinny.
        
        Args:
            resume: Whether to resume from checkpoint if available
            target_brands: Optional list of specific brand names to scrape
            
        Returns:
            List of all scraped rows
        """
        logger.info("Starting Spinny car data scrape...")
        
        # Load checkpoint if resuming
        start_brand_id = None
        start_year = None
        
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                self.all_rows = checkpoint.get("rows", [])
                start_brand_id = checkpoint.get("current_brand_id")
                start_year = checkpoint.get("current_year")
                self.errors = checkpoint.get("errors", [])
                logger.info(f"Resuming from brand_id={start_brand_id}, year={start_year}")
        
        # Get all brands
        all_brands = self.client.get_brands()
        
        # Filter brands if target_brands is specified
        if target_brands:
            brands = {}
            target_brands_lower = [b.lower() for b in target_brands]
            logger.info(f"Filtering for brands: {target_brands}")
            
            for brand_id, brand_name in all_brands.items():
                if brand_name.lower() in target_brands_lower:
                    brands[brand_id] = brand_name
            
            if not brands:
                logger.warning(f"No matching brands found for {target_brands}. Available: {list(all_brands.values())}")
        else:
            brands = all_brands

        logger.info(f"Processing {len(brands)} brands across years {config.YEAR_START}-{config.YEAR_END}")
        
        # Calculate total iterations for progress bar
        years = list(range(config.YEAR_START, config.YEAR_END + 1))
        total_iterations = len(brands) * len(years)
        
        # Track if we should skip (for resume)
        should_skip = start_brand_id is not None
        
        # Progress bar for brands
        with tqdm(total=total_iterations, desc="Scraping", unit="brand-year") as pbar:
            for make_id, brand_name in brands.items():
                for year in years:
                    # Handle resume logic
                    if should_skip:
                        if make_id == start_brand_id and year == start_year:
                            should_skip = False
                        else:
                            pbar.update(1)
                            continue
                    
                    pbar.set_description(f"{brand_name} ({year})")
                    
                    try:
                        # Get models for this brand/year
                        models = self.client.get_models(make_id, year)
                        
                        for model in models:
                            model_id = model.get("id")
                            model_name = model.get("display_name", model.get("name", ""))
                            model_body_type = model.get("body_type", "")
                            
                            if not model_id:
                                continue
                            
                            try:
                                # Get variants for this model/year
                                variants = self.client.get_variants(model_id, year)
                                
                                for variant in variants:
                                    # Only include usable variants
                                    if not variant.get("is_usable", True):
                                        continue
                                    
                                    row = self.normalize_variant(
                                        variant, brand_name, model_name, model_body_type, year
                                    )
                                    self.all_rows.append(row)
                                    
                            except Exception as e:
                                error_info = {
                                    "brand": brand_name,
                                    "model": model_name,
                                    "year": year,
                                    "error": str(e)
                                }
                                self.errors.append(error_info)
                                logger.warning(f"Error fetching variants: {e}")
                        
                    except Exception as e:
                        error_info = {
                            "brand": brand_name,
                            "year": year,
                            "error": str(e)
                        }
                        self.errors.append(error_info)
                        logger.warning(f"Error fetching models: {e}")
                    
                    # Save checkpoint every 10 iterations
                    if pbar.n % 10 == 0:
                        self.save_checkpoint(make_id, year)
                    
                    pbar.update(1)
        
        # Final checkpoint save
        if self.all_rows:
            self.save_checkpoint(list(brands.keys())[-1], years[-1])
        
        logger.info(f"Scraping complete. Total rows: {len(self.all_rows)}, Errors: {len(self.errors)}")
        return self.all_rows
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """
        Export scraped data to Excel file.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            Path to the exported file
        """
        if not self.all_rows:
            logger.warning("No data to export")
            return ""
        
        # Create DataFrame
        df = pd.DataFrame(self.all_rows)
        
        # Reorder columns
        column_order = [
            "brand_name",
            "model_name",
            "variant_name",
            "full_name",
            "make_year",
            "launch_year",
            "fuel_type",
            "transmission",
            "body_type",
            "engine_cc",
            "mileage_arai",
            "is_usable",
            "variant_id",
            "model_id",
        ]
        
        # Only include columns that exist
        existing_cols = [c for c in column_order if c in df.columns]
        df = df[existing_cols]
        
        # Remove duplicates based on variant_id to avoid duplicate entries
        initial_count = len(df)
        df = df.drop_duplicates(subset=["variant_id"], keep="first")
        logger.info(f"Removed {initial_count - len(df)} duplicate rows")
        
        # Sort by brand, model, year, variant
        df = df.sort_values(["brand_name", "model_name", "make_year", "variant_name"])
        
        # Generate filename with timestamp
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spinny_car_data_{timestamp}.xlsx"
        
        output_path = os.path.join(config.OUTPUT_DIR, filename)
        
        # Export to Excel with formatting
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Car Data', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Car Data']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                # Excel column index (A=1, B=2, etc.)
                col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
                worksheet.column_dimensions[col_letter].width = min(max_length, 50)
        
        logger.info(f"Exported {len(df)} rows to {output_path}")
        
        # Export errors if any
        if self.errors:
            errors_df = pd.DataFrame(self.errors)
            errors_path = os.path.join(config.OUTPUT_DIR, "scrape_errors.xlsx")
            errors_df.to_excel(errors_path, index=False)
            logger.info(f"Exported {len(self.errors)} errors to {errors_path}")
        
        # Cleanup checkpoint after successful export
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
            logger.info("Checkpoint file removed after successful export")
        
        return output_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the scraped data.
        
        Returns:
            Dictionary with statistics
        """
        if not self.all_rows:
            return {"total_rows": 0}
        
        df = pd.DataFrame(self.all_rows)
        
        return {
            "total_rows": len(df),
            "unique_brands": df["brand_name"].nunique() if "brand_name" in df.columns else 0,
            "unique_models": df["model_name"].nunique() if "model_name" in df.columns else 0,
            "unique_variants": df["variant_name"].nunique() if "variant_name" in df.columns else 0,
            "year_range": f"{df['make_year'].min()} - {df['make_year'].max()}" if "make_year" in df.columns else "N/A",
            "fuel_types": df["fuel_type"].dropna().unique().tolist() if "fuel_type" in df.columns else [],
            "transmissions": df["transmission"].dropna().unique().tolist() if "transmission" in df.columns else [],
            "errors": len(self.errors)
        }
    
    def close(self) -> None:
        """Cleanup resources."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

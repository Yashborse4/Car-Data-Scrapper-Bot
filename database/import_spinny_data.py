"""
PostgreSQL Ingestion Pipeline for Spinny Car Master Data
========================================================

Loads optimized car master dataset (Excel) directly into PostgreSQL
table `car_master`.

Usage:
    python database/import_spinny_data.py [--file path/to/file.xlsx]
"""

import os
import sys
import argparse
import datetime
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration defaults with environment variable overrides
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "carselling")
DB_USER = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Default Excel file path (relative to repo root)
DEFAULT_EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "data",
    "processed",
    "optimized_spinny_master.xlsx"
)

DDL_CREATE_TABLE = """
DROP TABLE IF EXISTS car_master CASCADE;
CREATE TABLE car_master (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255),
    make VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    variant VARCHAR(200),
    segment VARCHAR(50),
    engine_cc INTEGER,
    fuel_type VARCHAR(50),
    transmission VARCHAR(50),
    body_type VARCHAR(50),
    mileage_arai DOUBLE PRECISION,
    year_start INTEGER,
    year_end INTEGER,
    power_hp VARCHAR(255),
    torque_nm VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_car_master_make ON car_master(make);
CREATE INDEX idx_car_master_model ON car_master(model);
CREATE INDEX idx_car_master_external_id ON car_master(external_id);
"""

def import_data(excel_path: str = DEFAULT_EXCEL_PATH) -> None:
    """Reads Excel file and imports records into PostgreSQL."""
    if not os.path.exists(excel_path):
        # Fallback to current directory if not found in default path
        local_fallback = os.path.basename(excel_path)
        if os.path.exists(local_fallback):
            excel_path = local_fallback
        else:
            print(f"[ERROR] Excel file not found at: {excel_path}")
            sys.exit(1)

    try:
        print(f"Reading dataset from: {excel_path}...")
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df):,} records from Excel.")

        column_mapping = {
            'variant_id': 'external_id',
            'brand_name': 'make',
            'model_name': 'model',
            'variant_name': 'variant',
            'segment': 'segment',
            'engine_cc': 'engine_cc',
            'fuel_type': 'fuel_type',
            'transmission': 'transmission',
            'body_type': 'body_type',
            'mileage_arai': 'mileage_arai',
            'make_year_start': 'year_start',
            'make_year_end': 'year_end',
            'power_hp': 'power_hp',
            'torque_nm': 'torque_nm'
        }

        available_cols = [c for c in column_mapping.keys() if c in df.columns]
        df_db = df[available_cols].rename(columns=column_mapping)

        # Timestamps
        now = datetime.datetime.now()
        df_db['created_at'] = now
        df_db['updated_at'] = now

        if 'external_id' in df_db.columns:
            df_db['external_id'] = df_db['external_id'].astype(str)

        # Replace NaN with None for SQL NULL insertion
        df_db = df_db.replace({np.nan: None})

        print(f"Prepared {len(df_db):,} records. Connecting to database...")
        conn_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        engine = create_engine(conn_string)

        with engine.connect() as conn:
            conn.execute(text(DDL_CREATE_TABLE))
            conn.commit()
            print("Table schema created successfully.")

        print(f"Inserting records into table 'car_master'...")
        df_db.to_sql('car_master', engine, if_exists='append', index=False, chunksize=1000)
        print(f"[SUCCESS] Import completed successfully! {len(df_db):,} rows inserted.")

    except Exception as e:
        print(f"[ERROR] Failed to import data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import car master Excel data into PostgreSQL.")
    parser.add_argument("--file", default=DEFAULT_EXCEL_PATH, help="Path to Excel dataset file")
    args = parser.parse_args()

    import_data(args.file)

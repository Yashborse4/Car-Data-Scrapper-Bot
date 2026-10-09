# 🚗 Car Data Scrapper Bot

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Database: PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![Framework: Spring Boot JPA Ready](https://img.shields.io/badge/Spring%20Boot-JPA%20Entity-brightgreen.svg)](https://spring.io/projects/spring-boot)

A high-performance, fault-tolerant automotive data scraping, optimization, and database ingestion pipeline. Extracts comprehensive car specifications, variants, lifecycle data, and technical attributes from Indian automotive catalog APIs (spanning years 2000–2025 across 31+ manufacturers), normalizes the datasets, and provides direct bulk ingestion into PostgreSQL with companion Spring Boot JPA entities.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Repository Structure](#-repository-structure)
- [Prerequisites & Installation](#-prerequisites--installation)
- [Usage Guide](#-usage-guide)
  - [1. Running the Scraper](#1-running-the-scraper)
  - [2. Optimizing & Aggregating the Dataset](#2-optimizing--aggregating-the-dataset)
  - [3. PostgreSQL Database Ingestion](#3-postgresql-database-ingestion)
- [Data Dictionary & Schema](#-data-dictionary--schema)
- [Spring Boot / JPA Integration](#-spring-boot--jpa-integration)
- [Testing & Diagnostics](#-testing--diagnostics)
- [License & Author](#-license--author)

---

## 🔍 Overview

Scraping vehicle catalog data across hundreds of models and thousands of variants over a 25-year timeline is vulnerable to network drops, rate limits, duplicate variant IDs, and API schema quirks. 

**Car Data Scrapper Bot** solves this with:
1. **Two-Phase Architecture**: Separates model discovery from variant specification fetching to maximize throughput and minimize redundant API calls.
2. **Resilience & Rate Limiting**: Token-bucket delay control, exponential backoff jitter via `tenacity`, and periodic checkpointing to guarantee recovery without re-fetching already extracted data.
3. **Data Aggregation Engine**: Reduces year-by-year redundant variant rows into clean, deduplicated variant specifications with calculated production year spans (`make_year_start`, `make_year_end`, `total_years_produced`).
4. **End-to-End Pipeline**: Includes complete SQL schemas, SQLAlchemy bulk ingestion scripts, and a ready-to-use Spring Boot JPA Entity (`CarMaster.java`).

---

## 🚀 Key Features

- **Multi-Brand & Multi-Year Extraction**: Automatically scrapes 31+ car manufacturers across model years 2000 through 2025.
- **Robust Rate Limiting & Backoff**: Built-in exponential backoff with random jitter prevents IP throttling or ban issues.
- **Checkpoint & Resume Capability**: Automatically tracks progress in `checkpoint.json`. If a network disruption or manual interrupt occurs, scraping resumes exactly where it stopped.
- **Incremental Excel Writer**: Flushes collected records to disk at regular intervals (every 2 minutes) to prevent memory bloat and eliminate data loss.
- **Dataset Optimizer**: Transforms raw year-slice data into consolidated variant master records, achieving a **~3.5x reduction** in dataset size while preserving full historical provenance.
- **PostgreSQL Ingestion & Spring Boot Support**: Includes automated DDL generation, indexed PostgreSQL table creation, and a production Java JPA entity class.

---

## 🏗 System Architecture

```
┌────────────────┐      Token-Bucket / Jitter      ┌──────────────────┐
│  Spinny APIs   │  ◄───────────────────────────►  │  SpinnyClient    │
└────────────────┘                                 └─────────┬────────┘
                                                             │
                                                   Phase 1: Model Discovery
                                                   Phase 2: Variant Fetching
                                                             │
                                                             ▼
                                                   ┌──────────────────┐
                                                   │  SpinnyScraper   │
                                                   │  (Checkpointer)  │
                                                   └─────────┬────────┘
                                                             │
                                               Incremental Flush (Excel)
                                                             │
                                                             ▼
                                                   ┌──────────────────┐
                                                   │    data/raw/     │
                                                   └─────────┬────────┘
                                                             │
                                                   Grouping & Aggregation
                                                             │
                                                             ▼
                                                   ┌──────────────────┐
                                                   │ data/processed/  │
                                                   └─────────┬────────┘
                                                             │
                                                Bulk Import (SQLAlchemy)
                                                             │
                                                             ▼
                                                   ┌──────────────────┐
                                                   │ PostgreSQL DB    │
                                                   │  (car_master)    │
                                                   └──────────────────┘
```

---

## 📁 Repository Structure

```
Car-Data-Scrapper-Bot/
├── src/                                  # Core scraper implementation
│   ├── __init__.py
│   ├── config.py                         # Scraper & API configuration settings
│   ├── spinny_client.py                  # API client with rate limiting & exponential retries
│   ├── spinny_scraper.py                 # 2-Phase scraper engine with incremental checkpointing
│   ├── scraper.py                        # Alternative / base scraper module
│   └── scrape_all_brands.py              # Multi-brand scraper runner
├── data/                                 # Extracted and normalized datasets
│   ├── raw/                              # Full raw scraped Excel dataset (100,000+ rows)
│   │   └── spinny_car_master_20260110_203905.xlsx
│   ├── processed/                        # Optimized master dataset (~28,080 rows)
│   │   └── optimized_spinny_master.xlsx
│   └── README.md                         # Detailed dataset documentation & dictionary
├── database/                             # Database integration & schemas
│   ├── schema.sql                        # PostgreSQL DDL script with performance indexes
│   ├── import_spinny_data.py             # Bulk ingestion script using SQLAlchemy & pandas
│   ├── CarMaster.java                    # Spring Boot JPA Entity for car_master table
│   ├── application.properties            # Spring Boot DataSource configuration template
│   └── columns.txt                       # Column reference listing
├── scripts/                              # Data processing & analysis utilities
│   ├── optimize_dataset.py               # Aggregates raw data into consolidated variant master
│   ├── analyze_splits.py                 # Analyzes column variance and grouping splits
│   ├── analyze_splits_v2.py              # Extended split analysis utility
│   ├── check_variant_id.py               # Validates variant ID uniqueness across years
│   ├── inspect_excel.py                  # Quick inspection tool for Excel headers and types
│   └── prove_hypothesis.py               # Statistical validation of dataset attributes
├── tests/                                # Test suite & diagnostic utilities
│   ├── test_api.py                       # Validates API connectivity and response payloads
│   ├── test_incremental_save.py         # Tests incremental Excel appending logic
│   ├── test_no_year.py                   # Tests API behavior when year parameter is omitted
│   ├── verify_refactor.py                # Unit tests for attribute normalization and state saving
│   └── debug/                            # Debugging scripts for specific brands and fields
│       ├── debug_bmw.py
│       ├── debug_brands.py
│       ├── debug_data.py
│       ├── debug_missing.py
│       └── debug_optimization.py
├── main.py                               # CLI entry point to launch the scraper
├── requirements.txt                      # Project dependencies
├── .gitignore                            # Standard git exclusions (logs, cache, venv)
├── LICENSE                               # MIT License
└── README.md                             # Comprehensive project documentation
```

---

## ⚙️ Prerequisites & Installation

### 1. Prerequisites
- **Python**: 3.10 or higher
- **PostgreSQL**: 13+ (optional, only for database ingestion)
- **Java**: 17+ & Spring Boot 3+ (optional, for Java backend service)

### 2. Installation

Clone the repository:
```bash
git clone https://github.com/Yashborse4/Car-Data-Scrapper-Bot.git
cd Car-Data-Scrapper-Bot
```

Create and activate a virtual environment:
```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 📖 Usage Guide

### 1. Running the Scraper
To start the scraping process:
```bash
python main.py
```
- By default, scraping runs with resume mode enabled (`resume=True`).
- Output files are saved incrementally to the `data/raw/` directory.
- Detailed execution logs are recorded in `logs/scraper.log`.
- To pause execution at any time, press `Ctrl + C`. Progress is saved to `checkpoint.json` and will automatically resume on next execution.

### 2. Optimizing & Aggregating the Dataset
The raw dataset contains separate entries for each manufactured year of a variant. To aggregate these into a clean specification master table:
```bash
python scripts/optimize_dataset.py \
    --input data/raw/spinny_car_master_20260110_203905.xlsx \
    --output data/processed/optimized_spinny_master.xlsx
```
**Outcome**:
- Calculates `make_year_start` and `make_year_end` for each variant.
- Calculates `total_years_produced`.
- Produces a deduplicated, clean master dataset ready for relational database loading.

### 3. PostgreSQL Database Ingestion
Configure your database connection using environment variables and run the ingestion script:

```bash
# Set environment variables (or rely on defaults)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=carselling
export DB_USERNAME=postgres
export DB_PASSWORD=your_password

# Ingest data
python database/import_spinny_data.py --file data/processed/optimized_spinny_master.xlsx
```

---

## 📊 Data Dictionary & Schema

The target PostgreSQL table `car_master` is created with the following schema:

```sql
CREATE TABLE car_master (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255),               -- Catalog variant ID
    make VARCHAR(50) NOT NULL,              -- Manufacturer (e.g. Maruti Suzuki)
    model VARCHAR(100) NOT NULL,            -- Model (e.g. Swift)
    variant VARCHAR(200),                   -- Trim (e.g. VXI)
    segment VARCHAR(50),                    -- Segment (entry, mid, premium)
    engine_cc INTEGER,                      -- Engine displacement (CC)
    fuel_type VARCHAR(50),                  -- Fuel type (petrol, diesel, cng, electric)
    transmission VARCHAR(50),               -- Transmission (manual, automatic)
    body_type VARCHAR(50),                  -- Body style (hatchback, sedan, suv)
    mileage_arai DOUBLE PRECISION,          -- ARAI rated mileage
    year_start INTEGER,                     -- First production year
    year_end INTEGER,                       -- Last production year
    power_hp VARCHAR(255),                  -- Power output
    torque_nm VARCHAR(255),                 -- Torque output
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_car_master_make ON car_master(make);
CREATE INDEX idx_car_master_model ON car_master(model);
CREATE INDEX idx_car_master_external_id ON car_master(external_id);
```

---

## ☕ Spring Boot / JPA Integration

A pre-built JPA Entity `CarMaster.java` is included in `database/CarMaster.java` for seamless integration into Java Spring Boot applications:

```java
@Table(name = "car_master", indexes = {
    @Index(name = "idx_car_master_make", columnList = "make"),
    @Index(name = "idx_car_master_model", columnList = "model")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
public class CarMaster {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "external_id")
    private String externalId;

    @Column(nullable = false, length = 50)
    private String make;

    @Column(nullable = false, length = 100)
    private String model;

    @Column(length = 200)
    private String variant;

    @Column(name = "engine_cc")
    private Integer engineCC;

    @Column(name = "fuel_type", length = 50)
    private String fuelType;
    
    // ... Additional fields in database/CarMaster.java
}
```

---

## 🧪 Testing & Diagnostics

Run unit and verification tests:
```bash
# Run refactoring verification
python -m unittest tests/verify_refactor.py

# Test incremental Excel export logic
python tests/test_incremental_save.py

# Test API connectivity and response structure
python tests/test_api.py
```

---

## 📄 License & Author

Developed by **[Yash Borse](https://github.com/Yashborse4)**.  
Released under the [MIT License](LICENSE).

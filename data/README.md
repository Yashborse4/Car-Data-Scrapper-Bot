# Car Specification Master Dataset

This folder contains the automotive dataset scraped and processed by the **Car Data Scrapper Bot**.

---

## 📁 Directory Structure

```
data/
├── raw/
│   └── spinny_car_master_20260110_203905.xlsx    # Full raw year-by-year scraped records (100,000+ rows)
└── processed/
    └── optimized_spinny_master.xlsx              # Consolidated variant specifications (~28,080 rows)
```

---

## 📊 Dataset Overview

| Attribute | Raw Dataset | Optimized Dataset |
| :--- | :--- | :--- |
| **Filename** | `spinny_car_master_20260110_203905.xlsx` | `optimized_spinny_master.xlsx` |
| **Granularity** | Per Make-Year & Variant | Consolidated per Unique Variant Specification |
| **Approx. Rows** | 100,000+ rows | ~28,080 unique variants |
| **Years Covered**| 2000 – 2025 | 2000 – 2025 |
| **Brands Covered**| 31+ major manufacturers | 31+ major manufacturers |

---

## 📋 Data Dictionary (`car_master`)

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `variant_id` / `external_id` | String | External identifier from source catalog | `1628`, `4821` |
| `brand_name` / `make` | String | Vehicle manufacturer / brand | `Maruti Suzuki`, `Hyundai` |
| `model_name` / `model` | String | Model family name | `Swift`, `Creta`, `City` |
| `variant_name` / `variant` | String | Trim and variant designation | `VXI (O)`, `SX Turbo` |
| `segment` | String | Market vehicle classification | `entry`, `mid`, `premium`, `luxury` |
| `engine_cc` | Integer | Engine displacement in cubic centimeters (CC) | `1197`, `1498` |
| `fuel_type` | String | Powertrain fuel type | `petrol`, `diesel`, `cng`, `electric` |
| `transmission` | String | Transmission gearbox type | `manual`, `automatic` |
| `body_type` | String | Vehicle body style | `hatchback`, `sedan`, `suv` |
| `mileage_arai` | Float | ARAI certified fuel economy (kmpl or km/kg) | `22.56`, `18.2` |
| `power_hp` | String | Maximum power output | `88.5 bhp @ 6000 rpm` |
| `torque_nm` | String | Maximum torque output | `113 Nm @ 4400 rpm` |
| `launch_year` | Integer | Initial launch year according to catalog | `2018` |
| `discontinued_year` | Integer | Discontinuation year (null if in production) | `2023` |
| `make_year_start` | Integer | Earliest manufactured model year observed | `2018` |
| `make_year_end` | Integer | Latest manufactured model year observed | `2024` |
| `total_years_produced`| Integer | Total distinct production years recorded | `7` |

---

## 🔄 Ingestion & Database Loading

To load `data/processed/optimized_spinny_master.xlsx` into PostgreSQL:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=carselling
export DB_USERNAME=postgres
export DB_PASSWORD=your_password

python database/import_spinny_data.py
```

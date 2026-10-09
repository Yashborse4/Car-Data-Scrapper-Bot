-- =============================================================================
-- Spinny Car Master Database Schema
-- Database: PostgreSQL
-- Description: Table definition and indexes for normalized automotive specifications
-- =============================================================================

DROP TABLE IF EXISTS car_master CASCADE;

CREATE TABLE car_master (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255),               -- Spinny variant ID (external reference)
    make VARCHAR(50) NOT NULL,              -- Car manufacturer / brand (e.g., Maruti Suzuki, Hyundai)
    model VARCHAR(100) NOT NULL,            -- Vehicle model name (e.g., Swift, City, Creta)
    variant VARCHAR(200),                   -- Trim / Variant name (e.g., VXI, SX Optional)
    segment VARCHAR(50),                    -- Market segment (e.g., entry, mid, premium, luxury)
    engine_cc INTEGER,                      -- Engine displacement in CC
    fuel_type VARCHAR(50),                  -- Fuel type (e.g., petrol, diesel, cng, electric)
    transmission VARCHAR(50),               -- Transmission type (e.g., manual, automatic)
    body_type VARCHAR(50),                  -- Vehicle body shape (e.g., hatchback, sedan, suv)
    mileage_arai DOUBLE PRECISION,          -- ARAI certified fuel efficiency (kmpl or km/kg)
    year_start INTEGER,                     -- First production year for this variant
    year_end INTEGER,                       -- Last production year for this variant
    power_hp VARCHAR(255),                  -- Engine power output (hp / bhp / kW)
    torque_nm VARCHAR(255),                 -- Engine torque output in Nm
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_car_master_make ON car_master(make);
CREATE INDEX idx_car_master_model ON car_master(model);
CREATE INDEX idx_car_master_external_id ON car_master(external_id);
CREATE INDEX idx_car_master_fuel_transmission ON car_master(fuel_type, transmission);
CREATE INDEX idx_car_master_year_range ON car_master(year_start, year_end);

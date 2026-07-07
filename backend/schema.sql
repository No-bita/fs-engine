-- Database Schema for MSME Platform conforming to Pydantic v2 SchemeDocument

DROP TABLE IF EXISTS workflow CASCADE;
DROP TABLE IF EXISTS "references" CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS eligibility_rules CASCADE;
DROP TABLE IF EXISTS benefits CASCADE;
DROP TABLE IF EXISTS schemes CASCADE;

CREATE TABLE schemes (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    scheme_type VARCHAR(100),
    provider_category VARCHAR(100),
    provider_name VARCHAR(255),
    provider_government_level VARCHAR(50),
    geography_coverage VARCHAR(50),
    geography_states VARCHAR(100)[],
    geography_districts VARCHAR(100)[],
    business_stages VARCHAR(100)[],
    sectors VARCHAR(100)[],
    benefit_categories VARCHAR(100)[],
    msme_segments VARCHAR(100)[],
    business_intents VARCHAR(100)[],
    status VARCHAR(50),
    priority VARCHAR(50),
    created_at VARCHAR(50),
    updated_at VARCHAR(50),
    verified_at VARCHAR(50),
    source_confidence VARCHAR(50),
    compiled_by VARCHAR(100),
    reviewed_by VARCHAR(100),
    quality_score INT,
    notes TEXT
);

CREATE TABLE benefits (
    id VARCHAR(100) PRIMARY KEY,
    scheme_id VARCHAR(100) REFERENCES schemes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    summary TEXT,
    calculation_logic TEXT,
    max_amount NUMERIC,
    min_amount NUMERIC,
    loan_range VARCHAR(255),
    interest_rate VARCHAR(255),
    collateral_required BOOLEAN DEFAULT FALSE,
    collateral_details TEXT,
    guarantee_coverage VARCHAR(255),
    tenure_months INT,
    moratorium_months INT,
    margin_contribution TEXT
);

CREATE TABLE eligibility_rules (
    id VARCHAR(100) PRIMARY KEY,
    scheme_id VARCHAR(100) REFERENCES schemes(id) ON DELETE CASCADE,
    parameter VARCHAR(100) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    value JSONB NOT NULL
);

CREATE TABLE documents (
    id VARCHAR(100) PRIMARY KEY,
    scheme_id VARCHAR(100) REFERENCES schemes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT TRUE,
    issuing_authority VARCHAR(255),
    digitized_verification_available BOOLEAN DEFAULT FALSE
);

CREATE TABLE workflow (
    id VARCHAR(100) PRIMARY KEY,
    scheme_id VARCHAR(100) REFERENCES schemes(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    actor VARCHAR(100),
    channel VARCHAR(100),
    url VARCHAR(512),
    estimated_duration_days INT
);

CREATE TABLE "references" (
    id VARCHAR(100) PRIMARY KEY,
    scheme_id VARCHAR(100) REFERENCES schemes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(512) NOT NULL,
    type VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en'
);

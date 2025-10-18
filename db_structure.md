# Medicare Stars Database Schema

## Overview

This database schema supports the Medicare Advantage and Part D Stars Rating system, storing contract information, measure definitions, performance data, and star ratings.

---

## Tables

### 1. contracts

**Description**: Stores information about Medicare Advantage and Part D contracts

```sql
CREATE TABLE contracts (
    contract_id VARCHAR(10) PRIMARY KEY,
    organization_type VARCHAR(100) NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    organization_marketing_name VARCHAR(255),
    parent_organization VARCHAR(255),
    is_snp BOOLEAN DEFAULT FALSE,
    disaster_pct_2023 DECIMAL(5,2),
    disaster_pct_2024 DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_parent_org (parent_organization),
    INDEX idx_org_type (organization_type),
    INDEX idx_snp (is_snp)
);
```

**Columns**:
- `contract_id`: Unique identifier (e.g., H0028, E3014, S1234)
- `organization_type`: Type of plan (Local CCP, Regional CCP, PDP, Employer/Union Only, PFFS, MSA)
- `contract_name`: Legal entity name
- `organization_marketing_name`: Consumer-facing brand name
- `parent_organization`: Parent company controlling the contract
- `is_snp`: Boolean flag for Special Needs Plans
- `disaster_pct_2023`: Percentage of enrollees affected by disasters in 2023
- `disaster_pct_2024`: Percentage of enrollees affected by disasters in 2024

**Sample Data**:
```
H0028, 'Local CCP', 'CHA HMO, INC.', 'Humana', 'Humana Inc.', TRUE, 1, 9
H1290, 'Local CCP', 'DEVOTED HEALTH PLAN OF FLORIDA, INC.', 'Devoted Health', 'Devoted Health, Inc.', TRUE, 17, 81
```

---

### 2. measures

**Description**: Reference table defining all Star Rating measures

```sql
CREATE TABLE measures (
    measure_code VARCHAR(10) PRIMARY KEY,
    measure_name VARCHAR(255) NOT NULL,
    measure_domain VARCHAR(10) NOT NULL,
    domain_name VARCHAR(100),
    part_type ENUM('C', 'D') NOT NULL,
    measurement_period VARCHAR(100),
    higher_is_better BOOLEAN DEFAULT TRUE,
    measure_description TEXT,
    data_source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_part_type (part_type),
    INDEX idx_domain (measure_domain)
);
```

**Columns**:
- `measure_code`: Unique measure identifier (C01-C33 for Part C, D01-D12 for Part D)
- `measure_name`: Full name of the measure
- `measure_domain`: Domain code (HD1-HD5 for Part C, DD1-DD4 for Part D)
- `domain_name`: Full domain name
- `part_type`: 'C' for Part C (Medicare Advantage), 'D' for Part D (Prescription Drug)
- `measurement_period`: Date range when data is collected (e.g., "01/01/2024 – 12/31/2024")
- `higher_is_better`: TRUE for most measures, FALSE for inverse measures (e.g., readmissions, complaints)
- `measure_description`: Detailed description of what the measure evaluates
- `data_source`: Source of data (Claims, CAHPS, HOS, Pharmacy, etc.)

**Sample Data**:
```
'C01', 'Breast Cancer Screening', 'HD1', 'Staying Healthy: Screenings, Tests and Vaccines', 'C', '01/01/2024 – 12/31/2024', TRUE, 'Percentage of women 50-74 who had mammogram', 'Claims'
'C18', 'Plan All-Cause Readmissions', 'HD2', 'Managing Chronic (Long Term) Conditions', 'C', '01/01/2024 – 12/31/2024', FALSE, 'Hospital readmission rate', 'Claims'
'D08', 'Medication Adherence for Diabetes Medications', 'DD4', 'Drug Safety and Accuracy of Drug Pricing', 'D', '01/01/2024 – 12/31/2024', TRUE, 'PDC for diabetes medications', 'Pharmacy'
```

---

### 3. cut_points

**Description**: Defines star rating thresholds for each measure

```sql
CREATE TABLE cut_points (
    cut_point_id INT AUTO_INCREMENT PRIMARY KEY,
    measure_code VARCHAR(10) NOT NULL,
    org_type_category VARCHAR(50) NOT NULL,
    star_rating INT NOT NULL,
    threshold_min DECIMAL(10,4),
    threshold_max DECIMAL(10,4),
    threshold_operator VARCHAR(20),
    rating_year INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (measure_code) REFERENCES measures(measure_code),
    UNIQUE KEY unique_cut_point (measure_code, org_type_category, star_rating, rating_year),
    INDEX idx_measure_year (measure_code, rating_year),
    
    CONSTRAINT chk_star_rating CHECK (star_rating BETWEEN 1 AND 5)
);
```

**Columns**:
- `cut_point_id`: Auto-incrementing primary key
- `measure_code`: Links to measures table
- `org_type_category`: Differentiates thresholds ('Part C', 'MA-PD', 'PDP')
- `star_rating`: Star level (1 through 5)
- `threshold_min`: Minimum value for this star rating (inclusive)
- `threshold_max`: Maximum value for this star rating (exclusive, except for 5-star)
- `threshold_operator`: Describes comparison logic (e.g., '>=X to <Y', '>=X', '<X')
- `rating_year`: Year these cut points apply to (e.g., 2026)

**Sample Data**:
```
'C01', 'Part C', 1, NULL, 58.0000, '< 58%', 2026
'C01', 'Part C', 2, 58.0000, 71.0000, '>= 58% to < 71%', 2026
'C01', 'Part C', 3, 71.0000, 76.0000, '>= 71% to < 76%', 2026
'C01', 'Part C', 4, 76.0000, 84.0000, '>= 76% to < 84%', 2026
'C01', 'Part C', 5, 84.0000, NULL, '>= 84%', 2026
```

**Note**: For Part D measures, separate rows exist for MA-PD and PDP with different thresholds.

---

### 4. measure_performance

**Description**: Stores actual performance data and assigned stars for each contract-measure combination

```sql
CREATE TABLE measure_performance (
    performance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(10) NOT NULL,
    measure_code VARCHAR(10) NOT NULL,
    rating_year INT NOT NULL,
    raw_value DECIMAL(10,4),
    raw_value_display VARCHAR(50),
    star_rating INT,
    data_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
    FOREIGN KEY (measure_code) REFERENCES measures(measure_code),
    UNIQUE KEY unique_performance (contract_id, measure_code, rating_year),
    INDEX idx_contract_year (contract_id, rating_year),
    INDEX idx_measure_year (measure_code, rating_year),
    INDEX idx_star_rating (star_rating),
    
    CONSTRAINT chk_star_rating_valid CHECK (star_rating IS NULL OR star_rating BETWEEN 1 AND 5)
);
```

**Columns**:
- `performance_id`: Auto-incrementing primary key
- `contract_id`: Links to contracts table
- `measure_code`: Links to measures table
- `rating_year`: Year of the star rating (e.g., 2026)
- `raw_value`: Numeric performance value (percentage as decimal: 76% = 76.0000)
- `raw_value_display`: Original display format from source (e.g., "76%", "68", "0.16")
- `star_rating`: Assigned star rating (1-5) based on cut points
- `data_status`: Data availability status

**Data Status Values**:
- `'Valid'`: Normal performance data with star rating
- `'Plan not required to report measure'`: Exemption by plan type
- `'Plan too small to be measured'`: Enrollment < 11 or insufficient sample
- `'Not enough data available'`: Sample size requirements not met
- `'Plan too new to be measured'`: Contract in first 3 years
- `'No data available'`: Missing data
- `'Medicare shows only a Star Rating for this topic'`: Raw value suppressed

**Sample Data**:
```
'H0028', 'C01', 2026, 76.0000, '76%', 4, 'Valid'
'H0028', 'C02', 2026, 75.0000, '75%', 4, 'Valid'
'H0029', 'C01', 2026, NULL, 'Plan too small to be measured', NULL, 'Plan too small to be measured'
'H1290', 'C11', 2026, 94.0000, '94%', 5, 'Valid'
```

---

### 5. summary_ratings

**Description**: Aggregated summary star ratings for each contract

```sql
CREATE TABLE summary_ratings (
    summary_id INT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(10) NOT NULL,
    rating_year INT NOT NULL,
    part_c_summary DECIMAL(2,1),
    part_d_summary DECIMAL(2,1),
    overall_rating DECIMAL(2,1),
    part_c_status VARCHAR(100),
    part_d_status VARCHAR(100),
    overall_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
    UNIQUE KEY unique_summary (contract_id, rating_year),
    INDEX idx_overall_rating (overall_rating),
    INDEX idx_year (rating_year),
    
    CONSTRAINT chk_part_c_rating CHECK (part_c_summary IS NULL OR (part_c_summary >= 1.0 AND part_c_summary <= 5.0)),
    CONSTRAINT chk_part_d_rating CHECK (part_d_summary IS NULL OR (part_d_summary >= 1.0 AND part_d_summary <= 5.0)),
    CONSTRAINT chk_overall_rating CHECK (overall_rating IS NULL OR (overall_rating >= 1.0 AND overall_rating <= 5.0))
);
```

**Columns**:
- `summary_id`: Auto-incrementing primary key
- `contract_id`: Links to contracts table
- `rating_year`: Year of the star rating
- `part_c_summary`: Overall Part C (Medicare Advantage) summary rating (1.0 to 5.0 in 0.5 increments)
- `part_d_summary`: Overall Part D (Prescription Drug) summary rating
- `overall_rating`: Combined overall star rating
- `part_c_status`: Status for Part C rating (if not numeric)
- `part_d_status`: Status for Part D rating (if not numeric)
- `overall_status`: Status for overall rating (if not numeric)

**Status Values**:
- `'Not Applicable'`: Plan type doesn't have this component (e.g., PDP has no Part C)
- `'Not enough data available'`: Insufficient data to calculate
- `'Plan too new to be measured'`: Contract exempt (first 3 years)
- `'Plan too small to be measured'`: Enrollment too low

**Sample Data**:
```
'H0028', 2026, 3.5, 3.0, 3.5, 'Valid', 'Valid', 'Valid'
'H1290', 2026, 5.0, 4.0, 5.0, 'Valid', 'Valid', 'Valid'
'S1234', 2026, NULL, 4.5, NULL, 'Not Applicable', 'Valid', 'Not Applicable'
'E3014', 2026, NULL, 4.5, NULL, 'Not Applicable', 'Valid', 'Not Applicable'
```

---

## Relationships

### Entity Relationship Diagram

```
contracts (1) ----< (*) measure_performance
contracts (1) ----< (*) summary_ratings
measures (1) ----< (*) measure_performance
measures (1) ----< (*) cut_points
```

### Key Relationships

1. **One contract has many measure performances** (one row per measure per year)
2. **One contract has many summary ratings** (one row per year)
3. **One measure has many performances** (one row per contract)
4. **One measure has many cut points** (multiple star thresholds)

---

## Indexes

### Performance Optimization

**Primary Access Patterns**:

1. **Contract-centric queries**: Retrieve all measures for a specific contract
   - Index: `idx_contract_year` on `measure_performance(contract_id, rating_year)`

2. **Measure-centric queries**: Compare all contracts on a specific measure
   - Index: `idx_measure_year` on `measure_performance(measure_code, rating_year)`

3. **High-performer queries**: Find all 4+ or 5-star contracts
   - Index: `idx_overall_rating` on `summary_ratings(overall_rating)`
   - Index: `idx_star_rating` on `measure_performance(star_rating)`

4. **Parent organization queries**: Aggregate performance by parent company
   - Index: `idx_parent_org` on `contracts(parent_organization)`

5. **SNP analysis**: Filter/compare Special Needs Plans
   - Index: `idx_snp` on `contracts(is_snp)`

---

## Views

### Useful Analytical Views

#### view_contract_summary

```sql
CREATE VIEW view_contract_summary AS
SELECT 
    c.contract_id,
    c.organization_type,
    c.organization_marketing_name,
    c.parent_organization,
    c.is_snp,
    sr.part_c_summary,
    sr.part_d_summary,
    sr.overall_rating,
    sr.rating_year
FROM contracts c
LEFT JOIN summary_ratings sr ON c.contract_id = sr.contract_id
WHERE sr.rating_year = (SELECT MAX(rating_year) FROM summary_ratings);
```

#### view_measure_benchmarks

```sql
CREATE VIEW view_measure_benchmarks AS
SELECT 
    mp.measure_code,
    m.measure_name,
    m.part_type,
    mp.rating_year,
    COUNT(*) as contract_count,
    AVG(mp.raw_value) as avg_performance,
    MIN(mp.raw_value) as min_performance,
    MAX(mp.raw_value) as max_performance,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mp.raw_value) as p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY mp.raw_value) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY mp.raw_value) as p75,
    AVG(CASE WHEN mp.star_rating IS NOT NULL THEN mp.star_rating END) as avg_star_rating
FROM measure_performance mp
JOIN measures m ON mp.measure_code = m.measure_code
WHERE mp.data_status = 'Valid'
GROUP BY mp.measure_code, m.measure_name, m.part_type, mp.rating_year;
```

#### view_parent_org_performance

```sql
CREATE VIEW view_parent_org_performance AS
SELECT 
    c.parent_organization,
    sr.rating_year,
    COUNT(DISTINCT c.contract_id) as contract_count,
    AVG(sr.overall_rating) as avg_overall_rating,
    AVG(sr.part_c_summary) as avg_part_c_rating,
    AVG(sr.part_d_summary) as avg_part_d_rating,
    SUM(CASE WHEN sr.overall_rating >= 4.0 THEN 1 ELSE 0 END) as contracts_4plus_stars,
    SUM(CASE WHEN sr.overall_rating = 5.0 THEN 1 ELSE 0 END) as contracts_5_stars
FROM contracts c
JOIN summary_ratings sr ON c.contract_id = sr.contract_id
WHERE sr.overall_rating IS NOT NULL
GROUP BY c.parent_organization, sr.rating_year;
```

---

## Sample Queries

### Query 1: Find improvement opportunities (measures close to next star threshold)

```sql
SELECT 
    c.contract_id,
    c.organization_marketing_name,
    mp.measure_code,
    m.measure_name,
    mp.raw_value as current_performance,
    mp.star_rating as current_stars,
    cp_next.threshold_min as next_star_threshold,
    ROUND(cp_next.threshold_min - mp.raw_value, 2) as performance_gap,
    CONCAT('+', ROUND(((cp_next.threshold_min - mp.raw_value) / mp.raw_value * 100), 1), '%') as pct_improvement_needed
FROM measure_performance mp
JOIN contracts c ON mp.contract_id = c.contract_id
JOIN measures m ON mp.measure_code = m.measure_code
JOIN cut_points cp_current ON (
    mp.measure_code = cp_current.measure_code 
    AND cp_current.star_rating = mp.star_rating
    AND cp_current.rating_year = mp.rating_year
)
JOIN cut_points cp_next ON (
    mp.measure_code = cp_next.measure_code 
    AND cp_next.star_rating = mp.star_rating + 1
    AND cp_next.rating_year = mp.rating_year
)
WHERE mp.rating_year = 2026
  AND mp.star_rating < 5
  AND mp.data_status = 'Valid'
  AND c.contract_id = 'H0028' -- Example: specific contract
ORDER BY performance_gap ASC
LIMIT 10;
```

### Query 2: Compare contract to market benchmarks

```sql
SELECT 
    mp.measure_code,
    m.measure_name,
    mp.raw_value as my_performance,
    mp.star_rating as my_stars,
    bm.avg_performance as market_avg,
    bm.median as market_median,
    ROUND(mp.raw_value - bm.median, 2) as vs_median,
    CASE 
        WHEN mp.raw_value > bm.p75 THEN 'Top Quartile'
        WHEN mp.raw_value > bm.median THEN 'Above Median'
        WHEN mp.raw_value > bm.p25 THEN 'Below Median'
        ELSE 'Bottom Quartile'
    END as quartile_rank
FROM measure_performance mp
JOIN measures m ON mp.measure_code = m.measure_code
JOIN view_measure_benchmarks bm ON (
    mp.measure_code = bm.measure_code 
    AND mp.rating_year = bm.rating_year
)
WHERE mp.contract_id = 'H0028'
  AND mp.rating_year = 2026
  AND mp.data_status = 'Valid'
ORDER BY vs_median DESC;
```

### Query 3: Track star rating distribution across industry

```sql
SELECT 
    sr.overall_rating,
    COUNT(*) as contract_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    GROUP_CONCAT(DISTINCT c.parent_organization ORDER BY c.parent_organization SEPARATOR ', ') as example_orgs
FROM summary_ratings sr
JOIN contracts c ON sr.contract_id = c.contract_id
WHERE sr.rating_year = 2026
  AND sr.overall_rating IS NOT NULL
GROUP BY sr.overall_rating
ORDER BY sr.overall_rating DESC;
```

### Query 4: Identify consistently high-performing parent organizations

```sql
SELECT 
    c.parent_organization,
    COUNT(DISTINCT c.contract_id) as total_contracts,
    AVG(sr.overall_rating) as avg_rating,
    MIN(sr.overall_rating) as lowest_rating,
    MAX(sr.overall_rating) as highest_rating,
    SUM(CASE WHEN sr.overall_rating >= 4.0 THEN 1 ELSE 0 END) as high_performer_count,
    ROUND(SUM(CASE WHEN sr.overall_rating >= 4.0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_high_performers
FROM contracts c
JOIN summary_ratings sr ON c.contract_id = sr.contract_id
WHERE sr.rating_year = 2026
  AND sr.overall_rating IS NOT NULL
GROUP BY c.parent_organization
HAVING COUNT(DISTINCT c.contract_id) >= 3
ORDER BY avg_rating DESC, pct_high_performers DESC
LIMIT 20;
```

### Query 5: Analyze SNP vs non-SNP performance

```sql
SELECT 
    c.is_snp,
    CASE WHEN c.is_snp THEN 'Special Needs Plan' ELSE 'General Plan' END as plan_category,
    COUNT(DISTINCT c.contract_id) as contract_count,
    AVG(sr.overall_rating) as avg_overall_rating,
    AVG(sr.part_c_summary) as avg_part_c,
    AVG(sr.part_d_summary) as avg_part_d,
    SUM(CASE WHEN sr.overall_rating >= 4.0 THEN 1 ELSE 0 END) as count_4plus_stars
FROM contracts c
JOIN summary_ratings sr ON c.contract_id = sr.contract_id
WHERE sr.rating_year = 2026
  AND sr.overall_rating IS NOT NULL
  AND c.organization_type = 'Local CCP'
GROUP BY c.is_snp
ORDER BY c.is_snp DESC;
```

---

## Data Loading Strategy

### ETL Pipeline

**Step 1: Load Reference Data**
1. Load `measures` table from Part C and Part D Cut Points headers
2. Load `cut_points` table from Cut Points threshold rows

**Step 2: Load Contract Data**
1. Parse Measure Data CSV
2. Extract unique contracts → `contracts` table
3. Extract all measure performances → `measure_performance` table (raw values)

**Step 3: Enrich with Star Ratings**
1. Parse Measure Stars CSV
2. Update `measure_performance` table with star ratings
3. Validate: star ratings match cut point logic

**Step 4: Load Summary Ratings**
1. Parse Summary Ratings CSV
2. Insert into `summary_ratings` table

**Step 5: Validation**
1. Run integrity checks
2. Verify all foreign keys resolve
3. Check for orphaned records
4. Flag anomalies for review

### Data Refresh Frequency

- **Annual**: Full reload when new Star Ratings published (typically October)
- **As Needed**: Corrections or restatements from CMS
- **Historical**: Maintain prior years for trending (append, don't overwrite)

---

## Constraints & Business Rules

### Data Integrity Rules

1. **Contract ID Format**: 
   - H-contracts: Health plans (MA/MA-PD)
   - E-contracts: Employer/Union
   - R-contracts: Regional PPOs
   - S-contracts: Standalone PDPs

2. **Star Rating Range**: 1.0 to 5.0 in 0.5 increments
   - Valid values: 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0

3. **Part C vs Part D Measures**:
   - Part C: C01-C33 (33 measures)
   - Part D: D01-D12 (12 measures)

4. **Organization Type Constraints**:
   - PDP contracts: Part D measures only (no Part C)
   - MA-only contracts: Part C measures only (no Part D)
   - MA-PD contracts: Both Part C and Part D measures

5. **SNP Indicator**:
   - If `is_snp = TRUE`, must have C07 (SNP Care Management) data
   - If `is_snp = FALSE`, C07 should be "Plan not required to report"

---

## Performance Considerations

### Indexing Strategy

**High-cardinality columns** (good for indexing):
- `contract_id` (770+ unique values)
- `measure_code` (45 unique values)
- `parent_organization` (100+ unique values)

**Low-cardinality columns** (less useful for indexing):
- `star_rating` (5 unique values) - still indexed for common queries
- `is_snp` (2 unique values) - indexed because it's frequently filtered

### Query Optimization Tips

1. **Always filter by `rating_year`**: Reduces result set significantly
2. **Use covering indexes**: Include commonly selected columns in index
3. **Avoid SELECT ***: Specify only needed columns
4. **Leverage views**: Pre-aggregated views for common analytics
5. **Partition by year**: For very large historical datasets

### Estimated Table Sizes

- `contracts`: ~800 rows
- `measures`: 45 rows
- `cut_points`: ~250 rows (45 measures × 5 star levels)
- `measure_performance`: ~35,000 rows per year (800 contracts × ~45 measures)
- `summary_ratings`: ~800 rows per year

**Multi-year storage**: Multiply by number of years retained (recommend 5 years = ~175K total measure_performance rows)

---

## Maintenance

### Regular Tasks

**Monthly**:
- Monitor data quality flags
- Review null/missing data patterns

**Quarterly**:
- Archive old data if retention policy exists
- Optimize indexes based on query patterns

**Annually** (October/November):
- Load new Star Ratings data
- Run full validation suite
- Update cut_points for new year
- Generate year-over-year comparison reports

---

## Version History

- **v1.0** (October 17, 2025): Initial schema design for 2026 Star Ratings data


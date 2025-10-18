# Medicare Stars Data - Format Specification & Parsing Rules

**Last Updated**: October 17, 2025  
**Purpose**: Comprehensive guide for parsing and handling all edge cases in Medicare Stars data

---

## Executive Summary

Based on forensic analysis of 768 contracts and 45 measures (~35,000 data points), this document provides the complete specification for parsing Medicare Stars rating data.

### Key Challenges Identified
1. **3 different numeric formats**: Percentage, Integer, Decimal
2. **8 types of special status values**: "Plan too small", "Not enough data", etc.
3. **3 inverse measures**: Lower = better (readmissions, complaints)
4. **2 cut point sets for Part D**: MA-PD vs PDP have different thresholds
5. **7 threshold string patterns**: Need regex parsing for cut point bands

---

## Measure Formats

### Format Distribution

| Format | Count | Measures |
|--------|-------|----------|
| **PERCENTAGE** | 32 | Most Part C + adherence measures |
| **INTEGER** | 9 | CAHPS survey measures (C22-C27, D05-D06, D07) |
| **DECIMAL** | 2 | Complaints measures (C28, D02) |
| **NO_NUMERIC** | 2 | Quality Improvement composites (C30, D04) |

**TOTAL**: 45 measures

---

## Format 1: PERCENTAGE (32 measures)

### Characteristics
- **Pattern**: `"76%"`, `"82%"`, `"91%"`
- **Range**: 0% to 100%
- **Used for**: Clinical measures, screenings, adherence

### Parsing Rules
```python
def parse_percentage(value):
    """
    Input: "76%" or "82%"
    Output: 76.0 or 82.0 (as float)
    """
    if '%' in str(value):
        return float(str(value).replace('%', '').strip())
    return None
```

### Examples

| Measure | Sample Values | Range |
|---------|---------------|-------|
| C01: Breast Cancer Screening | 76%, 61%, 84% | 13% to 94% |
| C02: Colorectal Screening | 75%, 51%, 69% | 9% to 93% |
| C14: Blood Pressure Control | 82%, 86%, 78% | 39% to 98% |
| D08: Diabetes Adherence | 86%, 85%, 88% | 76% to 97% |
| D09: Hypertension Adherence | 90%, 83%, 89% | 66% to 97% |

### Edge Cases
- **Whole numbers**: `100%` common for C31, C32, C33, D01
- **Low values**: Some plans report < 20% on screening measures (data quality issue?)
- **Special case**: C30 and D04 (Quality Improvement) have NO raw percentages, only special status

---

## Format 2: INTEGER (9 measures)

### Characteristics
- **Pattern**: `"87"`, `"91"`, `"84"` (no decimal, no %)
- **Range**: Typically 75-95 (CAHPS scores), 80-100 (pricing)
- **Used for**: Survey-based ratings, pricing accuracy

### Parsing Rules
```python
def parse_integer(value):
    """
    Input: "87" or "91"
    Output: 87 or 91 (as int)
    """
    clean = str(value).strip()
    if clean.isdigit():
        return int(clean)
    return None
```

### Examples

| Measure | Sample Values | Range | Notes |
|---------|---------------|-------|-------|
| C22: Getting Needed Care | 81, 82, 87 | 69 to 94 | CAHPS composite score |
| C23: Getting Appointments | 82, 84, 91 | 72 to 95 | CAHPS composite score |
| C24: Customer Service | 88, 89, 91 | 76 to 96 | CAHPS composite score |
| C25: Rating Health Care Quality | 84, 86, 89 | 76 to 95 | CAHPS rating |
| C26: Rating Health Plan | 84, 85, 91 | 75 to 95 | CAHPS rating |
| C27: Care Coordination | 85, 86, 88 | 75 to 94 | CAHPS composite |
| D05: Rating of Drug Plan | 87, 86, 85 | 76 to 95 | CAHPS rating |
| D06: Getting Prescriptions | 89, 91, 88 | 83 to 96 | CAHPS composite |
| D07: MPF Price Accuracy | 84, 91, 99 | 82 to 100 | Pricing accuracy |

### Edge Cases
- **D07 (Pricing)**: Often 99 or 100 (very high performers)
- **CAHPS scores**: Rarely below 75 or above 95 (scale compression)

---

## Format 3: DECIMAL (2 measures)

### Characteristics
- **Pattern**: `"0.16"`, `"0.32"`, `"1.34"`
- **Range**: Typically -0.5 to 3.0
- **Used for**: Complaint rates and quality improvement scores

### Parsing Rules
```python
def parse_decimal(value):
    """
    Input: "0.16" or "1.34"
    Output: 0.16 or 1.34 (as float)
    """
    try:
        return float(str(value).strip())
    except:
        return None
```

### Examples

| Measure | Sample Values | Range | Notes |
|---------|---------------|-------|-------|
| C28: Complaints about Health Plan | 0.16, 0.12, 0.39 | 0.0 to 3.15 | **INVERSE**: Lower = better |
| D02: Complaints about Drug Plan | 0.16, 0.12, 0.39 | 0.0 to 3.15 | **INVERSE**: Lower = better |

### Edge Cases
- **Negative values**: C28 can have negative values (e.g., "-0.121368") indicating improvement
- **Very small values**: 5-star threshold is often ≤ 0.11
- **Inverse logic**: Lower complaint rates = higher stars

---

## Format 4: NO_NUMERIC (2 measures)

### Characteristics
- **Pattern**: No raw values, only star ratings
- **Special status**: `"Medicare shows only a Star Rating for this topic"`
- **Used for**: Composite quality improvement scores

### Handling
```python
def parse_no_numeric(value):
    """
    These measures don't have raw performance values
    Only star ratings are available in the Stars file
    """
    return None  # No raw value to parse
```

### Examples

| Measure | Prevalence | Notes |
|---------|------------|-------|
| C30: Health Plan Quality Improvement | 100% special status | Calculated by CMS, not reported |
| D04: Drug Plan Quality Improvement | 100% special status | Calculated by CMS, not reported |

### Edge Cases
- **No gaps to calculate**: Can't determine "how far to next star" without raw value
- **Stars only**: Must read from Measure Stars file, not Measure Data file

---

## Special Status Values

### All Special Values Found

| Special Value | Meaning | Prevalence | Action |
|---------------|---------|------------|--------|
| **"Plan too small to be measured"** | < 11 enrollees or insufficient sample | 7-18% per measure | Exclude from calculations |
| **"Plan too new to be measured"** | Contract in first 3 years (hold harmless) | 10-26% per measure | Exclude from calculations |
| **"Not enough data available"** | Sample size below threshold | 1-25% per measure | Exclude from calculations |
| **"Plan not required to report measure"** | Type exemption (e.g., PDPs don't report C measures) | 1-40% per measure | Expected, no penalty |
| **"No data available"** | Missing submission | 0-5% per measure | Investigate data quality issue |
| **"Medicare shows only a Star Rating for this topic"** | Raw value suppressed for privacy | 75% for C30/D04 | Use star rating only |
| **"CMS identified issues with this plan's data"** | Data quality flag | 3% for C07 | Investigate, may affect rating |
| **"Benefit not offered by plan"** | Plan doesn't offer this benefit | <1% | Not applicable |
| **"Not required to report"** | Exemption for specific plan types | 2-3% for D11 | Expected |

### Parsing Special Values

```python
SPECIAL_VALUES = [
    "Plan too small to be measured",
    "Plan too new to be measured",
    "Not enough data available",
    "Plan not required to report measure",
    "No data available",
    "Medicare shows only a Star Rating for this topic",
    "CMS identified issues with this plan's data",
    "Benefit not offered by plan",
    "Not required to report",
]

def is_special_value(value):
    """Check if value is special status (not numeric)"""
    value_str = str(value).strip()
    return any(sv in value_str for sv in SPECIAL_VALUES)

def get_special_value_category(value):
    """Categorize special values"""
    value_str = str(value).strip()
    
    if "too small" in value_str:
        return "INSUFFICIENT_SAMPLE"
    elif "too new" in value_str:
        return "HOLD_HARMLESS"
    elif "Not enough data" in value_str:
        return "INSUFFICIENT_DATA"
    elif "not required" in value_str or "Not required" in value_str:
        return "NOT_REQUIRED"
    elif "No data" in value_str:
        return "MISSING_DATA"
    elif "Star Rating for this topic" in value_str:
        return "STAR_ONLY"
    elif "CMS identified issues" in value_str:
        return "DATA_QUALITY_ISSUE"
    elif "Benefit not offered" in value_str:
        return "NOT_OFFERED"
    else:
        return "UNKNOWN"
```

### Measures with High Special Value Rates

**> 50% Special Values** (harder to analyze):
- **C04**: Improving Physical Health - 62% special (mostly "Not enough data")
- **C05**: Improving Mental Health - 62% special
- **C07**: SNP Care Management - 58% special (40% "not required" for non-SNPs)
- **C08**: Medication Review - 57% special
- **C09**: Pain Assessment - 57% special
- **C10**: Osteoporosis Management - 59% special
- **C16**: Improving Bladder Control - 50% special
- **C30**: Quality Improvement - 100% special ("Star Rating only")

**< 20% Special Values** (cleaner data):
- Most clinical measures (C11-C14, C17-C21)
- Most Part D measures (D07-D12)

---

## Inverse Measures (Lower = Better)

### Critical: 3 Measures Use INVERSE Logic

| Measure | Description | Why Inverse |
|---------|-------------|-------------|
| **C18**: Plan All-Cause Readmissions | Hospital readmission rate | Lower readmissions = better care |
| **C28**: Complaints about Health Plan | Complaint rate per 1000 members | Fewer complaints = better service |
| **D02**: Complaints about Drug Plan | Complaint rate per 1000 members | Fewer complaints = better service |

**Also potentially inverse** (need to verify with technical notes):
- **C29**: Members Choosing to Leave the Plan (lower disenrollment = better)
- **D03**: Members Choosing to Leave the Plan (lower disenrollment = better)

### Implementation

```python
INVERSE_MEASURES = {
    'C18': True,   # Readmissions
    'C28': True,   # Complaints health
    'C29': False,  # Disenrollment - VERIFY in tech notes
    'D02': True,   # Complaints drug
    'D03': False,  # Disenrollment - VERIFY in tech notes
}

def is_inverse_measure(measure_code):
    """Check if lower values mean better performance"""
    return INVERSE_MEASURES.get(measure_code, False)

def interpret_performance(measure_code, value, target):
    """
    Determine if performance is above/below target
    considering inverse measures
    """
    if is_inverse_measure(measure_code):
        return value < target  # Lower is better
    else:
        return value > target  # Higher is better
```

### Threshold Direction

**Normal measures**: 5-star = highest values
```
1⭐: < 58%
2⭐: 58% to <71%
3⭐: 71% to <76%
4⭐: 76% to <84%
5⭐: ≥ 84%
```

**Inverse measures**: 5-star = lowest values
```
C18 (Readmissions):
1⭐: > 12%
2⭐: 10% to ≤12%
3⭐: 9% to ≤10%
4⭐: 7% to ≤9%
5⭐: ≤ 7%
```

---

## Cut Point Threshold Parsing

### Threshold String Patterns

Cut point bands use various string formats that need regex parsing:

#### Pattern 1: Standard Range (Most Common)
**Format**: `">= X% to < Y%"` or `">= X to < Y"`  
**Example**: `">= 71 % to < 76 %"` or `">= 78 to < 80"`  
**Regex**: `>=\s*(-?\d+\.?\d*)\s*%?\s*to\s*<\s*(-?\d+\.?\d*)\s*%?`

```python
import re

def parse_standard_range(threshold_str):
    """
    Parse: ">= 71 % to < 76 %"
    Return: (71.0, 76.0, 'inclusive_lower', 'exclusive_upper')
    """
    pattern = r'>=\s*(-?\d+\.?\d*)\s*%?\s*to\s*<\s*(-?\d+\.?\d*)\s*%?'
    match = re.search(pattern, threshold_str)
    if match:
        lower = float(match.group(1))
        upper = float(match.group(2))
        return (lower, upper, '>=', '<')
    return None
```

#### Pattern 2: One-Star Lower Bound
**Format**: `"< X%"` or `"< X"`  
**Example**: `"< 58 %"`  
**Regex**: `<\s*(-?\d+\.?\d*)\s*%?`

```python
def parse_one_star(threshold_str):
    """
    Parse: "< 58 %"
    Return: (None, 58.0, None, '<')
    """
    pattern = r'<\s*(-?\d+\.?\d*)\s*%?'
    match = re.search(pattern, threshold_str)
    if match:
        upper = float(match.group(1))
        return (None, upper, None, '<')
    return None
```

#### Pattern 3: Five-Star Upper Bound
**Format**: `">= X%"` or `">= X"`  
**Example**: `">= 84 %"`  
**Regex**: `>=\s*(-?\d+\.?\d*)\s*%?`

```python
def parse_five_star(threshold_str):
    """
    Parse: ">= 84 %"
    Return: (84.0, None, '>=', None)
    """
    pattern = r'>=\s*(-?\d+\.?\d*)\s*%?(?:\s*$|(?!\s*to))'
    match = re.search(pattern, threshold_str)
    if match:
        lower = float(match.group(1))
        return (lower, None, '>=', None)
    return None
```

#### Pattern 4: Inverse One-Star (High is Bad)
**Format**: `"> X%"` or `"> X"`  
**Example**: `"> 39 %"` or `"> 12 %"`  
**Regex**: `>\s*(-?\d+\.?\d*)\s*%?`

```python
def parse_inverse_one_star(threshold_str):
    """
    Parse: "> 39 %"
    Return: (39.0, None, '>', None)
    Used for inverse measures where high values = 1 star
    """
    pattern = r'>\s*(-?\d+\.?\d*)\s*%?(?:\s*$|(?!\s*to))'
    match = re.search(pattern, threshold_str)
    if match:
        lower = float(match.group(1))
        return (lower, None, '>', None)
    return None
```

#### Pattern 5: Inverse Five-Star (Low is Good)
**Format**: `"<= X%"` or `"<= X"`  
**Example**: `"<= 7 %"`  
**Regex**: `<=\s*(-?\d+\.?\d*)\s*%?`

```python
def parse_inverse_five_star(threshold_str):
    """
    Parse: "<= 7 %"
    Return: (None, 7.0, None, '<=')
    Used for inverse measures where low values = 5 stars
    """
    pattern = r'<=\s*(-?\d+\.?\d*)\s*%?'
    match = re.search(pattern, threshold_str)
    if match:
        upper = float(match.group(1))
        return (None, upper, None, '<=')
    return None
```

#### Pattern 6: Range with Inclusive Upper Bound
**Format**: `"> X to <= Y"` or `">= X to <= Y"`  
**Example**: `"> 0.11 to <= 0.32"`  
**Regex**: `[>]=?\s*(-?\d+\.?\d*)\s*to\s*<=\s*(-?\d+\.?\d*)`

```python
def parse_inclusive_upper_range(threshold_str):
    """
    Parse: "> 0.11 to <= 0.32"
    Return: (0.11, 0.32, '>', '<=')
    """
    pattern = r'([>]=?)\s*(-?\d+\.?\d*)\s*to\s*(<=)\s*(-?\d+\.?\d*)'
    match = re.search(pattern, threshold_str)
    if match:
        lower_op = match.group(1)
        lower = float(match.group(2))
        upper_op = match.group(3)
        upper = float(match.group(4))
        return (lower, upper, lower_op, upper_op)
    return None
```

#### Pattern 7: Exact Value
**Format**: `"100%"` or `"X%"`  
**Example**: `"100%"` (for C31, C32, C33, D01)  
**Regex**: `^\s*(-?\d+\.?\d*)\s*%?\s*$`

```python
def parse_exact_value(threshold_str):
    """
    Parse: "100%"
    Return: (100.0, 100.0, '=', '=')
    """
    pattern = r'^\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.match(pattern, threshold_str)
    if match:
        val = float(match.group(1))
        return (val, val, '=', '=')
    return None
```

### Universal Threshold Parser

```python
def parse_threshold_band(threshold_str):
    """
    Universal parser for all threshold patterns
    Returns: (lower_bound, upper_bound, lower_op, upper_op)
    """
    threshold_str = str(threshold_str).strip()
    
    # Try each pattern in order
    result = (
        parse_standard_range(threshold_str) or
        parse_inclusive_upper_range(threshold_str) or
        parse_five_star(threshold_str) or
        parse_inverse_five_star(threshold_str) or
        parse_one_star(threshold_str) or
        parse_inverse_one_star(threshold_str) or
        parse_exact_value(threshold_str)
    )
    
    if result:
        return result
    else:
        raise ValueError(f"Could not parse threshold: '{threshold_str}'")
```

---

## Part D: MA-PD vs PDP Thresholds

### The Challenge

Part D measures have **TWO different sets of cut points**:
- **MA-PD**: Medicare Advantage with Part D (H-contracts with drug coverage)
- **PDP**: Standalone Prescription Drug Plans (S-contracts)

PDP thresholds are typically **stricter** (higher bars for same star rating).

### File Structure

**Part D Cut Points CSV**:
- Rows 4-8: MA-PD thresholds (1-star through 5-star)
- Rows 9-13: PDP thresholds (1-star through 5-star)

### Example: D08 (Diabetes Adherence)

| Star | MA-PD Threshold | PDP Threshold |
|------|----------------|---------------|
| 1⭐ | < 83% | < 85% |
| 2⭐ | 83% to <86% | 85% to <87% |
| 3⭐ | 86% to <89% | 87% to <89% |
| 4⭐ | 89% to <92% | 89% to <92% |
| 5⭐ | ≥ 92% | ≥ 92% |

**Note**: For 82% performance:
- MA-PD plan → **1 star**
- PDP plan → **1 star**

For 86% performance:
- MA-PD plan → **3 stars**
- PDP plan → **2 stars**

### Implementation

```python
def get_part_d_threshold(measure_code, star_rating, org_type):
    """
    Get appropriate threshold based on organization type
    
    Args:
        measure_code: 'D01', 'D02', etc.
        star_rating: 1, 2, 3, 4, or 5
        org_type: 'MA-PD' or 'PDP'
    
    Returns:
        (lower_bound, upper_bound, lower_op, upper_op)
    """
    # Load appropriate row from Part D cut points
    if org_type == 'MA-PD':
        row_idx = 4 + (star_rating - 1)  # Rows 4-8
    elif org_type == 'PDP':
        row_idx = 9 + (star_rating - 1)  # Rows 9-13
    else:
        raise ValueError(f"Unknown org type: {org_type}")
    
    # Parse threshold for this measure and star level
    threshold_str = cutpoints_df.iloc[row_idx, measure_col_idx]
    return parse_threshold_band(threshold_str)

def determine_org_type_for_part_d(contract_id, org_type_str):
    """
    Determine if contract should use MA-PD or PDP thresholds
    
    Args:
        contract_id: 'H0028', 'S1234', etc.
        org_type_str: From contracts table
    
    Returns:
        'MA-PD' or 'PDP'
    """
    if contract_id.startswith('S'):
        return 'PDP'
    elif contract_id.startswith('H') or contract_id.startswith('R'):
        return 'MA-PD'
    elif 'PDP' in org_type_str:
        return 'PDP'
    else:
        return 'MA-PD'  # Default assumption
```

---

## Value Normalization

### Challenge

Values come in different formats but need to be compared to cut points:
- Performance data: `"76%"`, `"87"`, `"0.16"`
- Cut point thresholds: `">= 76 % to < 84 %"`, `">= 84 to < 86"`, `">= 0.11 to <= 0.32"`

### Solution: Normalize Everything to Float

```python
def normalize_value(value, format_type):
    """
    Convert any value to comparable float
    
    Args:
        value: Raw value from data
        format_type: 'PERCENTAGE', 'INTEGER', 'DECIMAL'
    
    Returns:
        float value ready for comparison
    """
    if is_special_value(value):
        return None
    
    value_str = str(value).strip()
    
    if format_type == 'PERCENTAGE':
        # "76%" -> 76.0
        return float(value_str.replace('%', ''))
    
    elif format_type == 'INTEGER':
        # "87" -> 87.0
        return float(value_str)
    
    elif format_type == 'DECIMAL':
        # "0.16" -> 0.16
        return float(value_str)
    
    else:
        raise ValueError(f"Unknown format type: {format_type}")

def value_in_threshold_band(value, threshold_band):
    """
    Check if value falls within threshold band
    
    Args:
        value: Normalized float
        threshold_band: (lower, upper, lower_op, upper_op)
    
    Returns:
        Boolean
    """
    lower, upper, lower_op, upper_op = threshold_band
    
    # Check lower bound
    if lower is not None:
        if lower_op == '>=':
            if value < lower:
                return False
        elif lower_op == '>':
            if value <= lower:
                return False
    
    # Check upper bound
    if upper is not None:
        if upper_op == '<':
            if value >= upper:
                return False
        elif upper_op == '<=':
            if value > upper:
                return False
        elif upper_op == '=':
            if value != upper:
                return False
    
    return True
```

---

## Complete Parsing Pipeline

```python
def get_contract_measure_report(contract_id):
    """
    Complete pipeline to get formatted report for a contract
    """
    # 1. Get contract info
    contract_row = df_contracts[df_contracts['CONTRACT_ID'] == contract_id].iloc[0]
    org_type = contract_row['Organization Type']
    
    # 2. Determine Part D threshold set
    part_d_threshold_set = determine_org_type_for_part_d(contract_id, org_type)
    
    # 3. Loop through all measures
    report_rows = []
    
    for measure_code in ALL_MEASURE_CODES:
        # Get performance value
        perf_value = df_measure_data.loc[
            df_measure_data['CONTRACT_ID'] == contract_id, 
            measure_code
        ].values[0]
        
        # Get star rating
        star_rating = df_measure_stars.loc[
            df_measure_stars['CONTRACT_ID'] == contract_id,
            measure_code
        ].values[0]
        
        # Handle special values
        if is_special_value(perf_value):
            report_rows.append({
                'measure': measure_code,
                'star': 'N/A',
                'performance': perf_value,
                'band': 'N/A'
            })
            continue
        
        # Determine format
        format_type = get_measure_format(measure_code)
        
        # Normalize value
        norm_value = normalize_value(perf_value, format_type)
        
        # Get appropriate threshold
        if measure_code.startswith('D'):
            threshold_set = part_d_threshold_set
        else:
            threshold_set = 'Part C'
        
        threshold_band = get_threshold(measure_code, star_rating, threshold_set)
        
        # Format band for display
        band_str = format_threshold_band(threshold_band, format_type)
        
        report_rows.append({
            'measure': measure_code,
            'star': f"{star_rating}⭐",
            'performance': perf_value,
            'band': band_str
        })
    
    return pd.DataFrame(report_rows)
```

---

## Testing Checklist

### Edge Cases to Test

- [ ] **Contract with all special values** (new plan)
- [ ] **SNP contract** (has C07, others don't)
- [ ] **PDP contract** (Part D only, no Part C)
- [ ] **MA-only contract** (Part C only, no Part D)
- [ ] **Inverse measures** (C18, C28, D02) - verify star assignment
- [ ] **Percentage formats** (with/without %)
- [ ] **Integer formats** (CAHPS scores)
- [ ] **Decimal formats** (complaint rates)
- [ ] **Exact value thresholds** (100% for C31, C32, C33)
- [ ] **Negative decimals** (C28 quality improvement can be negative)
- [ ] **5-star threshold with no upper bound** (open-ended)
- [ ] **1-star threshold with no lower bound** (open-ended)
- [ ] **MA-PD vs PDP threshold difference** (same performance, different stars)

---

## Summary Statistics

### Data Completeness by Measure

**High Completeness** (>80% numeric):
- D07, D08, D09, D10, D11, D12 (Part D adherence/pricing)
- C11, C12, C13, C14 (Diabetes, BP control)
- C33, D01 (Language access)

**Medium Completeness** (50-80% numeric):
- Most clinical measures
- Most CAHPS measures

**Low Completeness** (<50% numeric):
- C04, C05 (HOS survey measures)
- C07, C08, C09 (SNP-specific or not required)
- C16 (Bladder control)

**No Numeric Values**:
- C30, D04 (Quality improvement composites)

---

## Recommendations

### For Building the Tool

1. **Start with high-completeness measures** (easier to test)
2. **Handle special values first** (35% of data!)
3. **Test with diverse contracts**:
   - H-contract (MA-PD)
   - S-contract (PDP)
   - New plan (lots of "too new")
   - Small plan (lots of "too small")
4. **Validate inverse measure logic** carefully
5. **Build comprehensive test suite** before going to production

### For Data Quality

1. **Flag suspicious patterns**:
   - Performance far outside typical range
   - Star rating doesn't match threshold logic
   - Contract with >50% missing data
2. **Handle edge cases gracefully**
   - Don't crash on unexpected formats
   - Log warnings for manual review
3. **Provide data quality metrics**
   - % measures with numeric values
   - % measures above/below target
   - Data completeness score

---

*This specification covers all known edge cases as of October 17, 2025*  
*Based on analysis of 768 contracts, 45 measures, ~35,000 data points*


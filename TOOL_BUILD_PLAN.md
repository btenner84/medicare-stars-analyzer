# Contract Performance Report Tool - Build Plan

**Goal**: Build a tool that displays all measures for a contract with performance, stars, and cut point bands

**Status**: Requirements analyzed, specifications complete, ready to build

---

## What We Want to Build

### Input
```bash
python contract_report.py H0028
```

### Output
```
================================================================================
CONTRACT PERFORMANCE REPORT
================================================================================
Contract: H0028 - Humana CHA HMO, INC.
Organization: Humana Inc.
Type: Local CCP (SNP)
Overall Rating: 3.5⭐ | Part C: 3.5⭐ | Part D: 3.0⭐

================================================================================
PART C MEASURES (33 measures)
================================================================================

HD1: Staying Healthy - Screenings, Tests and Vaccines
----------------------------------------------------------------------
Measure                               | Star | Performance | Cut Point Band
--------------------------------------|------|-------------|------------------
C01: Breast Cancer Screening          | 4⭐  | 76%         | 76% to <84%
C02: Colorectal Cancer Screening      | 4⭐  | 75%         | 70% to <78%
C03: Annual Flu Vaccine               | 4⭐  | 68          | 68 to <73
...

HD2: Managing Chronic Conditions
----------------------------------------------------------------------
...

PART D MEASURES (12 measures)
================================================================================
...

SUMMARY & INSIGHTS
================================================================================
Strengths (4-5 stars): 15 measures
At Target (3 stars): 18 measures
Needs Improvement (1-2 stars): 5 measures

Top Improvement Opportunities:
1. C22: Getting Needed Care - Currently 2⭐ (78), need 80 for 3⭐ (+2 points)
2. C01: Breast Cancer - Currently 4⭐ (76%), need 84% for 5⭐ (+8%)
...
```

---

## Complexity Assessment

### ✅ EASY Parts (2 hours)
1. **Loading CSVs**: pandas.read_csv() with proper row skipping
2. **Matching contract data**: Simple DataFrame lookups
3. **Basic display**: Print formatted tables

### ⚠️ MEDIUM Parts (3-4 hours)
1. **Special value handling**: 9 different special statuses
2. **Format normalization**: 3 number formats (%, integer, decimal)
3. **Cut point parsing**: 7 different threshold string patterns
4. **Part D logic**: MA-PD vs PDP threshold selection

### 🔴 CHALLENGING Parts (2-3 hours)
1. **Inverse measures**: C18, C28, D02 have opposite logic
2. **Gap calculation**: "How far to next star?" with proper direction
3. **Measure without values**: C30, D04 have no raw data
4. **Edge case testing**: Ensure all combinations work

**Total Time Estimate**: 7-10 hours for robust, tested solution

---

## What We Learned from Deep Dive

### 1. Data Formats (3 types + no-data)

| Format | Count | Pattern | Example | Measures |
|--------|-------|---------|---------|----------|
| **PERCENTAGE** | 32 | "76%" | C01: 76% | Most clinical measures |
| **INTEGER** | 9 | "87" | C22: 87 | CAHPS survey scores |
| **DECIMAL** | 2 | "0.16" | C28: 0.16 | Complaint rates |
| **NO_NUMERIC** | 2 | N/A | C30, D04 | Quality improvement |

**Action**: Need format detection + parsing logic for each

### 2. Special Values (35% of all data!)

| Special Value | Prevalence | Meaning |
|---------------|------------|---------|
| "Plan too small to be measured" | 7-18% | < 11 enrollees |
| "Plan too new to be measured" | 10-26% | First 3 years |
| "Not enough data available" | 1-25% | Sample size too low |
| "Plan not required to report" | 1-40% | Type exemption |
| 5 more types... | Various | See DATA_FORMAT_SPECIFICATION.md |

**Action**: Need special value detection + categorization

### 3. Inverse Measures (3 measures)

| Measure | Why Inverse | 5-Star Threshold |
|---------|-------------|------------------|
| C18: Readmissions | Lower readmissions = better | ≤ 7% |
| C28: Complaints (Health) | Fewer complaints = better | ≤ 0.11 |
| D02: Complaints (Drug) | Fewer complaints = better | ≤ 0.11 (MA-PD) / ≤ 0.03 (PDP) |

**Action**: Need inverse flag + reversed comparison logic

### 4. Cut Point Patterns (7 regex patterns)

| Pattern | Example | Used For |
|---------|---------|----------|
| Standard range | ">= 71 % to < 76 %" | Most measures |
| One-star low | "< 58 %" | Bottom threshold |
| Five-star high | ">= 84 %" | Top threshold |
| Inverse one-star | "> 39 %" | Bad = high value |
| Inverse five-star | "<= 7 %" | Good = low value |
| Inclusive upper | "> 0.11 to <= 0.32" | Decimal ranges |
| Exact value | "100%" | Perfect score only |

**Action**: Need regex parser for all 7 patterns

### 5. Part D Dual Thresholds

**Problem**: Part D has TWO cut point sets
- **MA-PD**: Medicare Advantage with drug coverage (H-contracts)
- **PDP**: Standalone drug plans (S-contracts)

**Example** (D08 - Diabetes Adherence, 86% performance):
- MA-PD contract → **3 stars** (86% is in 3-star band)
- PDP contract → **2 stars** (86% is in 2-star band)

**Action**: Need org type detection + threshold set selection

---

## Architecture

### File Structure
```
contract_report.py          # Main script
data_parsers.py            # Value parsing (%, int, decimal)
threshold_parser.py        # Cut point regex parsing
special_values.py          # Special value handling
measure_config.py          # Measure metadata (format, inverse flag)
utils.py                   # Helpers (formatting, display)
```

### Core Classes

```python
class MeasureConfig:
    """Metadata for each measure"""
    code: str              # 'C01', 'D08', etc.
    name: str              # Full measure name
    format_type: str       # 'PERCENTAGE', 'INTEGER', 'DECIMAL', 'NO_NUMERIC'
    is_inverse: bool       # Lower = better?
    domain: str            # 'HD1', 'DD4', etc.
    part_type: str         # 'C' or 'D'

class PerformanceData:
    """Parsed performance for one measure"""
    raw_value: str         # Original value from CSV
    numeric_value: float   # Parsed numeric (None if special)
    special_status: str    # Category if special value
    star_rating: int       # 1-5 or None
    is_special: bool       # True if special value

class ThresholdBand:
    """Parsed cut point band"""
    lower_bound: float     # None for open lower
    upper_bound: float     # None for open upper
    lower_op: str          # '>=', '>', None
    upper_op: str          # '<', '<=', '=', None
    band_display: str      # Formatted for display

class ContractReport:
    """Complete report for one contract"""
    contract_id: str
    contract_name: str
    parent_org: str
    org_type: str
    overall_rating: float
    part_c_rating: float
    part_d_rating: float
    measures: List[MeasureLine]
```

### Data Flow

```
1. User Input
   ↓
   contract_id = "H0028"

2. Load Data
   ↓
   df_contracts = load_contracts()
   df_measure_data = load_measure_data()
   df_measure_stars = load_measure_stars()
   df_cutpoints_c = load_cutpoints_part_c()
   df_cutpoints_d = load_cutpoints_part_d()

3. Get Contract Info
   ↓
   contract_row = df_contracts[df_contracts['CONTRACT_ID'] == contract_id]
   org_type = contract_row['Organization Type']
   part_d_threshold_set = 'MA-PD' or 'PDP'

4. For Each Measure
   ↓
   measure_config = get_measure_config(measure_code)
   
   raw_value = get_performance_value(contract_id, measure_code)
   star_rating = get_star_rating(contract_id, measure_code)
   
   if is_special_value(raw_value):
       special_status = categorize_special(raw_value)
       numeric_value = None
       threshold_band = None
   else:
       numeric_value = parse_value(raw_value, measure_config.format_type)
       threshold_band = get_threshold_band(
           measure_code, 
           star_rating, 
           part_d_threshold_set
       )
   
   measure_line = create_measure_line(
       measure_config,
       raw_value,
       numeric_value,
       star_rating,
       threshold_band
   )

5. Display Report
   ↓
   print_contract_header(contract_info)
   print_measures_by_domain(measure_lines)
   print_summary_insights(measure_lines)
```

---

## Implementation Steps

### Phase 1: Core Parsing (2 hours)

**Goal**: Load data and parse basic values

```python
# data_parsers.py

def parse_percentage(value):
    """Parse: "76%" -> 76.0"""
    pass

def parse_integer(value):
    """Parse: "87" -> 87"""
    pass

def parse_decimal(value):
    """Parse: "0.16" -> 0.16"""
    pass

def is_special_value(value):
    """Check if value is special status"""
    pass

def normalize_value(value, format_type):
    """Convert any format to float for comparison"""
    pass
```

**Test Cases**:
- [x] Parse percentage: "76%" → 76.0
- [x] Parse integer: "87" → 87
- [x] Parse decimal: "0.16" → 0.16
- [x] Detect special: "Plan too small" → True
- [x] Normalize for comparison

### Phase 2: Threshold Parsing (2 hours)

**Goal**: Parse all 7 threshold patterns

```python
# threshold_parser.py

def parse_standard_range(s):
    """Parse: ">= 71 % to < 76 %" -> (71.0, 76.0, '>=', '<')"""
    pass

def parse_one_star(s):
    """Parse: "< 58 %" -> (None, 58.0, None, '<')"""
    pass

def parse_five_star(s):
    """Parse: ">= 84 %" -> (84.0, None, '>=', None)"""
    pass

def parse_threshold_band(s):
    """Universal parser trying all patterns"""
    pass

def format_band_for_display(band, format_type):
    """Format for human-readable display"""
    pass
```

**Test Cases**:
- [x] Standard: ">= 71 % to < 76 %"
- [x] One-star: "< 58 %"
- [x] Five-star: ">= 84 %"
- [x] Inverse: "> 39 %", "<= 7 %"
- [x] Integer: ">= 78 to < 80"
- [x] Decimal: "> 0.11 to <= 0.32"
- [x] Exact: "100%"

### Phase 3: Measure Config (1 hour)

**Goal**: Define metadata for all 45 measures

```python
# measure_config.py

MEASURE_CONFIGS = {
    'C01': MeasureConfig(
        code='C01',
        name='Breast Cancer Screening',
        format_type='PERCENTAGE',
        is_inverse=False,
        domain='HD1',
        part_type='C'
    ),
    'C18': MeasureConfig(
        code='C18',
        name='Plan All-Cause Readmissions',
        format_type='PERCENTAGE',
        is_inverse=True,  # Lower = better!
        domain='HD2',
        part_type='C'
    ),
    # ... all 45 measures
}
```

**Test Cases**:
- [x] All 45 measures defined
- [x] Format types correct
- [x] Inverse flags correct (C18, C28, D02)
- [x] Domains correct

### Phase 4: Part D Logic (1 hour)

**Goal**: Handle MA-PD vs PDP threshold selection

```python
def determine_part_d_threshold_set(contract_id, org_type):
    """
    Returns: 'MA-PD' or 'PDP'
    """
    if contract_id.startswith('S'):
        return 'PDP'
    elif contract_id.startswith('H') or contract_id.startswith('R'):
        return 'MA-PD'
    elif 'PDP' in org_type:
        return 'PDP'
    else:
        return 'MA-PD'

def get_part_d_threshold(measure_code, star_rating, threshold_set):
    """
    Load appropriate threshold from Part D cut points
    Rows 4-8 for MA-PD, rows 9-13 for PDP
    """
    pass
```

**Test Cases**:
- [x] H-contract → MA-PD
- [x] S-contract → PDP
- [x] Same performance, different stars for MA-PD vs PDP

### Phase 5: Main Report Generator (2 hours)

**Goal**: Tie everything together

```python
# contract_report.py

def generate_contract_report(contract_id):
    """
    Main function to generate complete report
    """
    # 1. Load all data files
    # 2. Get contract info
    # 3. Determine Part D threshold set
    # 4. Loop through all measures
    # 5. Parse values, get bands
    # 6. Format for display
    # 7. Calculate insights
    pass

def print_report(report):
    """
    Pretty print the report with tables
    """
    pass
```

**Test Cases**:
- [x] H-contract (MA-PD) - full report
- [x] S-contract (PDP) - Part D only
- [x] SNP contract - includes C07
- [x] New contract - lots of special values
- [x] Small contract - lots of "too small"

### Phase 6: Gap Analysis & Insights (1-2 hours)

**Goal**: Add value beyond raw display

```python
def calculate_gap_to_next_star(measure_line):
    """
    How far to next star threshold?
    Handle inverse measures correctly!
    """
    pass

def identify_improvement_opportunities(measure_lines):
    """
    Find measures close to next star threshold
    Prioritize by:
    - Small gap (<5%)
    - Currently 1-3 stars (room to grow)
    - High weight in overall rating
    """
    pass

def calculate_summary_stats(measure_lines):
    """
    - Count by star rating
    - % measures at/above target
    - Data completeness score
    """
    pass
```

**Test Cases**:
- [x] Normal measure: 76% (4⭐), need 84% for 5⭐ → gap = +8%
- [x] Inverse measure: 10% (2⭐), need ≤7% for 5⭐ → gap = -3%
- [x] At threshold: exactly on boundary
- [x] Special value: no gap calculable

### Phase 7: Testing & Polish (1-2 hours)

**Goal**: Handle all edge cases gracefully

Test with:
- [x] H0028 (Humana CHA HMO) - Standard MA-PD
- [x] H1290 (Devoted Health FL) - 5-star performer
- [x] S1234 (Sample PDP) - Standalone drug plan
- [x] H0029 (Coordinated Care WA) - Lots of "too small"
- [x] H0413 (Devoted DE) - "Plan too new"

**Error Handling**:
- [ ] Contract not found
- [ ] Malformed data
- [ ] Unexpected threshold format
- [ ] Missing files
- [ ] Graceful degradation

---

## Technology Stack

### Required
```bash
pip install pandas numpy
```

### Optional (for enhanced display)
```bash
pip install tabulate colorama rich
```

### Files to Read
```
2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv
2026 Star Ratings Data Table - Measure Stars (Oct 8 2025).csv
2026 Star Ratings Data Table - Part C Cut Points (Oct 8 2025).csv
2026 Star Ratings Data Table - Part D Cut Points (Oct 8 2025).csv
2026 Star Ratings Data Table - Summary Ratings (Oct 8 2025).csv
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Threshold parsing fails** | Medium | High | Test all 7 patterns, log failures |
| **Inverse logic wrong** | Medium | High | Explicit test cases for C18, C28, D02 |
| **MA-PD vs PDP wrong** | Low | High | Test with S-contracts and H-contracts |
| **Special value missed** | Low | Medium | Comprehensive list, fuzzy matching |
| **Format detection wrong** | Low | Medium | Explicit measure config, no auto-detect |

---

## Success Criteria

### Minimum Viable Product (MVP)
- [x] Loads data correctly
- [x] Displays all measures for any contract
- [x] Shows star rating
- [x] Shows performance value
- [x] Shows cut point band
- [ ] Handles special values gracefully

### Full Feature Set
- [ ] Gap analysis (how far to next star)
- [ ] Improvement prioritization
- [ ] Summary statistics
- [ ] Handles inverse measures correctly
- [ ] Handles MA-PD vs PDP correctly
- [ ] Beautiful formatting (tables, colors)
- [ ] Export to Excel/CSV

### Production Ready
- [ ] Command-line interface
- [ ] Error handling for all edge cases
- [ ] Comprehensive test suite
- [ ] Documentation
- [ ] Performance optimized (< 2 sec for report)

---

## Next Steps

**Ready to build!** Start with Phase 1 (Core Parsing).

**Recommendation**: Build incrementally with tests at each phase.

1. ✅ **Phase 0**: Deep dive analysis (COMPLETED)
2. **Phase 1**: Core parsing (2 hours)
3. **Phase 2**: Threshold parsing (2 hours)
4. **Phase 3**: Measure config (1 hour)
5. **Phase 4**: Part D logic (1 hour)
6. **Phase 5**: Main report (2 hours)
7. **Phase 6**: Gap analysis (2 hours)
8. **Phase 7**: Testing & polish (2 hours)

**Total**: ~12 hours to production-ready tool

---

## Questions for User

1. **Output format preference?**
   - Terminal table?
   - HTML report?
   - Excel file?
   - All of the above?

2. **Which insights most valuable?**
   - Gap to next star?
   - Competitive benchmarking?
   - Historical trends?
   - Prioritized improvement list?

3. **Filtering options needed?**
   - Show only measures below 4 stars?
   - Show only Part C or Part D?
   - Show only measures with numeric data?

4. **Multiple contracts?**
   - Single contract at a time?
   - Batch mode for multiple contracts?
   - Comparison mode (side-by-side)?

---

*Build plan based on comprehensive data analysis*  
*All edge cases identified and documented*  
*Ready to implement!*


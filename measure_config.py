"""
Measure configuration and metadata
Defines format types, inverse flags, and domains for all 45 measures
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class MeasureConfig:
    """Metadata for a single measure"""
    code: str
    name: str
    format_type: str  # 'PERCENTAGE', 'INTEGER', 'DECIMAL', 'NO_NUMERIC'
    is_inverse: bool  # True if lower values = better
    domain: str       # 'HD1', 'HD2', etc.
    part_type: str    # 'C' or 'D'
    weight: float = 1.0  # Measure weight (1x, 1.5x, or 3x typically)


# All 45 measure configurations
MEASURE_CONFIGS: Dict[str, MeasureConfig] = {
    # Part C - HD1: Staying Healthy
    'C01': MeasureConfig('C01', 'Breast Cancer Screening', 'PERCENTAGE', False, 'HD1', 'C'),
    'C02': MeasureConfig('C02', 'Colorectal Cancer Screening', 'PERCENTAGE', False, 'HD1', 'C'),
    'C03': MeasureConfig('C03', 'Annual Flu Vaccine', 'PERCENTAGE', False, 'HD1', 'C'),
    'C04': MeasureConfig('C04', 'Improving or Maintaining Physical Health', 'PERCENTAGE', False, 'HD1', 'C'),
    'C05': MeasureConfig('C05', 'Improving or Maintaining Mental Health', 'PERCENTAGE', False, 'HD1', 'C'),
    'C06': MeasureConfig('C06', 'Monitoring Physical Activity', 'PERCENTAGE', False, 'HD1', 'C'),
    
    # Part C - HD2: Managing Chronic Conditions
    'C07': MeasureConfig('C07', 'Special Needs Plan (SNP) Care Management', 'PERCENTAGE', False, 'HD2', 'C'),
    'C08': MeasureConfig('C08', 'Care for Older Adults – Medication Review', 'PERCENTAGE', False, 'HD2', 'C'),
    'C09': MeasureConfig('C09', 'Care for Older Adults – Pain Assessment', 'PERCENTAGE', False, 'HD2', 'C'),
    'C10': MeasureConfig('C10', 'Osteoporosis Management in Women who had a Fracture', 'PERCENTAGE', False, 'HD2', 'C'),
    'C11': MeasureConfig('C11', 'Diabetes Care – Eye Exam', 'PERCENTAGE', False, 'HD2', 'C'),
    'C12': MeasureConfig('C12', 'Diabetes Care – Blood Sugar Controlled', 'PERCENTAGE', False, 'HD2', 'C', weight=3.0),
    'C13': MeasureConfig('C13', 'Kidney Health Evaluation for Patients with Diabetes', 'PERCENTAGE', False, 'HD2', 'C'),
    'C14': MeasureConfig('C14', 'Controlling High Blood Pressure', 'PERCENTAGE', False, 'HD2', 'C', weight=3.0),
    'C15': MeasureConfig('C15', 'Reducing the Risk of Falling', 'PERCENTAGE', False, 'HD2', 'C'),
    'C16': MeasureConfig('C16', 'Improving Bladder Control', 'PERCENTAGE', False, 'HD2', 'C'),
    'C17': MeasureConfig('C17', 'Medication Reconciliation Post-Discharge', 'PERCENTAGE', False, 'HD2', 'C'),
    'C18': MeasureConfig('C18', 'Plan All-Cause Readmissions', 'PERCENTAGE', True, 'HD2', 'C', weight=3.0),  # INVERSE!
    'C19': MeasureConfig('C19', 'Statin Therapy for Patients with Cardiovascular Disease', 'PERCENTAGE', False, 'HD2', 'C'),
    'C20': MeasureConfig('C20', 'Transitions of Care', 'PERCENTAGE', False, 'HD2', 'C'),
    'C21': MeasureConfig('C21', 'Follow-up after Emergency Department Visit for People with Multiple High-Risk Chronic Conditions', 'PERCENTAGE', False, 'HD2', 'C'),
    
    # Part C - HD3: Member Experience
    'C22': MeasureConfig('C22', 'Getting Needed Care', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    'C23': MeasureConfig('C23', 'Getting Appointments and Care Quickly', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    'C24': MeasureConfig('C24', 'Customer Service', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    'C25': MeasureConfig('C25', 'Rating of Health Care Quality', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    'C26': MeasureConfig('C26', 'Rating of Health Plan', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    'C27': MeasureConfig('C27', 'Care Coordination', 'INTEGER', False, 'HD3', 'C', weight=2.0),
    
    # Part C - HD4: Complaints and Changes
    'C28': MeasureConfig('C28', 'Complaints about the Health Plan', 'DECIMAL', True, 'HD4', 'C', weight=2.0),  # INVERSE!
    'C29': MeasureConfig('C29', 'Members Choosing to Leave the Plan', 'PERCENTAGE', True, 'HD4', 'C', weight=2.0),  # INVERSE!
    'C30': MeasureConfig('C30', 'Health Plan Quality Improvement', 'NO_NUMERIC', False, 'HD4', 'C', weight=5.0),
    
    # Part C - HD5: Customer Service
    'C31': MeasureConfig('C31', 'Plan Makes Timely Decisions about Appeals', 'PERCENTAGE', False, 'HD5', 'C', weight=2.0),
    'C32': MeasureConfig('C32', 'Reviewing Appeals Decisions', 'PERCENTAGE', False, 'HD5', 'C', weight=2.0),
    'C33': MeasureConfig('C33', 'Call Center – Foreign Language Interpreter and TTY Availability', 'PERCENTAGE', False, 'HD5', 'C', weight=2.0),
    
    # Part D - DD1: Customer Service
    'D01': MeasureConfig('D01', 'Call Center – Foreign Language Interpreter and TTY Availability', 'PERCENTAGE', False, 'DD1', 'D', weight=2.0),
    
    # Part D - DD2: Complaints and Changes
    'D02': MeasureConfig('D02', 'Complaints about the Drug Plan', 'DECIMAL', True, 'DD2', 'D', weight=0),  # INVERSE! Weight=0 to avoid double counting with C28
    'D03': MeasureConfig('D03', 'Members Choosing to Leave the Plan', 'PERCENTAGE', True, 'DD2', 'D', weight=0),  # INVERSE! Weight=0 to avoid double counting with C29
    'D04': MeasureConfig('D04', 'Drug Plan Quality Improvement', 'NO_NUMERIC', False, 'DD2', 'D', weight=5.0),
    
    # Part D - DD3: Member Experience
    'D05': MeasureConfig('D05', 'Rating of Drug Plan', 'INTEGER', False, 'DD3', 'D', weight=2.0),
    'D06': MeasureConfig('D06', 'Getting Needed Prescription Drugs', 'INTEGER', False, 'DD3', 'D', weight=2.0),
    
    # Part D - DD4: Drug Safety and Accuracy
    'D07': MeasureConfig('D07', 'MPF Price Accuracy', 'INTEGER', False, 'DD4', 'D'),
    'D08': MeasureConfig('D08', 'Medication Adherence for Diabetes Medications', 'PERCENTAGE', False, 'DD4', 'D', weight=3.0),
    'D09': MeasureConfig('D09', 'Medication Adherence for Hypertension (RAS antagonists)', 'PERCENTAGE', False, 'DD4', 'D', weight=3.0),
    'D10': MeasureConfig('D10', 'Medication Adherence for Cholesterol (Statins)', 'PERCENTAGE', False, 'DD4', 'D', weight=3.0),
    'D11': MeasureConfig('D11', 'MTM Program Completion Rate for CMR', 'PERCENTAGE', False, 'DD4', 'D'),
    'D12': MeasureConfig('D12', 'Statin Use in Persons with Diabetes (SUPD)', 'PERCENTAGE', False, 'DD4', 'D'),
}


# Domain names for display
DOMAIN_NAMES = {
    'HD1': 'Staying Healthy: Screenings, Tests and Vaccines',
    'HD2': 'Managing Chronic (Long Term) Conditions',
    'HD3': 'Member Experience with Health Plan',
    'HD4': 'Member Complaints and Changes in Health Plan Performance',
    'HD5': 'Health Plan Customer Service',
    'DD1': 'Drug Plan Customer Service',
    'DD2': 'Member Complaints and Changes in Drug Plan Performance',
    'DD3': 'Member Experience with the Drug Plan',
    'DD4': 'Drug Safety and Accuracy of Drug Pricing',
}


def get_measure_config(measure_code: str) -> MeasureConfig:
    """Get configuration for a measure"""
    if measure_code not in MEASURE_CONFIGS:
        raise ValueError(f"Unknown measure code: {measure_code}")
    return MEASURE_CONFIGS[measure_code]


def get_all_part_c_measures():
    """Get all Part C measure codes in order"""
    return [code for code in MEASURE_CONFIGS.keys() if code.startswith('C')]


def get_all_part_d_measures():
    """Get all Part D measure codes in order"""
    return [code for code in MEASURE_CONFIGS.keys() if code.startswith('D')]


def get_measures_by_domain(domain: str):
    """Get all measures for a specific domain"""
    return [
        code for code, config in MEASURE_CONFIGS.items()
        if config.domain == domain
    ]


def get_inverse_measures():
    """Get all inverse measures (lower = better)"""
    return [
        code for code, config in MEASURE_CONFIGS.items()
        if config.is_inverse
    ]


# Test and validation
if __name__ == "__main__":
    print("Testing measure configuration...")
    
    # Validate all measures present
    assert len(MEASURE_CONFIGS) == 45, f"Expected 45 measures, got {len(MEASURE_CONFIGS)}"
    print(f"✓ All 45 measures configured")
    
    # Check Part C/D split
    part_c = get_all_part_c_measures()
    part_d = get_all_part_d_measures()
    assert len(part_c) == 33, f"Expected 33 Part C measures, got {len(part_c)}"
    assert len(part_d) == 12, f"Expected 12 Part D measures, got {len(part_d)}"
    print(f"✓ Part C: {len(part_c)} measures, Part D: {len(part_d)} measures")
    
    # Check inverse measures
    inverse = get_inverse_measures()
    assert 'C18' in inverse, "C18 should be inverse"
    assert 'C28' in inverse, "C28 should be inverse"
    assert 'D02' in inverse, "D02 should be inverse"
    print(f"✓ Inverse measures: {inverse}")
    
    # Check format types
    percentage_measures = [c for c, m in MEASURE_CONFIGS.items() if m.format_type == 'PERCENTAGE']
    integer_measures = [c for c, m in MEASURE_CONFIGS.items() if m.format_type == 'INTEGER']
    decimal_measures = [c for c, m in MEASURE_CONFIGS.items() if m.format_type == 'DECIMAL']
    no_numeric_measures = [c for c, m in MEASURE_CONFIGS.items() if m.format_type == 'NO_NUMERIC']
    
    print(f"✓ Format distribution:")
    print(f"  - PERCENTAGE: {len(percentage_measures)} measures")
    print(f"  - INTEGER: {len(integer_measures)} measures")
    print(f"  - DECIMAL: {len(decimal_measures)} measures")
    print(f"  - NO_NUMERIC: {len(no_numeric_measures)} measures")
    
    # Test accessor
    config = get_measure_config('C01')
    assert config.name == 'Breast Cancer Screening'
    assert config.format_type == 'PERCENTAGE'
    assert config.is_inverse == False
    print(f"✓ Measure accessor works")
    
    # Test domains
    hd1_measures = get_measures_by_domain('HD1')
    assert len(hd1_measures) == 6, f"Expected 6 HD1 measures, got {len(hd1_measures)}"
    print(f"✓ Domain grouping works")
    
    print("\n✅ All measure configuration tests passed!")


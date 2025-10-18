"""
Core data parsing functions for Medicare Stars data
Handles percentages, integers, decimals, and special values
"""

import re
from typing import Optional, Tuple

# Special value patterns
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


def is_special_value(value) -> bool:
    """
    Check if value is a special status (not numeric)
    
    Args:
        value: Raw value from CSV
        
    Returns:
        True if special status, False if numeric
    """
    if value is None or str(value).strip() == '':
        return True
        
    value_str = str(value).strip()
    
    # Check against known special values
    for special in SPECIAL_VALUES:
        if special in value_str:
            return True
    
    return False


def categorize_special_value(value) -> str:
    """
    Categorize type of special value
    
    Returns:
        Category string or 'UNKNOWN'
    """
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


def parse_percentage(value) -> Optional[float]:
    """
    Parse percentage format: "76%" -> 76.0
    
    Args:
        value: String like "76%" or "82%"
        
    Returns:
        Float value or None if cannot parse
    """
    try:
        value_str = str(value).strip()
        if '%' in value_str:
            return float(value_str.replace('%', '').strip())
    except (ValueError, AttributeError):
        pass
    return None


def parse_integer(value) -> Optional[int]:
    """
    Parse integer format: "87" -> 87
    
    Args:
        value: String like "87" or "91"
        
    Returns:
        Integer value or None if cannot parse
    """
    try:
        value_str = str(value).strip()
        # Make sure it's actually an integer (no % or decimal)
        if '%' not in value_str and '.' not in value_str:
            return int(float(value_str))
    except (ValueError, AttributeError):
        pass
    return None


def parse_decimal(value) -> Optional[float]:
    """
    Parse decimal format: "0.16" -> 0.16
    
    Args:
        value: String like "0.16" or "1.34"
        
    Returns:
        Float value or None if cannot parse
    """
    try:
        value_str = str(value).strip()
        # Make sure no % sign
        if '%' not in value_str:
            return float(value_str)
    except (ValueError, AttributeError):
        pass
    return None


def normalize_value(value, format_type: str) -> Optional[float]:
    """
    Convert any value format to comparable float
    
    Args:
        value: Raw value from CSV
        format_type: One of 'PERCENTAGE', 'INTEGER', 'DECIMAL', 'NO_NUMERIC'
        
    Returns:
        Normalized float value or None if special/unparseable
    """
    # Check for special values first
    if is_special_value(value):
        return None
    
    # Parse based on format type
    if format_type == 'PERCENTAGE':
        return parse_percentage(value)
    elif format_type == 'INTEGER':
        result = parse_integer(value)
        return float(result) if result is not None else None
    elif format_type == 'DECIMAL':
        return parse_decimal(value)
    elif format_type == 'NO_NUMERIC':
        return None
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def parse_star_rating(value) -> Optional[int]:
    """
    Parse star rating value
    
    Args:
        value: String or number representing stars (1-5)
        
    Returns:
        Integer 1-5 or None if special value
    """
    if is_special_value(value):
        return None
    
    try:
        star = int(float(str(value).strip()))
        if 1 <= star <= 5:
            return star
    except (ValueError, AttributeError):
        pass
    
    return None


def format_value_for_display(value, format_type: str) -> str:
    """
    Format value for human-readable display
    
    Args:
        value: Raw or normalized value
        format_type: Format type
        
    Returns:
        Formatted string
    """
    if is_special_value(value):
        return str(value).strip()
    
    try:
        if format_type == 'PERCENTAGE':
            num = normalize_value(value, format_type)
            return f"{num:.1f}%" if num is not None else str(value)
        elif format_type == 'INTEGER':
            num = normalize_value(value, format_type)
            return f"{int(num)}" if num is not None else str(value)
        elif format_type == 'DECIMAL':
            num = normalize_value(value, format_type)
            return f"{num:.2f}" if num is not None else str(value)
        else:
            return str(value)
    except:
        return str(value)


# Test cases
if __name__ == "__main__":
    print("Testing data parsers...")
    
    # Test percentages
    assert parse_percentage("76%") == 76.0
    assert parse_percentage("82%") == 82.0
    assert parse_percentage("100%") == 100.0
    print("✓ Percentage parsing works")
    
    # Test integers
    assert parse_integer("87") == 87
    assert parse_integer("91") == 91
    print("✓ Integer parsing works")
    
    # Test decimals
    assert parse_decimal("0.16") == 0.16
    assert parse_decimal("1.34") == 1.34
    assert parse_decimal("-0.12") == -0.12
    print("✓ Decimal parsing works")
    
    # Test special values
    assert is_special_value("Plan too small to be measured") == True
    assert is_special_value("76%") == False
    assert categorize_special_value("Plan too new to be measured") == "HOLD_HARMLESS"
    print("✓ Special value detection works")
    
    # Test normalization
    assert normalize_value("76%", "PERCENTAGE") == 76.0
    assert normalize_value("87", "INTEGER") == 87.0
    assert normalize_value("0.16", "DECIMAL") == 0.16
    assert normalize_value("Plan too small", "PERCENTAGE") is None
    print("✓ Normalization works")
    
    print("\n✅ All data parser tests passed!")


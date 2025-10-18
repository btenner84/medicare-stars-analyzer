"""
Threshold band parsing for cut points
Handles all 7 threshold string patterns with regex
"""

import re
from typing import Optional, Tuple

# Type alias for threshold band
ThresholdBand = Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]


def parse_standard_range(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: ">= 71 % to < 76 %" or ">= 78 to < 80"
    Returns: (71.0, 76.0, '>=', '<')
    """
    # Pattern handles with or without % and spaces
    pattern = r'>=\s*(-?\d+\.?\d*)\s*%?\s*to\s*<\s*(-?\d+\.?\d*)\s*%?'
    match = re.search(pattern, threshold_str)
    if match:
        lower = float(match.group(1))
        upper = float(match.group(2))
        return (lower, upper, '>=', '<')
    return None


def parse_one_star_upper(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: "< 58 %" or "< 58"
    Returns: (None, 58.0, None, '<')
    """
    pattern = r'^<\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.search(pattern, threshold_str.strip())
    if match:
        upper = float(match.group(1))
        return (None, upper, None, '<')
    return None


def parse_five_star_lower(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: ">= 84 %" or ">= 84"
    Returns: (84.0, None, '>=', None)
    """
    # Make sure it's not part of a range (no "to" after)
    pattern = r'>=\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.search(pattern, threshold_str.strip())
    if match and ' to ' not in threshold_str.lower():
        lower = float(match.group(1))
        return (lower, None, '>=', None)
    return None


def parse_inverse_one_star(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: "> 39 %" or "> 12 %"
    Returns: (39.0, None, '>', None)
    For inverse measures where high values = 1 star
    """
    pattern = r'^>\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.search(pattern, threshold_str.strip())
    if match and ' to ' not in threshold_str.lower():
        lower = float(match.group(1))
        return (lower, None, '>', None)
    return None


def parse_inverse_five_star(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: "<= 7 %" or "<= 0.11"
    Returns: (None, 7.0, None, '<=')
    For inverse measures where low values = 5 stars
    """
    pattern = r'^<=\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.search(pattern, threshold_str.strip())
    if match:
        upper = float(match.group(1))
        return (None, upper, None, '<=')
    return None


def parse_inclusive_upper_range(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: "> 0.11 to <= 0.32" or ">= 0.11 to <= 0.32"
    Returns: (0.11, 0.32, '>', '<=') or (0.11, 0.32, '>=', '<=')
    """
    pattern = r'([>]=?)\s*(-?\d+\.?\d*)\s*%?\s*to\s*(<=)\s*(-?\d+\.?\d*)\s*%?'
    match = re.search(pattern, threshold_str)
    if match:
        lower_op = match.group(1)
        lower = float(match.group(2))
        upper_op = match.group(3)
        upper = float(match.group(4))
        return (lower, upper, lower_op, upper_op)
    return None


def parse_exact_value(threshold_str: str) -> Optional[ThresholdBand]:
    """
    Parse: "100%" or "100"
    Returns: (100.0, 100.0, '=', '=')
    """
    pattern = r'^\s*(-?\d+\.?\d*)\s*%?\s*$'
    match = re.match(pattern, threshold_str.strip())
    if match:
        val = float(match.group(1))
        # Only treat as exact if it looks like a standalone value
        if '<' not in threshold_str and '>' not in threshold_str and 'to' not in threshold_str.lower():
            return (val, val, '=', '=')
    return None


def parse_threshold_band(threshold_str: str) -> ThresholdBand:
    """
    Universal parser for all threshold patterns
    
    Args:
        threshold_str: Threshold string from cut points file
        
    Returns:
        (lower_bound, upper_bound, lower_op, upper_op)
        
    Raises:
        ValueError: If cannot parse
    """
    threshold_str = str(threshold_str).strip()
    
    # Try each pattern in order (most specific first)
    result = (
        parse_inclusive_upper_range(threshold_str) or
        parse_standard_range(threshold_str) or
        parse_five_star_lower(threshold_str) or
        parse_inverse_five_star(threshold_str) or
        parse_one_star_upper(threshold_str) or
        parse_inverse_one_star(threshold_str) or
        parse_exact_value(threshold_str)
    )
    
    if result:
        return result
    else:
        raise ValueError(f"Could not parse threshold: '{threshold_str}'")


def format_band_for_display(band: ThresholdBand, format_type: str) -> str:
    """
    Format threshold band for human-readable display
    
    Args:
        band: (lower, upper, lower_op, upper_op)
        format_type: 'PERCENTAGE', 'INTEGER', 'DECIMAL'
        
    Returns:
        Formatted string like "76% to <84%" or "78 to <80"
    """
    lower, upper, lower_op, upper_op = band
    
    # Determine format suffix
    suffix = '%' if format_type == 'PERCENTAGE' else ''
    
    # Format numbers based on type
    if format_type == 'DECIMAL':
        fmt = '.2f'
    elif format_type == 'INTEGER':
        fmt = '.0f'
    else:  # PERCENTAGE
        fmt = '.1f'
    
    # Build display string
    parts = []
    
    if lower is not None and lower_op:
        if lower_op == '>=':
            parts.append(f"{lower:{fmt}}{suffix}")
        elif lower_op == '>':
            parts.append(f">{lower:{fmt}}{suffix}")
        elif lower_op == '=':
            parts.append(f"{lower:{fmt}}{suffix}")
    
    if upper is not None and upper_op:
        if lower is not None:
            if upper_op == '<':
                parts.append(f" to <{upper:{fmt}}{suffix}")
            elif upper_op == '<=':
                parts.append(f" to {upper:{fmt}}{suffix}")
            elif upper_op == '=':
                parts.append(f"")  # Exact value, already shown
        else:
            if upper_op == '<':
                parts.append(f"<{upper:{fmt}}{suffix}")
            elif upper_op == '<=':
                parts.append(f"≤{upper:{fmt}}{suffix}")
    
    # Handle open upper bound
    if lower is not None and upper is None and lower_op in ['>=', '>']:
        if lower_op == '>=':
            parts.append('+')
        else:
            parts.append('+')
    
    return ''.join(parts)


def value_in_threshold_band(value: float, band: ThresholdBand) -> bool:
    """
    Check if value falls within threshold band
    
    Args:
        value: Normalized float value
        band: (lower, upper, lower_op, upper_op)
        
    Returns:
        True if value is in band
    """
    lower, upper, lower_op, upper_op = band
    
    # Check lower bound
    if lower is not None and lower_op:
        if lower_op == '>=':
            if value < lower:
                return False
        elif lower_op == '>':
            if value <= lower:
                return False
        elif lower_op == '=':
            if value != lower:
                return False
    
    # Check upper bound
    if upper is not None and upper_op:
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


# Test cases
if __name__ == "__main__":
    print("Testing threshold parser...")
    
    # Test standard range
    band = parse_threshold_band(">= 71 % to < 76 %")
    assert band == (71.0, 76.0, '>=', '<')
    assert format_band_for_display(band, 'PERCENTAGE') == "71.0% to <76.0%"
    print("✓ Standard range works")
    
    # Test one-star
    band = parse_threshold_band("< 58 %")
    assert band == (None, 58.0, None, '<')
    print("✓ One-star upper bound works")
    
    # Test five-star
    band = parse_threshold_band(">= 84 %")
    assert band == (84.0, None, '>=', None)
    print("✓ Five-star lower bound works")
    
    # Test inverse patterns
    band = parse_threshold_band("> 39 %")
    assert band == (39.0, None, '>', None)
    print("✓ Inverse one-star works")
    
    band = parse_threshold_band("<= 7 %")
    assert band == (None, 7.0, None, '<=')
    print("✓ Inverse five-star works")
    
    # Test integer format
    band = parse_threshold_band(">= 78 to < 80")
    assert band == (78.0, 80.0, '>=', '<')
    assert format_band_for_display(band, 'INTEGER') == "78 to <80"
    print("✓ Integer range works")
    
    # Test decimal format
    band = parse_threshold_band("> 0.11 to <= 0.32")
    assert band == (0.11, 0.32, '>', '<=')
    assert format_band_for_display(band, 'DECIMAL') == ">0.11 to 0.32"
    print("✓ Decimal range works")
    
    # Test exact value
    band = parse_threshold_band("100%")
    assert band == (100.0, 100.0, '=', '=')
    print("✓ Exact value works")
    
    # Test value in band
    band = (71.0, 76.0, '>=', '<')
    assert value_in_threshold_band(73.0, band) == True
    assert value_in_threshold_band(70.0, band) == False
    assert value_in_threshold_band(76.0, band) == False
    print("✓ Value in band check works")
    
    print("\n✅ All threshold parser tests passed!")


#!/usr/bin/env python3
"""
Comprehensive analysis of Medicare Stars measure data formats and edge cases
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict

print("="*100)
print("MEDICARE STARS - COMPREHENSIVE DATA FORMAT ANALYSIS")
print("="*100)

# Load the files with proper row handling
print("\n📁 Loading data files...")

# Measure Data - row 3 has measure codes, row 4 has date periods, data starts row 5
df_header = pd.read_csv('2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv', 
                        nrows=3)

# Extract measure codes from row 3 (index 2)
measure_codes_row = pd.read_csv('2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv', 
                                skiprows=2, nrows=1, header=None)
measure_codes = measure_codes_row.iloc[0, 5:].tolist()  # Skip first 5 contract columns

# Load actual data
df_data = pd.read_csv('2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv', 
                      skiprows=4)

print(f"✓ Loaded {len(df_data)} contracts")
print(f"✓ Found {len(measure_codes)} measures")

# Load measure stars for comparison
df_stars = pd.read_csv('2026 Star Ratings Data Table - Measure Stars (Oct 8 2025).csv',
                       skiprows=4)

# Load cut points
df_cutpoints_c = pd.read_csv('2026 Star Ratings Data Table - Part C Cut Points (Oct 8 2025).csv')
df_cutpoints_d = pd.read_csv('2026 Star Ratings Data Table - Part D Cut Points (Oct 8 2025).csv')

print("\n" + "="*100)
print("MEASURE-BY-MEASURE ANALYSIS")
print("="*100)

# Store results
analysis_results = []

for i, measure_code in enumerate(measure_codes):
    col_idx = 5 + i  # Data columns start at index 5
    measure_col = df_data.columns[col_idx]
    star_col = df_stars.columns[col_idx]
    
    print(f"\n{'='*100}")
    print(f"📊 MEASURE {i+1}/45: {measure_code}")
    print('='*100)
    
    # Get values
    values = df_data.iloc[:, col_idx].dropna()
    star_values = df_stars.iloc[:, col_idx].dropna()
    
    # Classify values
    numeric_values = []
    special_values = defaultdict(int)
    
    for val in values:
        val_str = str(val).strip()
        
        # Try to identify numeric values
        # Patterns: "76%", "68", "0.16", "100%"
        if re.match(r'^-?\d+\.?\d*%?$', val_str):
            numeric_values.append(val_str)
        else:
            special_values[val_str] += 1
    
    print(f"\n📈 Value Distribution:")
    print(f"  Total contracts: {len(values)}")
    print(f"  Numeric values: {len(numeric_values)} ({len(numeric_values)/len(values)*100:.1f}%)")
    print(f"  Special values: {len(values) - len(numeric_values)} ({(len(values)-len(numeric_values))/len(values)*100:.1f}%)")
    
    # Special values breakdown
    if special_values:
        print(f"\n⚠️  Special Values:")
        for sv, count in sorted(special_values.items(), key=lambda x: -x[1]):
            print(f"    • '{sv}' → {count} contracts ({count/len(values)*100:.1f}%)")
    
    # Analyze numeric format
    if numeric_values:
        print(f"\n🔢 Numeric Format Analysis:")
        
        # Detect format type
        has_percent = any('%' in v for v in numeric_values)
        has_decimal = any('.' in v.replace('%', '') for v in numeric_values)
        
        if has_percent:
            format_type = "PERCENTAGE"
            print(f"  Format: PERCENTAGE (values like '76%')")
            # Clean and get range
            clean_vals = [float(v.replace('%', '')) for v in numeric_values if '%' in v]
            if clean_vals:
                print(f"  Range: {min(clean_vals):.2f}% to {max(clean_vals):.2f}%")
                print(f"  Mean: {np.mean(clean_vals):.2f}%")
                print(f"  Samples: {numeric_values[:5]}")
        elif has_decimal:
            format_type = "DECIMAL"
            print(f"  Format: DECIMAL (values like '0.16')")
            clean_vals = [float(v) for v in numeric_values]
            if clean_vals:
                print(f"  Range: {min(clean_vals):.4f} to {max(clean_vals):.4f}")
                print(f"  Mean: {np.mean(clean_vals):.4f}")
                print(f"  Samples: {numeric_values[:5]}")
        else:
            format_type = "INTEGER"
            print(f"  Format: INTEGER (values like '68')")
            clean_vals = [int(float(v)) for v in numeric_values]
            if clean_vals:
                print(f"  Range: {min(clean_vals)} to {max(clean_vals)}")
                print(f"  Mean: {np.mean(clean_vals):.1f}")
                print(f"  Samples: {numeric_values[:5]}")
    else:
        format_type = "NO_NUMERIC"
        print(f"\n🔢 No numeric values found (all special values)")
    
    # Analyze star ratings
    numeric_stars = [v for v in star_values if str(v) not in ['Plan too small to be measured ', 
                                                                'Plan too new to be measured ',
                                                                'Plan not required to report measure ',
                                                                'Not enough data available ',
                                                                'No data available ']]
    
    if numeric_stars:
        # Convert to int
        star_ints = [int(float(str(s))) for s in numeric_stars if str(s).replace('.','').isdigit()]
        if star_ints:
            print(f"\n⭐ Star Rating Distribution:")
            for star in [5, 4, 3, 2, 1]:
                count = star_ints.count(star)
                if count > 0:
                    pct = count / len(star_ints) * 100
                    bar = '█' * int(pct / 2)
                    print(f"    {star}⭐: {count:3d} contracts ({pct:5.1f}%) {bar}")
    
    # Check if inverse measure
    is_inverse = 'readmission' in measure_code.lower() or 'complaint' in measure_code.lower() or 'leaving' in measure_code.lower()
    
    if is_inverse:
        print(f"\n🔄 INVERSE MEASURE: Lower values = Better performance")
    
    # Store results
    analysis_results.append({
        'measure_code': measure_code,
        'format_type': format_type if numeric_values else 'NO_NUMERIC',
        'numeric_count': len(numeric_values),
        'special_count': len(values) - len(numeric_values),
        'is_inverse': is_inverse,
        'has_data': len(numeric_values) > 0
    })
    
    print("\n" + "-"*100)

# Summary table
print("\n\n" + "="*100)
print("📋 SUMMARY TABLE - ALL MEASURES")
print("="*100)

print(f"\n{'Measure':<50} {'Format':<12} {'Numeric':<8} {'Special':<8} {'Inverse':<8}")
print("-"*100)

for result in analysis_results:
    code_short = result['measure_code'][:47] + '...' if len(result['measure_code']) > 50 else result['measure_code']
    inverse_mark = "⚠️ YES" if result['is_inverse'] else "No"
    print(f"{code_short:<50} {result['format_type']:<12} {result['numeric_count']:<8} {result['special_count']:<8} {inverse_mark:<8}")

print("\n" + "="*100)
print("🎯 KEY FINDINGS")
print("="*100)

# Count by format
format_counts = defaultdict(int)
for r in analysis_results:
    format_counts[r['format_type']] += 1

print(f"\n📊 Formats Distribution:")
for fmt, count in format_counts.items():
    print(f"  • {fmt}: {count} measures")

# Inverse measures
inverse_measures = [r['measure_code'] for r in analysis_results if r['is_inverse']]
print(f"\n🔄 Inverse Measures (lower = better): {len(inverse_measures)}")
for m in inverse_measures:
    print(f"  • {m}")

# Measures with lots of special values
high_special = [r for r in analysis_results if r['special_count'] > r['numeric_count']]
print(f"\n⚠️  Measures with >50% special values: {len(high_special)}")
for r in high_special[:5]:  # Show first 5
    pct = r['special_count'] / (r['numeric_count'] + r['special_count']) * 100
    print(f"  • {r['measure_code'][:60]}: {pct:.1f}% special")

print("\n" + "="*100)
print("✓ Analysis complete!")
print("="*100)


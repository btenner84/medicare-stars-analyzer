#!/usr/bin/env python3
"""
Contract Performance Report Tool
Displays all measures for a contract with star ratings and cut point bands
"""

import sys
import pandas as pd
from typing import Optional, List, Dict
from dataclasses import dataclass

# Import our modules
from data_parsers import (
    is_special_value, normalize_value, parse_star_rating,
    format_value_for_display, categorize_special_value
)
from threshold_parser import parse_threshold_band, format_band_for_display
from measure_config import (
    get_measure_config, get_all_part_c_measures, get_all_part_d_measures,
    DOMAIN_NAMES, get_measures_by_domain
)


@dataclass
class MeasureLine:
    """Data for one measure in the report"""
    measure_code: str
    measure_name: str
    star_rating: Optional[int]
    performance_value: str
    performance_numeric: Optional[float]
    threshold_band: Optional[str]
    threshold_lower: Optional[float]
    threshold_upper: Optional[float]
    is_special: bool
    special_category: Optional[str]
    domain: str


class ContractReportGenerator:
    """Generates performance reports for Medicare contracts"""
    
    def __init__(self):
        """Load all data files"""
        print("Loading data files...")
        
        # Load contracts and summary
        self.df_summary = pd.read_csv(
            '2026 Star Ratings Data Table - Summary Ratings (Oct 8 2025).csv',
            skiprows=2
        )
        
        # Load measure data (skiprows=4 to get past headers)
        self.df_measure_data = pd.read_csv(
            '2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv',
            skiprows=4
        )
        
        # Load measure stars
        self.df_measure_stars = pd.read_csv(
            '2026 Star Ratings Data Table - Measure Stars (Oct 8 2025).csv',
            skiprows=4
        )
        
        # Load cut points
        self.df_cutpoints_c = pd.read_csv(
            '2026 Star Ratings Data Table - Part C Cut Points (Oct 8 2025).csv'
        )
        
        self.df_cutpoints_d = pd.read_csv(
            '2026 Star Ratings Data Table - Part D Cut Points (Oct 8 2025).csv'
        )
        
        # Get measure codes from row 3 (index 2) of measure data file
        measure_codes_df = pd.read_csv(
            '2026 Star Ratings Data Table - Measure Data (Oct 8 2025).csv',
            skiprows=2,
            nrows=1,
            header=None
        )
        self.measure_columns = measure_codes_df.iloc[0, 5:].tolist()  # Skip first 5 contract columns
        
        print(f"✓ Loaded data: {len(self.df_measure_data)} contracts, {len(self.measure_columns)} measures")
    
    def determine_part_d_threshold_set(self, contract_id: str, org_type: str) -> str:
        """
        Determine if contract uses MA-PD or PDP thresholds
        
        Returns:
            'MA-PD' or 'PDP'
        """
        contract_id = str(contract_id).strip()
        org_type = str(org_type).strip()
        
        if contract_id.startswith('S'):
            return 'PDP'
        elif contract_id.startswith('H') or contract_id.startswith('R'):
            return 'MA-PD'
        elif 'PDP' in org_type:
            return 'PDP'
        else:
            return 'MA-PD'
    
    def calculate_star_from_performance(self, measure_code: str, performance_value: float, 
                                       part_d_set: str = 'MA-PD') -> Optional[int]:
        """
        Calculate what star rating a given performance value would receive
        
        Args:
            measure_code: The measure code
            performance_value: The numeric performance value
            part_d_set: 'MA-PD' or 'PDP' for Part D measures
            
        Returns:
            Star rating (1-5) or None if cannot determine
        """
        config = get_measure_config(measure_code)
        if not config:
            return None
        
        # Try each star rating from 5 down to 1
        for star in range(5, 0, -1):
            _, lower, upper = self.get_threshold_for_measure(measure_code, star, part_d_set)
            
            if lower is None and upper is None:
                continue
            
            # Check if performance falls in this band
            in_band = True
            
            if lower is not None:
                if config.is_inverse:
                    # For inverse, lower bound uses > operator for higher stars
                    in_band = in_band and (performance_value > lower if star == 1 else performance_value >= lower)
                else:
                    # For normal, lower bound uses >= operator
                    in_band = in_band and (performance_value >= lower)
            
            if upper is not None:
                if config.is_inverse:
                    # For inverse, upper bound uses <= operator
                    in_band = in_band and (performance_value <= upper)
                else:
                    # For normal, upper bound uses < operator
                    in_band = in_band and (performance_value < upper)
            
            if in_band:
                return star
        
        return None
    
    def get_threshold_for_measure(self, measure_code: str, star_rating: int, 
                                  part_d_set: str = 'MA-PD'):
        """
        Get threshold band for a measure at given star rating
        
        Returns:
            Tuple of (formatted_string, lower_bound, upper_bound) or (None, None, None)
        """
        config = get_measure_config(measure_code)
        
        try:
            if config.part_type == 'C':
                # Part C - rows 4-8 are 1-5 stars (indices 3-7)
                row_idx = 3 + (star_rating - 1)
                # Find column index for this measure in cutpoints file
                # The cutpoints file has measure names in row 1 (index 1)
                col_idx = None
                for i, col in enumerate(self.df_cutpoints_c.iloc[1, 1:]):  # Skip first col
                    col_str = str(col).strip()
                    if config.code in col_str or config.name in col_str:
                        col_idx = 1 + i
                        break
                
                if col_idx is None:
                    return (None, None, None)
                
                threshold_str = self.df_cutpoints_c.iloc[row_idx, col_idx]
                band = parse_threshold_band(str(threshold_str))
                lower, upper, _, _ = band
                formatted = format_band_for_display(band, config.format_type)
                return (formatted, lower, upper)
                
            else:  # Part D
                # MA-PD: indices 3-7 (1-5 stars), PDP: indices 8-12 (1-5 stars)
                if part_d_set == 'MA-PD':
                    row_idx = 3 + (star_rating - 1)
                else:  # PDP
                    row_idx = 8 + (star_rating - 1)
                
                # Find column for this measure (measure names in row at index 1)
                col_idx = None
                for i, col in enumerate(self.df_cutpoints_d.iloc[1, 2:]):  # Skip first 2 cols
                    col_str = str(col).strip()
                    if config.code in col_str or config.name in col_str:
                        col_idx = 2 + i
                        break
                
                if col_idx is None or row_idx >= len(self.df_cutpoints_d):
                    return (None, None, None)
                
                threshold_str = self.df_cutpoints_d.iloc[row_idx, col_idx]
                band = parse_threshold_band(str(threshold_str))
                lower, upper, _, _ = band
                formatted = format_band_for_display(band, config.format_type)
                return (formatted, lower, upper)
                
        except Exception as e:
            # Silently handle parsing errors
            return (None, None, None)
    
    def generate_report(self, contract_id: str) -> Dict:
        """
        Generate complete performance report for a contract
        
        Returns:
            Dictionary with contract info and measure lines
        """
        # Find contract
        contract_id = str(contract_id).strip()
        
        # Get from summary ratings
        summary_row = self.df_summary[self.df_summary.iloc[:, 0].astype(str).str.strip() == contract_id]
        if summary_row.empty:
            raise ValueError(f"Contract {contract_id} not found")
        
        summary_row = summary_row.iloc[0]
        
        # Get contract info
        contract_info = {
            'contract_id': contract_id,
            'org_type': summary_row.iloc[1] if len(summary_row) > 1 else 'Unknown',
            'contract_name': summary_row.iloc[2] if len(summary_row) > 2 else 'Unknown',
            'marketing_name': summary_row.iloc[3] if len(summary_row) > 3 else 'Unknown',
            'parent_org': summary_row.iloc[4] if len(summary_row) > 4 else 'Unknown',
            'is_snp': summary_row.iloc[5] if len(summary_row) > 5 else 'Unknown',
            'part_c_rating': summary_row.iloc[8] if len(summary_row) > 8 else None,
            'part_d_rating': summary_row.iloc[9] if len(summary_row) > 9 else None,
            'overall_rating': summary_row.iloc[10] if len(summary_row) > 10 else None,
        }
        
        # Determine Part D threshold set
        part_d_set = self.determine_part_d_threshold_set(contract_id, contract_info['org_type'])
        
        # Get measure data row
        data_row = self.df_measure_data[
            self.df_measure_data.iloc[:, 0].astype(str).str.strip() == contract_id
        ]
        if data_row.empty:
            raise ValueError(f"No measure data found for {contract_id}")
        data_row = data_row.iloc[0]
        
        # Get star ratings row
        stars_row = self.df_measure_stars[
            self.df_measure_stars.iloc[:, 0].astype(str).str.strip() == contract_id
        ]
        if stars_row.empty:
            raise ValueError(f"No star ratings found for {contract_id}")
        stars_row = stars_row.iloc[0]
        
        # Process each measure
        measure_lines = []
        
        for i, measure_col_name in enumerate(self.measure_columns):
            # Get measure code from column name (e.g., "C01: Breast Cancer Screening" -> "C01")
            measure_code = measure_col_name.split(':')[0].strip() if ':' in measure_col_name else None
            
            if not measure_code or measure_code not in ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10',
                                                         'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20',
                                                         'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29', 'C30',
                                                         'C31', 'C32', 'C33', 'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07',
                                                         'D08', 'D09', 'D10', 'D11', 'D12']:
                continue
            
            try:
                config = get_measure_config(measure_code)
            except:
                continue
            
            # Get values (column index is 5 + i since first 5 are contract info)
            col_idx = 5 + i
            perf_value = data_row.iloc[col_idx] if col_idx < len(data_row) else None
            star_value = stars_row.iloc[col_idx] if col_idx < len(stars_row) else None
            
            # Parse
            is_spec = is_special_value(perf_value)
            star_rating = parse_star_rating(star_value)
            
            if is_spec:
                measure_lines.append(MeasureLine(
                    measure_code=measure_code,
                    measure_name=config.name,
                    star_rating=star_rating,  # Keep star rating even if performance is special!
                    performance_value=str(perf_value).strip(),
                    performance_numeric=None,
                    threshold_band='N/A',
                    threshold_lower=None,
                    threshold_upper=None,
                    is_special=True,
                    special_category=categorize_special_value(perf_value),
                    domain=config.domain
                ))
            else:
                # Get numeric value
                numeric_val = normalize_value(perf_value, config.format_type)
                
                # Get threshold band if we have a star rating
                threshold_band = 'N/A'
                threshold_lower = None
                threshold_upper = None
                if star_rating is not None:
                    band_result = self.get_threshold_for_measure(
                        measure_code, star_rating, part_d_set
                    )
                    threshold_band, threshold_lower, threshold_upper = band_result
                    if threshold_band is None:
                        threshold_band = 'N/A'
                
                measure_lines.append(MeasureLine(
                    measure_code=measure_code,
                    measure_name=config.name,
                    star_rating=star_rating,
                    performance_value=format_value_for_display(perf_value, config.format_type),
                    performance_numeric=numeric_val,
                    threshold_band=threshold_band,
                    threshold_lower=threshold_lower,
                    threshold_upper=threshold_upper,
                    is_special=False,
                    special_category=None,
                    domain=config.domain
                ))
        
        return {
            'contract_info': contract_info,
            'part_d_set': part_d_set,
            'measure_lines': measure_lines
        }
    
    def print_report(self, report: Dict):
        """Print formatted report to console"""
        info = report['contract_info']
        lines = report['measure_lines']
        
        print("\n" + "="*100)
        print("CONTRACT PERFORMANCE REPORT")
        print("="*100)
        print(f"Contract: {info['contract_id']} - {info['marketing_name']}")
        print(f"Parent Organization: {info['parent_org']}")
        print(f"Type: {info['org_type']} | SNP: {info['is_snp']}")
        
        # Ratings
        overall = info['overall_rating']
        part_c = info['part_c_rating']
        part_d = info['part_d_rating']
        print(f"Overall Rating: {overall}⭐ | Part C: {part_c}⭐ | Part D: {part_d}⭐")
        
        if report['part_d_set'] == 'PDP':
            print(f"Part D Thresholds: PDP (stricter)")
        else:
            print(f"Part D Thresholds: MA-PD")
        
        # Group by domain
        part_c_domains = ['HD1', 'HD2', 'HD3', 'HD4', 'HD5']
        part_d_domains = ['DD1', 'DD2', 'DD3', 'DD4']
        
        # Part C
        print("\n" + "="*100)
        print("PART C MEASURES")
        print("="*100)
        
        for domain in part_c_domains:
            domain_lines = [l for l in lines if l.domain == domain]
            if not domain_lines:
                continue
            
            print(f"\n{domain}: {DOMAIN_NAMES.get(domain, domain)}")
            print("-"*100)
            print(f"{'Measure':<50} | {'Star':<6} | {'Performance':<15} | {'Cut Point Band':<25}")
            print("-"*100)
            
            for line in domain_lines:
                star_display = f"{line.star_rating}⭐" if line.star_rating else 'N/A'
                perf_display = line.performance_value[:15] if len(line.performance_value) <= 15 else line.performance_value[:12] + '...'
                measure_display = line.measure_code + ': ' + line.measure_name
                if len(measure_display) > 50:
                    measure_display = measure_display[:47] + '...'
                
                print(f"{measure_display:<50} | {star_display:<6} | {perf_display:<15} | {line.threshold_band:<25}")
        
        # Part D
        part_d_lines = [l for l in lines if l.domain.startswith('DD')]
        if part_d_lines:
            print("\n" + "="*100)
            print("PART D MEASURES")
            print("="*100)
            
            for domain in part_d_domains:
                domain_lines = [l for l in lines if l.domain == domain]
                if not domain_lines:
                    continue
                
                print(f"\n{domain}: {DOMAIN_NAMES.get(domain, domain)}")
                print("-"*100)
                print(f"{'Measure':<50} | {'Star':<6} | {'Performance':<15} | {'Cut Point Band':<25}")
                print("-"*100)
                
                for line in domain_lines:
                    star_display = f"{line.star_rating}⭐" if line.star_rating else 'N/A'
                    perf_display = line.performance_value[:15] if len(line.performance_value) <= 15 else line.performance_value[:12] + '...'
                    measure_display = line.measure_code + ': ' + line.measure_name
                    if len(measure_display) > 50:
                        measure_display = measure_display[:47] + '...'
                    
                    print(f"{measure_display:<50} | {star_display:<6} | {perf_display:<15} | {line.threshold_band:<25}")
        
        # Summary
        print("\n" + "="*100)
        print("SUMMARY")
        print("="*100)
        
        numeric_lines = [l for l in lines if not l.is_special and l.star_rating is not None]
        if numeric_lines:
            five_star = sum(1 for l in numeric_lines if l.star_rating == 5)
            four_star = sum(1 for l in numeric_lines if l.star_rating == 4)
            three_star = sum(1 for l in numeric_lines if l.star_rating == 3)
            two_star = sum(1 for l in numeric_lines if l.star_rating == 2)
            one_star = sum(1 for l in numeric_lines if l.star_rating == 1)
            
            print(f"Measures with ratings: {len(numeric_lines)}")
            print(f"  5⭐: {five_star} measures")
            print(f"  4⭐: {four_star} measures")
            print(f"  3⭐: {three_star} measures")
            print(f"  2⭐: {two_star} measures")
            print(f"  1⭐: {one_star} measures")
        
        special_lines = [l for l in lines if l.is_special]
        if special_lines:
            print(f"\nMeasures with special status: {len(special_lines)}")
        
        print("\n" + "="*100)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python contract_report.py <CONTRACT_ID>")
        print("Example: python contract_report.py H0028")
        sys.exit(1)
    
    contract_id = sys.argv[1]
    
    try:
        generator = ContractReportGenerator()
        report = generator.generate_report(contract_id)
        generator.print_report(report)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


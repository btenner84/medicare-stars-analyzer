"""
CAI (Categorical Adjustment Index) Calculator
Maps FAC (Final Adjustment Category) to CAI values per CMS Technical Notes 2026
"""

import pandas as pd
from typing import Optional, Dict

# CAI Values from Technical Notes Tables 12, 15, 18, 21
# These are the exact values CMS uses to adjust star ratings

CAI_VALUES_OVERALL = {
    1: -0.063262,
    2: -0.040422,
    3: -0.017803,
    4: 0.003256,
    5: 0.018790,
    6: 0.045683,
    7: 0.058145,
    8: 0.101257,
    9: 0.145515
}

CAI_VALUES_PART_C = {
    1: -0.058259,
    2: -0.036927,
    3: -0.013699,
    4: 0.004022,
    5: 0.032302,
    6: 0.059788,
    7: 0.080451,
    8: 0.102370
}

CAI_VALUES_PART_D_MAPD = {
    1: -0.033144,
    2: -0.014987,
    3: -0.002688,
    4: 0.046282,
    5: 0.072332,
    6: 0.128476
}

CAI_VALUES_PART_D_PDP = {
    1: -0.028,  # Approximate - need to verify from tech notes
    2: -0.010,
    3: 0.015,
    4: 0.045
}


class CAICalculator:
    """Handles CAI data loading and adjustment calculations"""
    
    def __init__(self, cai_csv_path: str):
        """Load CAI data from CSV"""
        self.df_cai = pd.read_csv(cai_csv_path, skiprows=1)
        print(f"✓ Loaded CAI data for {len(self.df_cai)} contracts")
    
    def get_cai_for_contract(self, contract_id: str) -> Dict[str, Optional[float]]:
        """
        Get CAI values for a specific contract
        
        Returns dict with:
        - overall_fac: Overall FAC category (1-9)
        - part_c_fac: Part C FAC category (1-8)
        - part_d_mapd_fac: Part D MA-PD FAC category (1-6)
        - part_d_pdp_fac: Part D PDP FAC category (1-4)
        - overall_cai: Overall CAI value
        - part_c_cai: Part C CAI value
        - part_d_cai: Part D CAI value
        """
        contract_id = str(contract_id).strip()
        
        # Find contract in CAI data
        row = self.df_cai[self.df_cai.iloc[:, 0].astype(str).str.strip() == contract_id]
        
        if row.empty:
            return {
                'overall_fac': None,
                'part_c_fac': None,
                'part_d_mapd_fac': None,
                'part_d_pdp_fac': None,
                'overall_cai': 0,
                'part_c_cai': 0,
                'part_d_cai': 0
            }
        
        row = row.iloc[0]
        
        # Parse FAC values from CSV (columns: Part C FAC, Part D MA-PD FAC, Part D PDP FAC, Overall FAC)
        part_c_fac = self._parse_fac(row.iloc[5])  # Column index 5: Part C FAC
        part_d_mapd_fac = self._parse_fac(row.iloc[6])  # Column index 6: Part D MA-PD FAC
        part_d_pdp_fac = self._parse_fac(row.iloc[7])  # Column index 7: Part D PDP FAC
        overall_fac = self._parse_fac(row.iloc[8])  # Column index 8: Overall FAC
        
        # Map FAC to CAI values
        overall_cai = CAI_VALUES_OVERALL.get(overall_fac, 0) if overall_fac else 0
        part_c_cai = CAI_VALUES_PART_C.get(part_c_fac, 0) if part_c_fac else 0
        
        # Determine Part D CAI based on contract type
        part_d_cai = 0
        if part_d_mapd_fac:
            part_d_cai = CAI_VALUES_PART_D_MAPD.get(part_d_mapd_fac, 0)
        elif part_d_pdp_fac:
            part_d_cai = CAI_VALUES_PART_D_PDP.get(part_d_pdp_fac, 0)
        
        return {
            'overall_fac': overall_fac,
            'part_c_fac': part_c_fac,
            'part_d_mapd_fac': part_d_mapd_fac,
            'part_d_pdp_fac': part_d_pdp_fac,
            'overall_cai': overall_cai,
            'part_c_cai': part_c_cai,
            'part_d_cai': part_d_cai
        }
    
    def _parse_fac(self, value) -> Optional[int]:
        """Parse FAC value from CSV (handle N/A, etc.)"""
        if pd.isna(value):
            return None
        
        try:
            val_str = str(value).strip().upper()
            if val_str in ['N/A', 'NA', '']:
                return None
            return int(float(val_str))
        except (ValueError, TypeError):
            return None
    
    def apply_cai_to_rating(self, raw_rating: float, cai_value: float) -> float:
        """
        Apply CAI adjustment to a raw star rating
        
        Args:
            raw_rating: The unadjusted star rating
            cai_value: The CAI adjustment value
            
        Returns:
            Adjusted star rating (raw + CAI)
        """
        if raw_rating is None or cai_value is None:
            return raw_rating
        
        return raw_rating + cai_value


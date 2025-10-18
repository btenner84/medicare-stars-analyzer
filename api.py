"""
FastAPI Backend for Medicare Stars Analyzer
Reuses all existing business logic from contract_report.py
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import pandas as pd

from contract_report import ContractReportGenerator
from measure_config import get_measure_config

app = FastAPI(title="Medicare Stars API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize generator (loads data from CSV files in current directory)
generator = ContractReportGenerator()

# Mount static files FIRST (before routes)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve the main frontend"""
    return FileResponse("static/index.html")

@app.get("/api/contracts")
async def get_contracts():
    """Get list of all contracts"""
    try:
        contracts = []
        for _, row in generator.df_measure_data.iterrows():
            contract_id = str(row.iloc[0]).strip()
            org_name = str(row.iloc[1]).strip() if len(row) > 1 else ""
            marketing_name = str(row.iloc[2]).strip() if len(row) > 2 else ""
            
            # Get overall rating from summary
            summary_row = generator.df_summary[generator.df_summary.iloc[:, 0].astype(str).str.strip() == contract_id]
            overall_rating = None
            if not summary_row.empty:
                overall_val = summary_row.iloc[0, 5]
                try:
                    overall_rating = int(float(overall_val))
                except:
                    pass
            
            contracts.append({
                "id": contract_id,
                "org_name": org_name,
                "marketing_name": marketing_name,
                "overall_rating": overall_rating,
                "display": f"{contract_id} - {marketing_name}" if marketing_name else contract_id
            })
        
        return {"contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contract/{contract_id}")
async def get_contract(contract_id: str):
    """Get detailed contract performance data"""
    try:
        report = generator.generate_report(contract_id)
        
        # Format measures for frontend
        measures = []
        for line in report['measure_lines']:
            config = get_measure_config(line.measure_code)
            
            measures.append({
                "code": line.measure_code,
                "name": line.measure_name,
                "weight": int(config.weight) if config else 1,
                "is_inverse": config.is_inverse if config else False,
                "star_rating": line.star_rating,
                "performance": line.performance_value,
                "performance_numeric": line.performance_numeric,
                "threshold_band": line.threshold_band,
                "threshold_lower": line.threshold_lower,
                "threshold_upper": line.threshold_upper,
                "is_special": line.is_special,
                "domain": line.domain,
                "format_type": config.format_type if config else "PERCENTAGE"
            })
        
        return {
            "contract_info": report['contract_info'],
            "part_d_set": report['part_d_set'],
            "measures": measures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whatif")
async def calculate_whatif(data: dict):
    """Calculate what-if star rating"""
    try:
        measure_code = data.get("measure_code")
        value = data.get("value")
        contract_id = data.get("contract_id")
        
        # Get part_d_set for this contract
        report = generator.generate_report(contract_id)
        part_d_set = report['part_d_set']
        
        # Calculate new star
        new_star = generator.calculate_star_from_performance(
            measure_code, float(value), part_d_set
        )
        
        return {"star": new_star}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


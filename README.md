# Medicare Stars Analyzer

A comprehensive Medicare Advantage Stars rating analysis tool with What-If scenario modeling.

## Features

- ⭐ Contract performance analysis across all 45 measures
- 📊 Weighted average star calculations
- 🎯 Risk status indicators (At Risk / Neutral / Upside)
- 💡 What-If scenario modeling
- 🔍 Cut-point band analysis
- 📈 Star risk scoring

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + TailwindCSS + Vanilla JS
- **Data**: CSV-based (no database required)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python api.py

# Or use uvicorn
uvicorn api:app --reload --port 8000
```

Visit `http://localhost:8000`

## Project Structure

```
Stars2.0/
├── api.py                    # FastAPI backend
├── contract_report.py        # Core business logic
├── measure_config.py         # Measure definitions
├── threshold_parser.py       # Threshold parsing
├── data_parsers.py          # Data parsing utilities
├── static/
│   ├── index.html           # Frontend UI
│   └── app.js               # Frontend logic
└── *.csv                    # CMS data files
```

## Deployment

### Railway

1. Create a new project on Railway
2. Connect your GitHub repo
3. Railway will auto-detect Python and deploy
4. Add environment variable (if needed): `PORT=8000`

### Render / Heroku / DigitalOcean

Similar process - just connect your repo and deploy!

## Data Sources

- 2026 Star Ratings Data (CMS)
- Measure Stars
- Part C & D Cut Points
- Summary Ratings

## License

Proprietary

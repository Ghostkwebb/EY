# EY Fiduciary Veracity Portal

Enhanced Customer Due Diligence (ECDD) platform for Ultra-High-Net-Worth Individuals (UHNWIs). Maps Origin of Capital Matrix, performs live market plausibility calibrations, and logs deficiency registers per Wolfsberg / MAS guidelines.

## Quick Start

```bash
cd Task-1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in `Task-1/`:

```env
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here
```

### Generate Mock Data

```bash
python generate_mock.py
```

### Run

```bash
streamlit run app.py
```

## Project Structure

```
Task-1/
├── app.py                      # Main Streamlit application (UI + routing)
├── auth.py                     # Authentication (hashed credentials)
├── db.py                       # Client database (session-state backed)
├── generate_mock.py            # Generate 60-month multi-driver SOW mock data
├── generate_missing_slips.py   # Generate PDFs for documentary gaps
├── requirements.txt            # Pinned Python dependencies
├── .env                        # API keys (NOT committed to git)
└── mock_data/
    ├── client_summary.csv      # Master summary database
    ├── client_summary.xlsx     # Excel export
    ├── pdfs/                   # Generated PDF vouchers
    └── test_missing_slips/     # Gap-fill vouchers
```

## Features

- **Client Profile Summary** — Net worth, capital inflow vectors, metadata
- **Compliance Matrix** — SOW driver status tracking (Salary, Equity, Rent, Trust, Inheritance)
- **Documentary Proof Compartments** — 60-month ledger with per-slot PDF upload
- **Market Plausibility Calibration** — SerpAPI-powered salary benchmarking
- **Real Estate Yield Engine** — Multi-factor rent plausibility calculator
- **Volatility Profiling** — MoM % change with dynamic anomaly thresholds (rolling ±2σ)
- **AI Terminal** — LangChain agent for natural language data queries
- **Light/Dark Mode** — CSS variable-based theme toggle

## Auth Credentials (Dev)

| Username | Role | Notes |
|----------|------|-------|
| `carlos_krause` | RM Standard | Limited access |
| `ghostkwebb` | Dev Admin | Full system override |
| `dev_admin` | Dev Admin | Full system override |

## Tech Stack

- **Frontend:** Streamlit + Plotly + custom CSS (Swiss Neo-Brutalist)
- **LLM:** Groq (Llama 3.1) / LM Studio (local) via LangChain
- **PDF Parsing:** pdfplumber + regex + LLM fallback
- **Scraping:** SerpAPI (Google Search)
- **Data:** Pandas + CSV (session-state persistence)

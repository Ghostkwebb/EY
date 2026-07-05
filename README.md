# Client Wealth Audit Portal

Enhanced Customer Due Diligence (ECDD) platform for Ultra-High-Net-Worth Individuals (UHNWIs). Models the Origin of Capital Matrix, performs live market plausibility calibrations, and logs deficiency registers per Wolfsberg Group AML Principles and MAS compliance guidelines.

---

## 1. Quick Start

### 1.1 Local Installation
1. Navigate to the project folder and initialize a Python virtual environment:
   ```bash
   cd Task-1
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 1.2 Configuration (.env)
Create a `.env` file in `Task-1/` containing your API keys:
```env
GROQ_API_KEY="your_groq_api_key_here"
SERPAPI_KEY="your_serpapi_key_here"
```

### 1.3 Database Seeding & Launch
1. Generate mock SOW data and seed the local CSV database:
   ```bash
   python generate_mock.py
   python generate_missing_slips.py
   ```
2. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```
   The portal will automatically launch at `http://localhost:8501`.

---

## 2. Project Structure

```
Task-1/
├── app.py                      # Main Streamlit application (UI, charts, and routing)
├── auth.py                     # Hashed user credentials and authentication screens
├── db.py                       # In-memory client database and session-state mutation
├── generate_mock.py            # Generates 60-month multi-driver SOW CSV database
├── generate_missing_slips.py   # Utility script to backfill timeline PDF vouchers
├── requirements.txt            # Pinned project dependencies
├── .env                        # Local API configuration (excluded from git)
└── mock_data/
    ├── client_summary.csv      # Master CSV ledger database
    ├── client_summary.xlsx     # Compiled Excel workbook export
    ├── pdfs/                   # Active verified PDF vouchers
    └── test_missing_slips/     # Missing ledger vouchers for upload testing
```

---

## 3. Core Features

- **Client Profile Summary**: Visual dashboard display of UHNWI metadata, nationality, account history tenure, active wealth vectors, and net worth estimations.
- **SOW Compliance Matrix**: Checks document completeness (*Fully Available, Partially Available, Not Available, N/A*) across all primary income categories.
- **60-Month Documentary Ledger**: A yearly tabbed ledger grid showing verified and missing monthly/quarterly document vouchers. Uploaded PDFs are parsed and verified using a hybrid OCR/Regex and LLM engine.
- **Salary Calibration**: Segmented career historical alignment mapping of actual reported income vs. scraped market rates (Glassdoor, LinkedIn, AmbitionBox).
- **Rental Property Yield Engine**: Multi-factor rental math verification checks against property specifications (area, base rate, tier, property type, density factors) with 10% annual compound escalations.
- **Volatility Profiling**: Tracks Month-over-Month percentage changes in cash flow, flagging fluctuations exceeding standard thresholds ($\pm 2\sigma$).
- **Terminal AI chatbot**: Natural language query engine using a LangChain Pandas Agent.
- **Theme Transitions**: Dark and Light UI themes.

---

## 4. Pre-configured Credentials (Dev)

| Username | Role | Access | Notes |
|----------|------|--------|-------|
| `carlos_krause` | RM Standard | Standard | Standard Relationship Manager access |
| `ghostkwebb` | Dev Admin | Full | Admin override access |
| `dev_admin` | Dev Admin | Full | Admin override access |

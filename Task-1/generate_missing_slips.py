# generate_missing_slips.py
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Setup output folder
out_dir = "mock_data/test_missing_slips"
os.makedirs(out_dir, exist_ok=True)

# 2. Check database
csv_path = "mock_data/client_summary.csv"
if not os.path.exists(csv_path):
    print("Error: Run generate_mock.py first!")
    exit()

df = pd.read_csv(csv_path)
df['Date_Parsed'] = pd.to_datetime(df['Month_Year'], format='%b %Y', errors='coerce')

# Mapping & metadata
clients = {
    "C-1001": {"Name": "Robert Kramer", "Job_Title": "Software Engineer", "Base": 65000},
    "C-1002": {"Name": "Priya Patel", "Job_Title": "Relationship Manager", "Base": 85000},
    "C-1003": {"Name": "Vikram Biswas", "Job_Title": "Data Analyst", "Base": 50000}
}

sow_map = {
    "Executive Yield (Salary)": "Salary",
    "Corporate Equity Liquidation": "Equity",
    "Real Estate Yield (Rent)": "Rent"
}

def draw_pdf(rec, sow_type):
    """Draws custom SOW PDF voucher."""
    short_type = sow_map[sow_type]
    pdf_path = f"{out_dir}/{rec['Client_ID']}_{short_type}_{rec['Month_Year'].replace(' ', '_')}.pdf"
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, f"PROOF OF SOURCE: {sow_type.upper()}")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Client ID: {rec['Client_ID']}")
    c.drawString(50, 680, f"Name: {rec['Name']}")
    c.drawString(50, 660, f"Job Title/SOW Role: {rec['Job_Title']}")
    c.drawString(50, 640, f"Month/Year: {rec['Month_Year']}")
    c.drawString(50, 600, f"Gross Amount: INR {rec['Gross_Salary']}")
    c.drawString(50, 580, f"Tax / Fees: INR {rec['Tax']}")
    c.drawString(50, 560, f"Net Amount Received: INR {rec['Net_Salary']}")
    c.save()

# 3. Locate gaps and generate
print("Scanning database for documentary gaps...")
for cid, meta in clients.items():
    for driver, short_name in sow_map.items():
        client_sow_df = df[(df['Client_ID'] == cid) & (df['SOW_Driver'] == driver)]
        
        # Check applicability fallback
        if client_sow_df.empty:
            continue
            
        ideal_dates = pd.date_range(start='2019-01-01', end='2023-12-01', freq='MS')
        present_dates = pd.to_datetime(client_sow_df['Date_Parsed']).dt.tz_localize(None)
        missing_dates = ideal_dates.difference(present_dates)
        
        # Draw PDF vouchers for missing slots
        for m_date in missing_dates:
            month_year_str = m_date.strftime("%b %Y")
            gross = meta["Base"]
            tax = int(gross * 0.15)
            rec = {
                "Client_ID": cid,
                "Name": meta["Name"],
                "Job_Title": meta["Job_Title"],
                "Month_Year": month_year_str,
                "Gross_Salary": gross,
                "Tax": tax,
                "Net_Salary": gross - tax
            }
            draw_pdf(rec, driver)

print(f"Success! {len(os.listdir(out_dir))} missing vouchers generated in '{out_dir}/' folder.")
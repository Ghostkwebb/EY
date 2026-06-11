# generate_mock.py
import os
import random
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Setup folders
os.makedirs("mock_data/pdfs", exist_ok=True)

# 2. Client Base Configs
clients = [
    {"Client_ID": "C-1001", "Name": "Robert Kramer", "Job_Title": "Software Engineer", "Salary_Base": 65000, "Rent_Base": 40000, "Equity_Base": 120000},
    {"Client_ID": "C-1002", "Name": "Priya Patel", "Job_Title": "Relationship Manager", "Salary_Base": 85000, "Rent_Base": 0, "Equity_Base": 200000},
    {"Client_ID": "C-1003", "Name": "Vikram Seth", "Job_Title": "Data Analyst", "Salary_Base": 50000, "Rent_Base": 25000, "Equity_Base": 0}
]

start_date = datetime(2019, 1, 1)
all_records = []

# Helper to draw PDF slips based on SOW Type
def draw_pdf(rec, sow_type):
    short_map = {
        "Executive Yield (Salary)": "Salary", 
        "Corporate Equity Liquidation": "Equity",
        "Real Estate Yield (Rent)": "Rent"
    }
    short_type = short_map[sow_type]
    pdf_path = f"mock_data/pdfs/{rec['Client_ID']}_{short_type}_{rec['Month_Year'].replace(' ', '_')}.pdf"
    
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

# 3. Generate 60 Months of Multi-Driver SOW data
for client in clients:
    client_summary_records = []
    
    for i in range(60):
        current_date = start_date + relativedelta(months=i)
        month_year_str = current_date.strftime("%b %Y")
        
        # A. GENERATE EXECUTIVE COMPENSATION (SALARY) - Monthly
        sal_base = client["Salary_Base"]
        sal_val = int(sal_base * (1 + random.uniform(-0.02, 0.02)))
        if (i + 1) % 3 == 0: sal_val += int(sal_base * random.uniform(0.15, 0.30)) # Quarterly bonus
        if (i + 1) % 12 == 0: sal_val += int(sal_base * random.uniform(0.40, 0.75)) # Year-end bonus
        
        sal_tax = int(sal_val * 0.15)
        client_summary_records.append({
            "Client_ID": client["Client_ID"], "Name": client["Name"], "Job_Title": client["Job_Title"],
            "SOW_Driver": "Executive Yield (Salary)", "Date": current_date.strftime("%Y-%m-%d"),
            "Month_Year": month_year_str, "Gross_Salary": sal_val, "Tax": sal_tax, "Net_Salary": sal_val - sal_tax
        })

        # B. GENERATE REAL ESTATE YIELD (RENT) - Monthly (If applicable)
        if client["Rent_Base"] > 0:
            rent_base = client["Rent_Base"]
            # Apply 10% rent raise every 12 months
            rent_val = int(rent_base * (1.10 ** (i // 12)))
            rent_tax = int(rent_val * 0.10) # 10% property tax
            
            client_summary_records.append({
                "Client_ID": client["Client_ID"], "Name": client["Name"], "Job_Title": "Property Landlord",
                "SOW_Driver": "Real Estate Yield (Rent)", "Date": current_date.strftime("%Y-%m-%d"),
                "Month_Year": month_year_str, "Gross_Salary": rent_val, "Tax": rent_tax, "Net_Salary": rent_val - rent_tax
            })
            
        # C. GENERATE CORPORATE EQUITY LIQUIDATION - Quarterly (If applicable)
        if client["Equity_Base"] > 0 and (i + 1) % 3 == 0:
            eq_base = client["Equity_Base"]
            eq_val = int(eq_base * (1 + random.uniform(-0.10, 0.25)))
            eq_tax = int(eq_val * 0.10) # Capital gains tax
            
            client_summary_records.append({
                "Client_ID": client["Client_ID"], "Name": client["Name"], "Job_Title": "Shareholder / Director",
                "SOW_Driver": "Corporate Equity Liquidation", "Date": current_date.strftime("%Y-%m-%d"),
                "Month_Year": month_year_str, "Gross_Salary": eq_val, "Tax": eq_tax, "Net_Salary": eq_val - eq_tax
            })

    # Apply Random 10 Gaps (Missing slips) per driver category
    for driver in ["Executive Yield (Salary)", "Real Estate Yield (Rent)", "Corporate Equity Liquidation"]:
        driver_recs = [r for r in client_summary_records if r["SOW_Driver"] == driver]
        if len(driver_recs) >= 10:
            drop_indices = random.sample(range(len(driver_recs)), 10)
            for idx in sorted(drop_indices, reverse=True):
                del driver_recs[idx]
            
            # Add remaining to master list and draw PDFs
            for rec in driver_recs:
                all_records.append(rec)
                draw_pdf(rec, rec["SOW_Driver"])
        else:
            all_records.extend(driver_recs)

# Save Master Summary Database
df = pd.DataFrame(all_records)
df.to_csv("mock_data/client_summary.csv", index=False)
df.to_excel("mock_data/client_summary.xlsx", index=False)
print("HNWI Volatile Multi-Driver database successfully generated!")
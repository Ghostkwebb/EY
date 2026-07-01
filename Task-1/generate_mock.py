# generate_mock.py
import os
import random
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Setup folders and clear the entire mock_data folder to start fresh
import shutil
if os.path.exists("mock_data"):
    shutil.rmtree("mock_data")
os.makedirs("mock_data/pdfs", exist_ok=True)
os.makedirs("mock_data/test_missing_slips", exist_ok=True)

# 2. Client Base Configs
clients = [
    {"Client_ID": "C-1001", "Name": "Robert Kramer", "Job_Title": "Software Engineer", "Rent_Base": 1485120, "Equity_Base": 120000},
    {"Client_ID": "C-1002", "Name": "Priya Patel", "Job_Title": "Relationship Manager", "Rent_Base": 0, "Equity_Base": 200000},
    {"Client_ID": "C-1003", "Name": "Vikram Seth", "Job_Title": "Data Analyst", "Rent_Base": 70000, "Equity_Base": 0}
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
    short_type = short_map.get(sow_type, sow_type)
    
    salary_subtypes = ["SalaryPayslip", "TaxForm16", "BankStatement", "HRLetter"]
    if sow_type == "Executive Yield (Salary)":
        h = sum(ord(c) for c in f"{rec['Client_ID']}_{rec['Month_Year']}")
        short_type = salary_subtypes[h % len(salary_subtypes)]
        
    pdf_path = f"mock_data/pdfs/{rec['Client_ID']}_{short_type}_{rec['Month_Year'].replace(' ', '_')}.pdf"
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    if short_type == "SalaryPayslip":
        c.setFont("Helvetica-Bold", 16)
        c.drawString(120, 750, "EMPLOYEE PAYSLIP / COMPENSATIONAL VOUCHER")
        c.setFont("Helvetica", 11)
        c.drawString(50, 700, f"Client ID: {rec['Client_ID']}")
        c.drawString(50, 680, f"Employee Name: {rec['Name']}")
        c.drawString(50, 660, f"Designation: {rec['Job_Title']}")
        c.drawString(50, 640, f"Pay Period: {rec['Month_Year']}")
        c.drawString(50, 600, f"Gross Earnings: INR {rec['Gross_Salary']:,}")
        c.drawString(50, 580, f"Tax Deducted: INR {rec['Tax']:,}")
        c.drawString(50, 560, f"Net Disbursed: INR {rec['Net_Salary']:,}")
    elif short_type == "TaxForm16":
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "GOVERNMENT OF INDIA - INCOME TAX DEPARTMENT")
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120, 730, "FORM 16: CERTIFICATE OF TAX DEDUCTED AT SOURCE")
        c.setFont("Helvetica", 11)
        c.drawString(50, 680, f"Taxpayer ID Reference: {rec['Client_ID']}")
        c.drawString(50, 660, f"Taxpayer Name: {rec['Name']}")
        c.drawString(50, 640, f"Employer Designation: {rec['Job_Title']}")
        c.drawString(50, 620, f"Assessment Period: {rec['Month_Year']}")
        c.drawString(50, 580, f"Gross Certified Compensation: INR {rec['Gross_Salary']:,}")
        c.drawString(50, 560, f"Total Tax Deducted: INR {rec['Tax']:,}")
        c.drawString(50, 540, f"Net Income Paid: INR {rec['Net_Salary']:,}")
    elif short_type == "BankStatement":
        c.setFont("Helvetica-Bold", 16)
        c.drawString(140, 750, "SWISS METROPOLITAN BANK - CREDIT ADVICE")
        c.setFont("Helvetica", 11)
        c.drawString(50, 680, f"Account Holder Name: {rec['Name']}")
        c.drawString(50, 660, f"Client ID Reference: {rec['Client_ID']}")
        c.drawString(50, 640, f"Transaction Description: ACH CREDIT - SALARY DEPOSIT")
        c.drawString(50, 620, f"Value Date / Period: {rec['Month_Year']}")
        c.drawString(50, 580, f"Gross Transaction Amount: INR {rec['Gross_Salary']:,}")
        c.drawString(50, 560, f"Tax Withheld: INR {rec['Tax']:,}")
        c.drawString(50, 540, f"Net Deposited Amount: INR {rec['Net_Salary']:,}")
    elif short_type == "HRLetter":
        c.setFont("Helvetica-Bold", 15)
        c.drawString(100, 750, "EMPLOYMENT & REMUNERATION VERIFICATION LETTER")
        c.setFont("Helvetica", 11)
        c.drawString(50, 700, "To Whom It May Concern,")
        c.drawString(50, 680, f"This letter certifies that {rec['Name']} (ID: {rec['Client_ID']})")
        c.drawString(50, 660, f"is employed as {rec['Job_Title']}.")
        c.drawString(50, 640, f"For the auditing period of {rec['Month_Year']}, the compensation structure is:")
        c.drawString(50, 600, f"Gross Monthly Salary: INR {rec['Gross_Salary']:,}")
        c.drawString(50, 580, f"Tax Withholding: INR {rec['Tax']:,}")
        c.drawString(50, 560, f"Net Compensation Disbursed: INR {rec['Net_Salary']:,}")
    else:
        # Corporate Equity or Rent SOW
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 750, f"PROOF OF SOURCE: {sow_type.upper()}")
        c.setFont("Helvetica", 12)
        c.drawString(50, 700, f"Client ID: {rec['Client_ID']}")
        c.drawString(50, 680, f"Name: {rec['Name']}")
        c.drawString(50, 660, f"Job Title/SOW Role: {rec['Job_Title']}")
        c.drawString(50, 640, f"Month/Year: {rec['Month_Year']}")
        c.drawString(50, 600, f"Gross Amount: INR {rec['Gross_Salary']:,}")
        c.drawString(50, 580, f"Tax / Fees: INR {rec['Tax']:,}")
        c.drawString(50, 560, f"Net Amount Received: INR {rec['Net_Salary']:,}")

    # Standardized compliance metadata block at the bottom
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 150, "--- FIDUCIARY COMPLIANCE METADATA ---")
    c.setFont("Helvetica", 10)
    c.drawString(50, 130, f"Client ID: {rec['Client_ID']}")
    c.drawString(50, 110, f"Name: {rec['Name']}")
    c.drawString(50, 90, f"Job Title/SOW Role: {rec['Job_Title']}")
    c.drawString(50, 70, f"Month/Year: {rec['Month_Year']}")
    c.drawString(50, 50, f"Gross Amount: INR {rec['Gross_Salary']:,}")
    c.drawString(50, 30, f"Tax / Fees: INR {rec['Tax']:,}")
    c.drawString(50, 10, f"Net Amount Received: INR {rec['Net_Salary']:,}")
    
    c.save()

# 3. Generate 60 Months of Multi-Driver SOW data
for client in clients:
    client_summary_records = []
    
    for i in range(60):
        current_date = start_date + relativedelta(months=i)
        month_year_str = current_date.strftime("%b %Y")
        
        # A. GENERATE EXECUTIVE COMPENSATION (SALARY) - Monthly
        # Dynamically map correct high-value benchmark salary bases
        sal_base = 100000
        job_role = client["Job_Title"]
        if client["Client_ID"] == "C-1001":
            if current_date < datetime(2021, 7, 1):
                sal_base = 250000  # Google SE
                job_role = "Software Engineer"
            else:
                sal_base = 280000  # Microsoft SE
                job_role = "Software Engineer"
        elif client["Client_ID"] == "C-1002":
            if current_date < datetime(2021, 1, 1):
                sal_base = 130000  # EY RM
                job_role = "Relationship Manager"
            else:
                sal_base = 160000  # Meta RM
                job_role = "Relationship Manager"
        elif client["Client_ID"] == "C-1003":
            if current_date < datetime(2022, 1, 1):
                sal_base = 150000  # Amazon DA
                job_role = "Data Analyst"
            else:
                sal_base = 180000  # McKinsey DA
                job_role = "Data Analyst"

        sal_val = int(sal_base * (1 + random.uniform(-0.02, 0.02)))
        if (i + 1) % 3 == 0: sal_val += int(sal_base * random.uniform(0.15, 0.30)) # Quarterly bonus
        if (i + 1) % 12 == 0: sal_val += int(sal_base * random.uniform(0.40, 0.75)) # Year-end bonus
        
        sal_tax = int(sal_val * 0.15)
        client_summary_records.append({
            "Client_ID": client["Client_ID"], "Name": client["Name"], "Job_Title": job_role,
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

    # Apply Random Gaps (Missing slips) per driver category (10 for Salary/Rent, only 2 for Equity)
    for driver in ["Executive Yield (Salary)", "Real Estate Yield (Rent)", "Corporate Equity Liquidation"]:
        driver_recs = [r for r in client_summary_records if r["SOW_Driver"] == driver]
        drop_count = 2 if driver == "Corporate Equity Liquidation" else 10
        if len(driver_recs) >= drop_count:
            drop_indices = random.sample(range(len(driver_recs)), drop_count)
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
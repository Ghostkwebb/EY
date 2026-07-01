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
    "C-1001": {"Name": "Robert Kramer", "Job_Title": "Software Engineer"},
    "C-1002": {"Name": "Priya Patel", "Job_Title": "Relationship Manager"},
    "C-1003": {"Name": "Vikram Seth", "Job_Title": "Data Analyst"}
}

sow_map = {
    "Executive Yield (Salary)": "Salary",
    "Corporate Equity Liquidation": "Equity",
    "Real Estate Yield (Rent)": "Rent"
}

def get_dynamic_base(client_id, date_obj, sow_driver):
    if sow_driver == "Executive Yield (Salary)":
        if client_id == "C-1001":
            return 250000 if date_obj < datetime(2021, 7, 1) else 280000
        elif client_id == "C-1002":
            return 130000 if date_obj < datetime(2021, 1, 1) else 160000
        elif client_id == "C-1003":
            return 150000 if date_obj < datetime(2022, 1, 1) else 180000
    elif sow_driver == "Real Estate Yield (Rent)":
        if client_id == "C-1001":
            months_elapsed = (date_obj.year - 2019) * 12 + (date_obj.month - 1)
            year_idx = months_elapsed // 12
            return int(1485120 * (1.10 ** year_idx))
        elif client_id == "C-1003":
            months_elapsed = (date_obj.year - 2019) * 12 + (date_obj.month - 1)
            year_idx = months_elapsed // 12
            return int(70000 * (1.10 ** year_idx))
    elif sow_driver == "Corporate Equity Liquidation":
        if client_id == "C-1001":
            return 120000
        elif client_id == "C-1002":
            return 200000
    return 100000

def draw_pdf(rec, sow_type):
    """Draws custom SOW PDF voucher."""
    short_type = sow_map.get(sow_type, sow_type)
    
    salary_subtypes = ["SalaryPayslip", "TaxForm16", "BankStatement", "HRLetter"]
    if sow_type == "Executive Yield (Salary)":
        h = sum(ord(c) for c in f"{rec['Client_ID']}_{rec['Month_Year']}")
        short_type = salary_subtypes[h % len(salary_subtypes)]
        
    pdf_path = f"{out_dir}/{rec['Client_ID']}_{short_type}_{rec['Month_Year'].replace(' ', '_')}.pdf"
    
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
            gross = get_dynamic_base(cid, m_date, driver)
            tax = int(gross * 0.15) if driver == "Executive Yield (Salary)" else (int(gross * 0.10) if driver == "Real Estate Yield (Rent)" else int(gross * 0.10))
            
            # Determine job role for document
            job_role = meta["Job_Title"]
            if driver == "Executive Yield (Salary)":
                if cid == "C-1001":
                    job_role = "Software Engineer"
                elif cid == "C-1002":
                    job_role = "Relationship Manager"
                elif cid == "C-1003":
                    job_role = "Data Analyst"
            elif driver == "Real Estate Yield (Rent)":
                job_role = "Property Landlord"
            elif driver == "Corporate Equity Liquidation":
                job_role = "Shareholder / Director"
                
            rec = {
                "Client_ID": cid,
                "Name": meta["Name"],
                "Job_Title": job_role,
                "Month_Year": month_year_str,
                "Gross_Salary": gross,
                "Tax": tax,
                "Net_Salary": gross - tax
            }
            draw_pdf(rec, driver)

print(f"Success! {len(os.listdir(out_dir))} missing vouchers generated in '{out_dir}/' folder.")
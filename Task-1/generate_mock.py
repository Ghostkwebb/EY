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

# 2. Benchmark DB
benchmark_data = [
    {"Job_Title": "Software Engineer", "Experience_Years": 3, "Min_Salary": 60000, "Max_Salary": 90000},
    {"Job_Title": "Data Analyst", "Experience_Years": 2, "Min_Salary": 50000, "Max_Salary": 80000},
    {"Job_Title": "Relationship Manager", "Experience_Years": 5, "Min_Salary": 70000, "Max_Salary": 120000}
]
pd.DataFrame(benchmark_data).to_csv("mock_data/benchmark.csv", index=False)

# 3. Client Config
clients = [
    {"Client_ID": "C-1001", "Name": "Rohan S.", "Job_Title": "Software Engineer", "Base_Salary": 65000},
    {"Client_ID": "C-1002", "Name": "Priya P.", "Job_Title": "Relationship Manager", "Base_Salary": 85000},
    {"Client_ID": "C-1003", "Name": "Vikram B.", "Job_Title": "Data Analyst", "Base_Salary": 50000} # NEW FRAUD CLIENT
]

start_date = datetime(2019, 1, 1)
all_records = []

# 4. Generate 60 months data with HNWI Volatile Patterns (No staircase, spiky bonuses, no fraud logic)
for client in clients:
    base_salary = client["Base_Salary"]
    client_records = []
    
    for i in range(60):
        current_date = start_date + relativedelta(months=i)
        
        # Base salary with ±2% minor monthly variation
        import random
        current_salary = int(base_salary * (1 + random.uniform(-0.02, 0.02)))
        
        # Quarterly Performance Payout (Every 3 months, spike of +15% to +30%)
        if (i + 1) % 3 == 0:
            current_salary += int(base_salary * random.uniform(0.15, 0.30))
            
        # Annual Stock Vest / Year-end Bonus (Every 12 months, massive spike of +40% to +75%)
        if (i + 1) % 12 == 0:
            current_salary += int(base_salary * random.uniform(0.40, 0.75))
            
        tax = int(current_salary * 0.15)
        net = current_salary - tax
        
        client_records.append({
            "Client_ID": client["Client_ID"],
            "Name": client["Name"],
            "Job_Title": client["Job_Title"],
            "Date": current_date.strftime("%Y-%m-%d"),
            "Month_Year": current_date.strftime("%b %Y"),
            "Gross_Salary": current_salary,
            "Tax": tax,
            "Net_Salary": net
        })
        
    # Random drop 10 slips (leave gaps)
    drop_indices = random.sample(range(60), 10)
    for idx in sorted(drop_indices, reverse=True):
        del client_records[idx]
        
    all_records.extend(client_records)

# 5. Draw PDF slips
for rec in all_records:
    pdf_path = f"mock_data/pdfs/{rec['Client_ID']}_{rec['Month_Year'].replace(' ', '_')}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "SALARY SLIP")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Client ID: {rec['Client_ID']}")
    c.drawString(50, 680, f"Name: {rec['Name']}")
    c.drawString(50, 660, f"Job Title: {rec['Job_Title']}")
    c.drawString(50, 640, f"Month/Year: {rec['Month_Year']}")
    c.drawString(50, 600, f"Gross Salary: INR {rec['Gross_Salary']}")
    c.drawString(50, 580, f"Tax: INR {rec['Tax']}")
    c.drawString(50, 560, f"Net Salary: INR {rec['Net_Salary']}")
    
    c.save()

# 6. Save sumary sheets
df = pd.DataFrame(all_records)
df.to_csv("mock_data/client_summary.csv", index=False)
df.to_excel("mock_data/client_summary.xlsx", index=False)
print("Mock data done!")
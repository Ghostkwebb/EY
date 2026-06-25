# db.py
import os
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent

SOW_CATEGORIES = [
    "Executive Yield (Salary)",
    "Corporate Equity Liquidation",
    "Real Estate Yield (Rent)",
    "Venture Fund Divestments",
    "Inheritance & Trust Payouts"
]

def scan_preloaded_pdfs():
    """Scans mock_data/pdfs and groups files dynamically by Client ID and SOW Category."""
    pdf_dir = BASE_DIR / "mock_data" / "pdfs"
    sow_map = {
        "salary": "Executive Yield (Salary)",
        "equity": "Corporate Equity Liquidation",
        "rent": "Real Estate Yield (Rent)"
    }
    db_slips = {
        "C-1001": {k: [] for k in SOW_CATEGORIES},
        "C-1002": {k: [] for k in SOW_CATEGORIES},
        "C-1003": {k: [] for k in SOW_CATEGORIES}
    }
    if os.path.exists(pdf_dir):
        for f in os.listdir(pdf_dir):
            if f.endswith(".pdf"):
                parts = f.split("_")
                if len(parts) >= 2:
                    cid = parts[0]
                    type_key = parts[1].lower()
                    if cid in db_slips and type_key in sow_map:
                        db_slips[cid][sow_map[type_key]].append(f)
    return db_slips

def init_db():
    if "client_db" not in st.session_state:
        preloaded = scan_preloaded_pdfs()
        st.session_state.client_db = {
            "C-1001": {
                "Client_ID": "C-1001",
                "Name": "Robert Kramer",
                "Net_Worth": "$316,500,000 USD",
                "Nationality": "United States",
                "Relationship_Since": "16 Nov 2002",
                "Region": "North America",
                "Sub_Region": "United States",
                "Account_Number": "12345",
                "RM_Name": "Carlos Krause",
                "Industry": "Pharmaceutics",
                "Country": "US",
                "Career_Segments": [
                    {"Company": "Google", "Job_Title": "Software Engineer", "Start_Month": "Jan", "Start_Year": 2019, "End_Month": "Jun", "End_Year": 2021},
                    {"Company": "Microsoft", "Job_Title": "Software Engineer", "Start_Month": "Jul", "Start_Year": 2021, "End_Month": "Dec", "End_Year": 2023}
                ],
                "Properties": [
                    {
                        "Name": "Kramer Tech Plaza (Bangalore)",
                        "Area": 8000,
                        "Base_Rate": 85,
                        "Location_Tier": "Tier 1 Metro (Bangalore)",
                        "Property_Type": "Prime Commercial Space",
                        "Demand_Factor": "High (Tech Park / SEZ)"
                    }
                ],
                "SOW_Drivers": {
                    "Executive Yield (Salary)": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1001"]["Executive Yield (Salary)"] else "Not Available", "Slips": preloaded["C-1001"]["Executive Yield (Salary)"]},
                    "Corporate Equity Liquidation": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1001"]["Corporate Equity Liquidation"] else "Not Available", "Slips": preloaded["C-1001"]["Corporate Equity Liquidation"]},
                    "Real Estate Yield (Rent)": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1001"]["Real Estate Yield (Rent)"] else "Not Available", "Slips": preloaded["C-1001"]["Real Estate Yield (Rent)"]},
                    "Venture Fund Divestments": {"Applicable": True, "Status": "Partially Available", "Slips": ["US_Bond_Holdings.pdf"]},
                    "Inheritance & Trust Payouts": {"Applicable": True, "Status": "Not Available", "Slips": []}
                }
            },
            "C-1002": {
                "Client_ID": "C-1002",
                "Name": "Priya Patel",
                "Net_Worth": "$150,000,000 USD",
                "Nationality": "India",
                "Relationship_Since": "04 May 2011",
                "Region": "Asia",
                "Sub_Region": "India",
                "Account_Number": "67890",
                "RM_Name": "Carlos Krause",
                "Industry": "Technology",
                "Country": "IN",
                "Career_Segments": [
                    {"Company": "EY", "Job_Title": "Relationship Manager", "Start_Month": "Jan", "Start_Year": 2019, "End_Month": "Dec", "End_Year": 2020},
                    {"Company": "Meta", "Job_Title": "Relationship Manager", "Start_Month": "Jan", "Start_Year": 2021, "End_Month": "Dec", "End_Year": 2023}
                ],
                "Properties": [
                    {
                        "Name": "Patel Tech Tower (Mumbai)",
                        "Area": 5000,
                        "Base_Rate": 90,
                        "Location_Tier": "Tier 1 Metro (Mumbai)",
                        "Property_Type": "Tech Park / SEZ Office Space",
                        "Demand_Factor": "High Density / High Demand"
                    }
                ],
                "SOW_Drivers": {
                    "Executive Yield (Salary)": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1002"]["Executive Yield (Salary)"] else "Not Available", "Slips": preloaded["C-1002"]["Executive Yield (Salary)"]},
                    "Corporate Equity Liquidation": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1002"]["Corporate Equity Liquidation"] else "Not Available", "Slips": preloaded["C-1002"]["Corporate Equity Liquidation"]},
                    "Real Estate Yield (Rent)": {"Applicable": False, "Status": "NA", "Slips": []},
                    "Venture Fund Divestments": {"Applicable": True, "Status": "Not Available", "Slips": []},
                    "Inheritance & Trust Payouts": {"Applicable": True, "Status": "Not Available", "Slips": []}
                }
            },
            "C-1003": {
                "Client_ID": "C-1003",
                "Name": "Vikram Seth",
                "Net_Worth": "$75,000,000 USD",
                "Nationality": "India",
                "Relationship_Since": "12 Aug 2018",
                "Region": "Asia",
                "Sub_Region": "India",
                "Account_Number": "11223",
                "RM_Name": "Carlos Krause",
                "Industry": "Data Analytics",
                "Country": "IN",
                "Career_Segments": [
                    {"Company": "Amazon", "Job_Title": "Data Analyst", "Start_Month": "Jan", "Start_Year": 2019, "End_Month": "Dec", "End_Year": 2021},
                    {"Company": "McKinsey", "Job_Title": "Data Analyst", "Start_Month": "Jan", "Start_Year": 2022, "End_Month": "Dec", "End_Year": 2023}
                ],
                "Properties": [
                    {
                        "Name": "Seth Residency (Pune)",
                        "Area": 2500,
                        "Base_Rate": 35,
                        "Location_Tier": "Tier 2 City (Pune)",
                        "Property_Type": "Suburban Residential Space",
                        "Demand_Factor": "Medium Density / Stable Demand"
                    }
                ],
                "SOW_Drivers": {
                    "Executive Yield (Salary)": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1003"]["Executive Yield (Salary)"] else "Not Available", "Slips": preloaded["C-1003"]["Executive Yield (Salary)"]},
                    "Corporate Equity Liquidation": {"Applicable": False, "Status": "NA", "Slips": []},
                    "Real Estate Yield (Rent)": {"Applicable": True, "Status": "Partially Available" if preloaded["C-1003"]["Real Estate Yield (Rent)"] else "Not Available", "Slips": preloaded["C-1003"]["Real Estate Yield (Rent)"]},
                    "Venture Fund Divestments": {"Applicable": True, "Status": "Not Available", "Slips": []},
                    "Inheritance & Trust Payouts": {"Applicable": True, "Status": "Not Available", "Slips": []}
                }
            }
        }

def get_client(query):
    init_db()
    db = st.session_state.client_db
    query_clean = str(query).strip().lower()
    for cid, data in db.items():
        if query_clean == cid.lower() or query_clean in data["Name"].lower():
            return data
    return None

def add_document_to_sow(client_id, category, filename):
    init_db()
    db = st.session_state.client_db
    if client_id in db and category in db[client_id]["SOW_Drivers"]:
        driver = db[client_id]["SOW_Drivers"][category]
        if filename not in driver["Slips"]:
            driver["Slips"].append(filename)
            if driver["Status"] == "Not Available":
                driver["Status"] = "Partially Available"
            st.session_state.client_db = db
            return True
    return False

def update_sow_applicability(client_id, category, is_applicable):
    init_db()
    db = st.session_state.client_db
    if client_id in db and category in db[client_id]["SOW_Drivers"]:
        driver = db[client_id]["SOW_Drivers"][category]
        driver["Applicable"] = is_applicable
        driver["Status"] = "Partially Available" if is_applicable and driver["Slips"] else ("Not Available" if is_applicable else "NA")
        st.session_state.client_db = db
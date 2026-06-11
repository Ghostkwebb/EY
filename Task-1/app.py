# app.py
import streamlit as st
import pandas as pd
import pdfplumber
import re
import plotly.express as px
import os
import db  
import auth
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from serpapi import GoogleSearch

# --- SETUP ---
load_dotenv()
st.set_page_config(page_title="Origin of Capital Portal", layout="wide")
db.init_db()  
auth.check_auth()

# --- DYNAMIC CONFIG BASED ON AUTH & SESSION STATE ---
if "dev_llm" not in st.session_state:
    st.session_state.dev_llm = "Groq (Cloud)"

is_dev = st.session_state.get("is_dev", False)

# If developer is logged in (ghostkwebb), use their toggled engine. Otherwise, default silently to Groq.
llm_choice = st.session_state.dev_llm if is_dev else "Groq (Cloud)"
api_key = os.getenv("GROQ_API_KEY") if llm_choice == "Groq (Cloud)" else "lm-studio"

class SalaryData(BaseModel):
    Client_ID: str = Field(description="Unique client identifier")
    Name: str = Field(description="Employee name")
    Job_Title: str = Field(description="Job title")
    Month_Year: str = Field(description="Month and year")
    Gross_Salary: float = Field(description="Gross salary amount")

@st.cache_data 
def fetch_real_benchmark(job_title, serp_key, llm_choice, groq_key):
    """Scrapes Google for real benchmark salary data with LLM extraction."""
    fallbacks = {"Software Engineer": 75000, "Relationship Manager": 95000, "Data Analyst": 60000}
    if not serp_key: return fallbacks.get(job_title, 50000), "No SerpAPI key. Using fallback."
    
    params = {"q": f"average salary for {job_title} in India Glassdoor AmbitionBox", "hl": "en", "gl": "in", "api_key": serp_key}
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        snippets = " ".join([res.get("snippet", "") for res in results.get("organic_results", [])[:3]])
        
        if not snippets: return fallbacks.get(job_title, 50000), "No Google results."
        
        yearly_val = 0
        lakh_match = re.search(r'(?:₹|Rs\.?)?\s*([\d\.]+)\s*(?:Lakhs?|LPA)', snippets, re.IGNORECASE)
        
        if lakh_match:
            yearly_val = int(float(lakh_match.group(1)) * 100000)
        else:
            if llm_choice == "Groq (Cloud)": llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=groq_key, temperature=0)
            else: llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="local-model", temperature=0)
                
            prompt = f"Snippets: '{snippets}'. Extract the average YEARLY salary. Return ONLY the raw integer. If it says '6 Lakhs', output 600000."
            ans = llm.invoke(prompt).content
            
            match = re.search(r'\d+', ans.replace(',', ''))
            if match: yearly_val = int(match.group())

        if yearly_val > 0:
            monthly_base = yearly_val // 12
            adjusted_val = int(monthly_base * 1.8) # 1.8x EY Premium Multiplier
        else:
            adjusted_val = fallbacks.get(job_title, 50000)
            
        if adjusted_val < 30000 or adjusted_val > 500000: 
            return fallbacks.get(job_title, 50000), f"Safe Fallback used. Extracted weird value: {yearly_val}/yr."
            
        return adjusted_val, f"Scraped Google -> {snippets[:100]}..."
    except Exception as e:
        return fallbacks.get(job_title, 50000), f"Error: {e}"

def parse_pdf(file, llm_choice, api_key):
    """Parses PDF slips using Hybrid OCR/regex parser."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages: text += (page.extract_text() or "") + "\n"
    try:
        return {
            "Client_ID": re.search(r"Client ID:\s*(.+)", text).group(1).strip(), 
            "Name": re.search(r"Name:\s*(.+)", text).group(1).strip(), 
            "Job_Title": re.search(r"Job Title:\s*(.+)", text).group(1).strip(), 
            "Month_Year": re.search(r"Month/Year:\s*(.+)", text).group(1).strip(), 
            "Gross_Salary": float(re.search(r"Gross Salary:\s*INR\s*(\d+)", text).group(1))
        }
    except AttributeError:
        if llm_choice == "Groq (Cloud)": llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key, temperature=0)
        else: llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="local-model", temperature=0)
        try: return llm.with_structured_output(SalaryData).invoke(f"Extract details.\n\nText: {text}").model_dump()
        except Exception: return None

# --- STARK SWISS NEO-BRUTALIST STYLING ---
st.markdown("""
<style>
    /* Global Swiss Base Reset */
    div[data-testid="stChatMessage"] { background-color: #121214 !important; border: 2px solid #333 !important; padding: 10px !important; margin-bottom: 10px !important; }
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
    .stApp, .main, .stAppViewContainer { background-color: #080808 !important; font-family: 'Courier New', monospace !important; }
    h1, h2, h3, h4, p, span, label, div, li, summary, input { color: #FFFFFF !important; }
    
    /* Clean Swiss Typography - CENTERED & BLUE ACCENT */
    h1 { 
        text-align: center !important; 
        font-family: 'Helvetica Neue', Arial, sans-serif !important; 
        font-weight: 900 !important; 
        text-transform: uppercase; 
        border-bottom: 5px solid #1E60FF !important; /* Swiss Electric Blue bottom line */
        padding-bottom: 15px !important; 
        margin-bottom: 40px !important; 
    }
    h2, h3 { font-family: 'Helvetica Neue', Arial, sans-serif !important; font-weight: 800 !important; text-transform: uppercase; }

    /* Client Profile Card - Electric Blue top border */
    .profile-card {
        background-color: #121318 !important; /* Deep slate blue/charcoal tint */
        border: 1px solid #2d2d30 !important;
        border-top: 4px solid #1E60FF !important; /* Blue top border */
        padding: 24px !important;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 5px 5px 0px #000000;
    }
    .profile-meta-item {
        border-bottom: 1px solid #2d2d30;
        padding: 8px 0;
        display: flex;
        justify-content: space-between;
    }
    .profile-meta-item b { color: #8a8a8f; }

    /* High Visibility Search Box - Electric Blue & Cyan Shadow */
    div[data-baseweb="select"] > div {
        background-color: #16171d !important;
        border: 2px solid #1E60FF !important; /* Blue Border */
        box-shadow: 4px 4px 0px #00D2FF !important; /* Cyan drop shadow */
        border-radius: 0px !important;
        height: 50px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }

    /* Minimalist Outline Badges */
    .badge-fully { border: 1px solid #00FFCC; color: #00FFCC !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-partially { border: 1px solid #1E60FF; color: #1E60FF !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-not { border: 1px solid #FF003C; color: #FF003C !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-na { border: 1px solid #555555; color: #8a8a8f !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }

    /* Streamlit components */
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary, div[data-baseweb="input"] > div, [data-testid="stChatInput"] {
        background-color: #121214 !important; border: 1px solid #2d2d30 !important; border-radius: 0px !important;
    }
    [data-testid="stExpander"] { border: 1px solid #2d2d30 !important; border-radius: 0px !important; }
    
    /* Swiss Stark White Buttons with Cyan Shadow */
    .stButton>button, .stDownloadButton>button { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #FFFFFF !important; 
        box-shadow: 4px 4px 0px #00D2FF !important; 
        border-radius: 0px !important; 
        font-weight: 900 !important; 
        text-transform: uppercase;
        font-size: 14px !important;
        transition: all 0.1s ease;
    }
    /* Force all text elements inside button to be black */
    .stButton>button *, .stDownloadButton>button * {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #00D2FF !important; 
        border-color: #00D2FF !important;
        box-shadow: 0px 0px 0px #00D2FF !important;
    }
    /* Force text inside button to stay black on hover */
    .stButton>button:hover *, .stDownloadButton>button:hover * {
        color: #000000 !important;
    }
    .stButton>button:active { transform: translate(4px, 4px); }

    /* Visual Tabs - Centered blue accents */
    button[role="tab"] { 
        background-color: #1E1E1E !important; 
        border: 2px solid #555555 !important; 
        border-bottom: 2px solid #FFFFFF !important; 
        border-radius: 10px 10px 0px 0px !important; 
        margin-right: 5px !important; 
        padding: 10px 25px !important;
        transition: all 0.3s;
    }
    button[role="tab"] * { color: #888888 !important; font-weight: bold !important; }
    button[role="tab"]:hover { background-color: #333333 !important; }
    button[role="tab"]:hover * { color: #FFFFFF !important; }
    
    button[role="tab"][aria-selected="true"] { 
        background-color: #1E60FF !important; 
        border: 4px solid #FFFFFF !important; 
        border-bottom: 4px solid #1E60FF !important; 
        transform: translateY(4px); 
        z-index: 10;
    }
    button[role="tab"][aria-selected="true"] * { color: #FFFFFF !important; font-weight: 900 !important; }
    
    /* Content box under tabs */
    div[data-testid="stTabs"] { 
        border-top: 4px solid #FFFFFF !important; 
        margin-top: -4px; 
        padding-top: 20px; 
    }

    /* Popover Floating Chat - Blue Theme */
    div[data-testid="stPopover"] { position: fixed !important; bottom: 30px !important; right: 30px !important; z-index: 99999 !important; width: fit-content !important; }
    div[data-testid="stPopover"] > button { 
        background-color: #0A0A0A !important; color: #00D2FF !important; border: 2px solid #00D2FF !important; border-radius: 50px !important; padding: 10px 25px !important; font-size: 16px !important; box-shadow: 0px 0px 15px rgba(0, 210, 255, 0.3) !important;
    }
    div[data-testid="stPopoverBody"] { background-color: #0A0A0A !important; border: 4px solid #00D2FF !important; box-shadow: 8px 8px 0px rgba(0, 210, 255, 0.5) !important; border-radius: 0px !important; width: 380px !important; }
    div[data-testid="stChatInput"] { border: 2px solid #333 !important; border-radius: 0px !important; }
    div[data-testid="stChatMessage"] { background-color: #121214 !important; border: 1px solid #2d2d30 !important; }
    
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- UI START ---
st.title("EY: FIDUCIARY VERACITY PORTAL")

# 1. Autocomplete Search Bar Layout
all_client_options = {
    "Robert Kramer (C-1001)": "C-1001",
    "Priya Patel (C-1002)": "C-1002",
    "Vikram Seth (C-1003)": "C-1003"
}

st.write("### 🔍 TARGET LOOKUP")
search_selection = st.selectbox(
    "SEARCH CLIENT NAME OR ID:", 
    options=["Select Client..."] + list(all_client_options.keys()), 
    label_visibility="collapsed",
    key="autocomplete_search"
)
st.write("") # Whitespace padding

# Manage state routing
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "summary"
if "selected_sow" not in st.session_state:
    st.session_state.selected_sow = "Executive Yield (Salary)" 

if search_selection != "Select Client...":
    target_id = all_client_options[search_selection]
    st.session_state.active_client = db.get_client(target_id)
else:
    st.session_state.active_client = None
    st.session_state.view_mode = "summary"

# Get active client data
client = st.session_state.get("active_client")

# --- MULTI-PAGE ENGINE ROUTER ---
if client:
    # --- HOMEPAGE VIEW (Summary Mode) ---
    if st.session_state.view_mode == "summary":
        st.write("---")
        st.header(f"CAPITAL GENESIS SUMMARY: {client['Name']}")
        
        col_meta, col_summary = st.columns(2)
        with col_meta:
            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-meta-item"><b>Client Nationality:</b> <span>{client['Nationality']}</span></div>
                <div class="profile-meta-item"><b>Relationship Since:</b> <span>{client['Relationship_Since']}</span></div>
                <div class="profile-meta-item"><b>Region:</b> <span>{client['Region']}</span></div>
                <div class="profile-meta-item"><b>Sub-Region:</b> <span>{client['Sub_Region']}</span></div>
                <div class="profile-meta-item"><b>Account Number:</b> <span>{client['Account_Number']}</span></div>
                <div class="profile-meta-item"><b>RM Name:</b> <span>{client['RM_Name']}</span></div>
                <div class="profile-meta-item"><b>Main Inception Industry:</b> <span>{client['Industry']}</span></div>
                <div class="profile-meta-item"><b>Main SOW Country:</b> <span>{client['Country']}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_summary:
            active_drivers = [k for k, v in client["SOW_Drivers"].items() if v["Applicable"]]
            drivers_li = "".join(f"<li style='margin-bottom:6px;'>{d}</li>" for d in active_drivers)
            st.markdown(f"""
            <div class="profile-card">
                <div>
                    <h4 style="color:#8a8a8f; margin:0; padding:0; text-transform:uppercase; font-size:14px;">Estimated Net Worth</h4>
                    <h1 style="border-bottom:none; color:#FFDF00 !important; font-size:36px; margin:8px 0 24px 0;">{client['Net_Worth']}</h1>
                </div>
                <div>
                    <p style="font-weight:bold; color:#8a8a8f; margin-bottom:8px;">Capital Inflow Vectors:</p>
                    <ul style="padding-left:20px; font-weight:bold; font-size:15px;">
                        {drivers_li}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Action Button to launch SOW Matrix (Updated colors)
        st.write("---")
        if st.button("🛡️ EXECUTE WEALTH VERACITY DUE DILIGENCE", use_container_width=True):
            st.session_state.view_mode = "audit"
            st.rerun()
            
    # --- AUDIT MATRIX & DETAILS VIEW ---
    elif st.session_state.view_mode == "audit":
        st.write("---")
        if st.button("← BACK TO SUMMARY", use_container_width=True):
            st.session_state.view_mode = "summary"
            st.rerun()
            
        st.header(f"ORIGIN OF CAPITAL MATRIX: {client['Name']}")
        
        # Clean Swiss Ledger Header
        col_h_name, col_h_src, col_h_act = st.columns([3, 2, 2])
        col_h_name.write("**CAPITAL INFLOW STREAM**")
        col_h_src.write("**INFLOW VERACITY RATING**")
        col_h_act.write("**DUE DILIGENCE WORKSPACE**")
        st.markdown("<hr style='border: 2px solid #2d2d30; margin-top:0; margin-bottom:15px;'>", unsafe_allow_html=True)
        
        # Loop SOW Categories
        for category, data in client["SOW_Drivers"].items():
            col_name, col_src, col_act = st.columns([3, 2, 2])
            
            # Column 1: SOW Driver Name
            col_name.markdown(f"<p style='font-size:18px; font-weight:bold; margin-top:10px;'>{category}</p>", unsafe_allow_html=True)
            
            # Column 2: Minimalist Status Outline Badge
            status = data["Status"]
            if status == "Fully Available":
                badge_html = f"<span class='badge-fully'>{status}</span>"
            elif status == "Partially Available":
                badge_html = f"<span class='badge-partially'>{status}</span>"
            elif status == "Not Available":
                badge_html = f"<span class='badge-not'>{status}</span>"
            else:
                badge_html = f"<span class='badge-na'>{status}</span>"
            col_src.markdown(f"<div style='margin-top:10px;'>{badge_html}</div>", unsafe_allow_html=True)
            
            # Column 3: Row Audit Drill-Down Action Button
            btn_lbl = "👉 ACTIVE VERIFICATION" if st.session_state.selected_sow == category else "🔍 VERIFY & CALIBRATE"
            if col_act.button(btn_lbl, key=f"btn_{client['Client_ID']}_{category}", use_container_width=True):
                st.session_state.selected_sow = category
                st.rerun()

        # --- FULL-WIDTH ACTIVE AUDIT WORKSPACE ---
        st.write("---")
        active_sow = st.session_state.selected_sow
        sow_data = client["SOW_Drivers"][active_sow]
        
        st.header(f"💼 DOCUMENTARY PROOF COMPARTMENT: {active_sow}")
        
        # Verification Ingestion Area
        uploaded_doc = st.file_uploader(
            f"Upload inflow verification voucher for {active_sow}", 
            type=["pdf", "csv", "xlsx"], 
            key=f"{client['Client_ID']}_{active_sow}_upload_container"
        )
        
        if uploaded_doc:
            if active_sow == "Executive Yield (Salary)" and uploaded_doc.name.endswith(".pdf"):
                with st.spinner("Extracting SOW Data..."):
                    parsed_rec = parse_pdf(uploaded_doc, llm_choice, api_key)
                if parsed_rec:
                    if parsed_rec["Client_ID"] == client["Client_ID"]:
                        if db.add_document_to_sow(client["Client_ID"], active_sow, uploaded_doc.name):
                            st.toast(f"Successfully linked {uploaded_doc.name} to {active_sow}!")
                            st.session_state.active_client = db.get_client(client["Client_ID"])
                            st.rerun()
                    else:
                        st.error(f"ERROR: Slip belongs to {parsed_rec['Client_ID']}.")
            else:
                if db.add_document_to_sow(client["Client_ID"], active_sow, uploaded_doc.name):
                    st.toast(f"Successfully linked {uploaded_doc.name} to {active_sow}!")
                    st.session_state.active_client = db.get_client(client["Client_ID"])
                    st.rerun()

        # Dynamic Checklist / Inflow Analysis based on active SOW type
        # If it's a periodic cashflow driver (Salary, Rent, Equity), show full 5-year timeline & charts!
        periodic_drivers = ["Executive Yield (Salary)", "Corporate Equity Liquidation", "Real Estate Yield (Rent)"] # Updated keys to match db.py
        
        if active_sow in periodic_drivers:
            st.write("**5-Year Document Audit Matrix:**")
            years = ["2019", "2020", "2021", "2022", "2023"]
            tabs = st.tabs(years)
            
            # Map visual indices based on type (Quarterly vs Monthly)
            is_quarterly = (active_sow == "Corporate Equity Liquidation")
            intervals = ["Q1", "Q2", "Q3", "Q4"] if is_quarterly else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            for yr_idx, year in enumerate(years):
                with tabs[yr_idx]:
                    col_m1, col_m2 = st.columns(2)
                    for idx, interval in enumerate(intervals):
                        pattern = f"{interval}_{year}"
                        has_file = any(pattern in f for f in sow_data["Slips"])
                        target_col = col_m1 if idx < (len(intervals) / 2) else col_m2
                        
                        if has_file:
                            target_col.markdown(f"🟩 **{interval}**: Received")
                        else:
                            target_col.markdown(f"🟥 **{interval}**: Missing")
            
            # DYNAMIC BENCHMARKING & CHARTS (Loads from client summary filtered by SOW Driver)
            try:
                full_db_df = pd.read_csv("mock_data/client_summary.csv")
                full_db_df['Date_Parsed'] = pd.to_datetime(full_db_df['Month_Year'], format='%b %Y', errors='coerce')
                client_sow_df = full_db_df[
                    (full_db_df['Client_ID'] == client['Client_ID']) & 
                    (full_db_df['SOW_Driver'] == active_sow)
                ].sort_values('Date_Parsed')
            except FileNotFoundError:
                client_sow_df = pd.DataFrame()
                
            if not client_sow_df.empty:
                st.write("---")
                st.subheader("MARKET PLAUSIBILITY CALIBRATION")
                fig_trend = px.line()
                px_colors = px.colors.qualitative.Plotly
                client_color = px_colors[0]
                serp_key = os.getenv("SERPAPI_KEY")
                
                # Dynamic search keyword based on SOW Type
                search_terms = {
                    "Executive Yield (Salary)": f"{client_sow_df['Job_Title'].iloc[0]} average salary",
                    "Corporate Equity Liquidation": "average corporate executive stock dividend payout",
                    "Real Estate Yield (Rent)": "average monthly commercial property rent yield"
                }

                search_q = search_terms.get(active_sow, f"{active_sow} average yield")
                
                with st.spinner(f"Scraping Web for '{active_sow}' Plausibility Index..."):
                    bench_val, src = fetch_real_benchmark(search_q, serp_key, llm_choice, api_key)
                    st.info(f"**Live Market Plausibility Index:** INR {bench_val} | {src}")
                    
                ideal_dates = pd.date_range(start='2019-01-01', end='2023-12-01', freq='MS')
                merged = pd.merge(pd.DataFrame({'Date_Parsed': ideal_dates}), client_sow_df[['Date_Parsed', 'Gross_Salary']], on='Date_Parsed', how='left')
                
                # Plot Actuals (Broken on gaps)
                fig_trend.add_scatter(x=merged['Date_Parsed'], y=merged['Gross_Salary'], mode='lines+markers', name='Actual Proof', line=dict(color=client_color), connectgaps=False)
                
                # Interpolate Gaps (Snaps perfect to curve)
                missing_dates = ideal_dates.difference(pd.to_datetime(client_sow_df['Date_Parsed']).dt.tz_localize(None))
                missing = merged[merged['Gross_Salary'].isna()].copy()
                if not missing.empty and bench_val > 0:
                    base_year = 2023
                    inflation_rate = 0.08
                    merged['Interpolated'] = merged['Gross_Salary'].interpolate(method='linear', limit_direction='both')
                    missing['Expected_Salary'] = merged.loc[missing.index, 'Interpolated']
                    
                    fig_trend.add_scatter(x=missing['Date_Parsed'], y=missing['Expected_Salary'], mode='markers', marker=dict(color=client_color, size=12, symbol='x'), name='Missing Voucher (Interpolated)')
                    
                fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), hovermode="x unified")
                fig_trend.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
                fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Volatility Graph (MoM Change)
                st.subheader("YIELD VARIANCE & VOLATILITY PROFILE (MoM % CHANGE)")
                client_sow_df['MoM_Change_%'] = client_sow_df['Gross_Salary'].pct_change() * 100
                fig_mom = px.bar(client_sow_df, x="Date_Parsed", y="MoM_Change_%")
                fig_mom.add_hline(y=10.0, line_dash="dash", line_color="#FF3333", annotation_text="Anomaly Threshold (+10%)")
                fig_mom.add_hline(y=-10.0, line_dash="dash", line_color="#FF3333", annotation_text="Anomaly Threshold (-10%)")
                fig_mom.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                fig_mom.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
                fig_mom.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
                st.plotly_chart(fig_mom, use_container_width=True)
                
                csv_missing = pd.DataFrame([{"Client_ID": client["Client_ID"], "SOW_Driver": active_sow, "Date": d.strftime('%b %Y')} for d in missing_dates]).to_csv(index=False).encode('utf-8')
                st.download_button("EXPORT MISSING LOG (CSV)", data=csv_missing, file_name=f"{client['Client_ID']}_missing_{active_sow.replace(' ', '_')}.csv", mime="text/csv")
            else:
                st.warning("No SOW transactions found in bank database for this category.")
        else:
            # Non-salary SOW drivers: Dynamic checklists
            st.write("**SOW COMPLIANCE DOCUMENT CHECKLIST:**")
            
            sow_checklists = {
                "Venture Fund Divestments": [ # Updated keys
                    {"name": "Venture Fund Exit Agreement / Term Sheet", "key": "US_Bond"},
                    {"name": "Tax Declaration / Capital Gains Return", "key": "Tax"},
                    {"name": "Bank Credit Voucher / Wire Confirmation", "key": "Credit"}
                ],
                "Inheritance & Trust Payouts": [
                    {"name": "Certified Will / Grant of Probate", "key": "Will"},
                    {"name": "Trust Deed & Distribution Voucher", "key": "Trust"},
                    {"name": "Bank Statement Showing Trust Payout Credit", "key": "Payout"}
                ]
            }
            
            checklist = sow_checklists.get(active_sow, [])
            if checklist:
                col_chk1, col_chk2 = st.columns(2)
                for idx, item in enumerate(checklist):
                    target_col = col_chk1 if idx % 2 == 0 else col_chk2
                    matched_file = next((f for f in sow_data["Slips"] if item["key"].lower() in f.lower()), None)
                    
                    if matched_file:
                        target_col.markdown(f"🟩 **{item['name']}**")
                        target_col.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;`Verified File: {matched_file}`")
                    else:
                        target_col.markdown(f"🟥 **{item['name']}**")
                        target_col.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;`Status: Missing (Awaiting Upload)`")
            else:
                st.write("**Pre-loaded / Uploaded SOW Files:**")
                if sow_data["Slips"]:
                    for f in sow_data["Slips"]: st.markdown(f"- `{f}`")
                else:
                    st.write("No files linked. Use uploader above to verify this driver.")
else:
    # --- HOMEPAGE PRE-SEARCH LANDING SCREEN ---
    st.write("---")
    st.markdown("""
    <div class="profile-card" style="border: 2px solid #FFFFFF; box-shadow: 8px 8px 0px #FFFFFF; padding: 30px;">
        <p style="margin:0; padding:0; font-size:14px; color:#8a8a8f !important; text-transform:uppercase; font-weight:900;">Fiduciary Compliance Gateway</p>
        <h1 style="border-bottom:none; font-size:36px; margin:10px 0 20px 0; color:#FFDF00 !important; font-family:'Helvetica Neue', Arial, sans-serif !important;">WEALTH GENESIS DUE DILIGENCE ENGINE</h1>
        <p style="font-size:15px; line-height:1.6; max-width:900px; font-family: 'Courier New', monospace;">
            This secure portal performs Enhanced Customer Due Diligence (ECDD) on Ultra-High-Net-Worth Individuals (UHNWIs) in accordance with Wolfsberg and MAS guidelines. It maps the <b>Origin of Capital Matrix</b>, performs live market plausibility calibrations, and logs deficiency registers.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("### SYSTEM CORE PROTOCOLS")
    step1, step2, step3 = st.columns(3)
    step1.markdown("""
    <div class="profile-card" style="height:100%; border:1px solid #2d2d30;">
        <h4 style="color:#00FFAA; margin:0 0 10px 0; font-weight:900; font-family:'Helvetica Neue',sans-serif;">01 / SEARCH LEDGER</h4>
        <p style="font-size:13px; color:#8a8a8f !important; line-height:1.5;">Select a designated Client's Capital Genesis Profile from the autocomplete search bar above to initialize verification.</p>
    </div>
    """, unsafe_allow_html=True)
    step2.markdown("""
    <div class="profile-card" style="height:100%; border:1px solid #2d2d30;">
        <h4 style="color:#FFDF00; margin:0 0 10px 0; font-weight:900; font-family:'Helvetica Neue',sans-serif;">02 / AUDIT CHANNELS</h4>
        <p style="font-size:13px; color:#8a8a8f !important; line-height:1.5;">Track Wealth Generation Streams, open documentary proof compartments, and directly ingest verification vouchers.</p>
    </div>
    """, unsafe_allow_html=True)
    step3.markdown("""
    <div class="profile-card" style="height:100%; border:1px solid #2d2d30;">
        <h4 style="color:#FF003C; margin:0 0 10px 0; font-weight:900; font-family:'Helvetica Neue',sans-serif;">03 / PLAUSIBILITY</h4>
        <p style="font-size:13px; color:#8a8a8f !important; line-height:1.5;">Compare executive yields, rental streams, and equity liquidations against live global market indices to verify wealth plausibility.</p>
    </div>
    """, unsafe_allow_html=True)
    
# --- SYSTEM SESSION CONTROL (Logout & Developer override) ---
st.write("---")
with st.expander("⚙️ SYSTEM SESSION CONTROL", expanded=False):
    col_logout, col_dev = st.columns(2)
    
    with col_logout:
        # Secure Logout Button
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.is_dev = False
            st.session_state.active_client = None
            st.session_state.view_mode = "summary"
            st.toast("LOGGED OUT.")
            st.rerun()
            
    with col_dev:
        # Developer Override Switch (Only visible if logged in as ghostkwebb)
        is_dev = st.session_state.get("is_dev", False)
        if is_dev:
            st.write("**🔧 DEVELOPER SYSTEM OVERRIDE ACTIVE**")
            dev_selection = st.radio(
                "Select Active Engine:", 
                ["LM Studio (Local)", "Groq (Cloud)"], 
                index=0 if st.session_state.dev_llm == "LM Studio (Local)" else 1, 
                key="dev_llm_selector_radio_btn", 
                horizontal=True
            )
            if dev_selection != st.session_state.dev_llm:
                st.session_state.dev_llm = dev_selection
                st.rerun()
        else:
            st.info("System Engine Status: Secured Cloud Mode")

# --- TERMINAL AI WIDGET ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "FINCRIME AGENT ONLINE. Awaiting command."}]

with st.popover("💬 TERMINAL AI", use_container_width=False):
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    prompt = st.chat_input("Query data (e.g., 'Hi' or 'Max salary?')...")
    
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        
        with chat_container:
            with st.chat_message("assistant"):
                if not client:
                    st.error("SYSTEM HALT: Search client first.")
                elif llm_choice == "Groq (Cloud)" and not api_key: 
                    st.error("SYSTEM HALT: Missing API Key.")
                else:
                    with st.spinner("Processing..."):
                        try:
                            full_db_df = pd.read_csv("mock_data/client_summary.csv")
                            df = full_db_df[full_db_df['Client_ID'] == client['Client_ID']]
                        except:
                            df = pd.DataFrame()
                        
                        # --- NEW: DYNAMIC HIGH-SPEED CONTEXT SUMMARY ---
                        sow_lines = []
                        for cat, data in client["SOW_Drivers"].items():
                            sow_lines.append(f"- {cat}: Status is '{data['Status']}'. Files linked: {', '.join(data['Slips']) if data['Slips'] else 'None'}")
                        sow_summary_str = "\\n".join(sow_lines)
                        
                        # Pack all summary metrics into system prompt
                        SYS_PREFIX = f"""
                        You are the EY Fiduciary AI Agent analyzing the active client: {client['Name']}.
                        Here is the live audited summary of the client's Origin of Capital Profile. 
                        Use this summary to answer questions INSTANTLY. DO NOT run python code if the answer is in this summary.
                        
                        [CLIENT SUMMARY]
                        - Client ID: {client['Client_ID']}
                        - Client Name: {client['Name']}
                        - Net Worth: {client['Net_Worth']}
                        - Nationality: {client['Nationality']}
                        - Relationship Since: {client['Relationship_Since']}
                        - Region / Sub-Region: {client['Region']} / {client['Sub_Region']}
                        - Account Number: {client['Account_Number']}
                        - RM Name: {client['RM_Name']}
                        - SOW Industry / SOW Country: {client['Industry']} / {client['Country']}
                        
                        [INFLOW STREAMS VERACITY COMPLIANCE]
                        {sow_summary_str}
                        
                        Only use the python_repl_ast tool if the user asks for a complex calculation on the dataframe `df` (like standard deviations, means, or custom aggregations) that is not listed in the summary above.
                        If user says 'Hi' or 'Hello', reply politely with a Final Answer.
                        """
                            
                        llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key) if llm_choice == "Groq (Cloud)" else ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="local-model", temperature=0)
                        try:
                            # Pass high-speed context prefix
                            agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True, number_of_head_rows=3, prefix=SYS_PREFIX)
                            safe_prompt = f"{prompt}\\n\\n(Remember: If the answer is in the system context summary, output 'Final Answer: [your response]' directly without using python tools)"
                            out = agent.invoke(safe_prompt)["output"]
                            st.markdown(out)
                            st.session_state.chat_history.append({"role": "assistant", "content": out})
                        except Exception as e:
                            err_str = str(e)
                            if "Could not parse LLM output:" in err_str:
                                out = err_str.split("Could not parse LLM output:")[1].strip().replace("`", "")
                                st.markdown(out)
                                st.session_state.chat_history.append({"role": "assistant", "content": out})
                            elif "413" in err_str or "rate_limit_exceeded" in err_str:
                                st.error("GROQ LIMIT HIT (6000 TPM). Wait 60s.")
                            else:
                                st.error(f"Error: {err_str}")
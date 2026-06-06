# app.py
import streamlit as st
import pandas as pd
import pdfplumber
import re
import plotly.express as px
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from serpapi import GoogleSearch

# --- SETUP ---
load_dotenv()
st.set_page_config(page_title="FinCrime Dashboard", layout="wide")

class SalaryData(BaseModel):
    Client_ID: str = Field(description="Unique client identifier")
    Name: str = Field(description="Employee name")
    Job_Title: str = Field(description="Job title")
    Month_Year: str = Field(description="Month and year")
    Gross_Salary: float = Field(description="Gross salary amount")

@st.cache_data 
def fetch_real_benchmark(job_title, serp_key, llm_choice, groq_key):
    fallbacks = {"Software Engineer": 75000, "Relationship Manager": 95000, "Data Analyst": 60000}
    if not serp_key: return fallbacks.get(job_title, 50000), "No SerpAPI key."
    
    params = {"q": f"average salary for {job_title} in India Glassdoor AmbitionBox", "hl": "en", "gl": "in", "api_key": serp_key}
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        snippets = " ".join([res.get("snippet", "") for res in results.get("organic_results", [])[:3]])
        
        if not snippets: return fallbacks.get(job_title, 50000), "No Google results."
        
        yearly_val = 0
        
        # 1. SMART PYTHON REGEX (Catches 90% of Indian Salary Formats instantly)
        # Looks for "₹6.5 Lakhs", "12 LPA", "5 Lakh" etc.
        lakh_match = re.search(r'(?:₹|Rs\.?)?\s*([\d\.]+)\s*(?:Lakhs?|LPA)', snippets, re.IGNORECASE)
        
        if lakh_match:
            yearly_val = int(float(lakh_match.group(1)) * 100000)
        else:
            # 2. LLM FALLBACK (If snippet uses weird formatting)
            if llm_choice == "Groq (Cloud)": llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=groq_key, temperature=0)
            else: llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", model="gemma-4-e4b-it", temperature=0)
                
            prompt = f"Snippets: '{snippets}'. Extract the average YEARLY salary. Return ONLY the raw integer. If it says '6 Lakhs', output 600000."
            ans = llm.invoke(prompt).content
            
            match = re.search(r'\d+', ans.replace(',', ''))
            if match: yearly_val = int(match.group())

        # 3. MATH & MULTIPLIER
        if yearly_val > 0:
            monthly_base = yearly_val // 12
            adjusted_val = int(monthly_base * 1.8) # 1.8x EY Premium Multiplier
        else:
            adjusted_val = fallbacks.get(job_title, 50000)
            
        # 4. STRICT SANITY CHECK
        if adjusted_val < 30000 or adjusted_val > 500000: 
            return fallbacks.get(job_title, 50000), f"Safe Fallback used. Extracted weird value: {yearly_val}/yr."
            
        return adjusted_val, f"Scraped Google -> {snippets[:100]}..."
        
    except Exception as e:
        return fallbacks.get(job_title, 50000), f"Error: {e}"

def parse_pdf(file, llm_choice, api_key):
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
        else: llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="gemma-4-e4b-it", temperature=0)
        try: return llm.with_structured_output(SalaryData).invoke(f"Extract details.\n\nText: {text}").model_dump()
        except Exception: return None

# --- CSS ---
st.markdown("""
<style>
    div[data-testid="stChatMessage"] { background-color: #121212 !important; border: 2px solid #333 !important; padding: 10px !important; margin-bottom: 10px !important; }
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
    .stApp, .main, .stAppViewContainer { background-color: #0A0A0A !important; font-family: 'Courier New', monospace !important; }
    h1, h2, h3, h4, p, span, label, div, li, summary, input { color: #FFFFFF !important; }
    h1, h2, h3 { border-bottom: 4px solid #FFFFFF !important; text-transform: uppercase; font-weight: 900 !important; margin-bottom: 20px !important; }
    
    /* Inputs & Uploaders */
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, [data-testid="stChatInput"] {
        background-color: #121212 !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important;
    }
    [data-testid="stFileUploadDropzone"] { border: 4px dashed #FFFFFF !important; background-color: #121212 !important; }
    [data-testid="stFileUploadDropzone"] * { color: #FFFFFF !important; background-color: transparent !important; }
    
    /* Boxes & Metrics */
    [data-testid="stExpander"], div[data-testid="metric-container"], [data-testid="stDataFrame"], .stAlert {
        background-color: #121212 !important; border: 4px solid #FFFFFF !important; box-shadow: 6px 6px 0px #FFFFFF !important; border-radius: 0px !important; margin-bottom: 15px !important;
    }
    
    /* Visual Tabs */
    button[role="tab"] { 
        background-color: #1E1E1E !important; 
        border: 2px solid #555555 !important; 
        border-bottom: 2px solid #FFFFFF !important; 
        border-radius: 10px 10px 0px 0px !important; /* Real tab shape */
        margin-right: 5px !important; 
        padding: 10px 25px !important;
        transition: all 0.3s;
    }
    button[role="tab"] * { color: #888888 !important; font-weight: bold !important; }
    button[role="tab"]:hover { background-color: #333333 !important; }
    button[role="tab"]:hover * { color: #FFFFFF !important; }
    
    button[role="tab"][aria-selected="true"] { 
        background-color: #FFDF00 !important; 
        border: 4px solid #FFFFFF !important; 
        border-bottom: 4px solid #FFDF00 !important; /* Erases bottom line */
        transform: translateY(4px); /* Pushes down to merge with box */
        z-index: 10;
    }
    button[role="tab"][aria-selected="true"] * { color: #000000 !important; font-weight: 900 !important; }
    
    /* Content box under tabs */
    div[data-testid="stTabs"] { 
        border-top: 4px solid #FFFFFF !important; 
        margin-top: -4px; 
        padding-top: 20px; 
    }
    
    /* Buttons */
    .stButton>button, .stDownloadButton>button { 
        background-color: #FFDF00 !important; color: #000 !important; border: 3px solid #FFF !important; box-shadow: 4px 4px 0px #FFF !important; border-radius: 0px !important; font-weight: 900 !important;
    }
    
    /* Terminal AI */
    div[data-testid="stPopover"] { 
        position: fixed !important; bottom: 30px !important; right: 30px !important; 
        z-index: 99999 !important; 
        width: fit-content !important; /* Kills the long bar */
        display: flex !important; justify-content: flex-end !important;
    }
    div[data-testid="stPopover"] > button { 
        background-color: #0A0A0A !important; color: #00FFAA !important; 
        border: 2px solid #00FFAA !important; border-radius: 50px !important; 
        padding: 10px 25px !important; font-size: 16px !important; 
        box-shadow: 0px 0px 15px rgba(0, 255, 170, 0.3) !important; 
        width: fit-content !important;
    }
    div[data-testid="stPopover"] > button * { color: #00FFAA !important; font-weight: bold !important; }
    
    /* 8. Inside AI Popover (No position hacks) */
    div[data-testid="stPopoverBody"] {
        background-color: #0A0A0A !important; border: 4px solid #00FFAA !important;
        box-shadow: 8px 8px 0px rgba(0, 255, 170, 0.5) !important; border-radius: 0px !important; 
        width: 380px !important; padding: 10px !important;
    }
    div[data-testid="stChatInput"] { border: 2px solid #333 !important; border-radius: 0px !important; }
    div[data-testid="stChatMessage"] { background-color: #121212 !important; border: 1px solid #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- UI START ---
st.title("SALARY DRIVER DASHBOARD")

with st.expander("⚙️ SYSTEM CONFIGURATION & DATA INGESTION", expanded=True):
    col1, col2 = st.columns([1, 2])
    with col1:
        # Check URL for hidden developer switch (?dev=true)
        is_dev = st.query_params.get("dev") == "true"
        
        if is_dev:
            llm_choice = st.radio("Select LLM:", ["LM Studio (Local)", "Groq (Cloud)"], index=1, key="dev_llm_selector")
        else:
            llm_choice = "Groq (Cloud)" # Silent default for RM
            st.info("System Engine: Secured Cloud") # Simple clean placeholder
            
        api_key = os.getenv("GROQ_API_KEY") if llm_choice == "Groq (Cloud)" else "lm-studio"
    
    with col2:
        uploaded_files = st.file_uploader("Upload Slips (PDF, CSV, Excel)", type=["pdf", "csv", "xlsx"], accept_multiple_files=True)

all_data = []

if uploaded_files:
    pb = st.progress(0, text="Ingesting files...")
    for i, file in enumerate(uploaded_files):
        pb.progress((i) / len(uploaded_files), text=f"Parsing: {file.name}")
        if file.name.endswith(".pdf"):
            data = parse_pdf(file, llm_choice, api_key)
            if data: all_data.append(data)
        elif file.name.endswith(".csv"): all_data.extend(pd.read_csv(file).to_dict('records'))
        elif file.name.endswith(".xlsx"): all_data.extend(pd.read_excel(file).to_dict('records'))
    pb.progress(1.0, text="Extraction complete.")

if all_data:
    df = pd.DataFrame(all_data)
    if 'Month_Year' in df.columns:
        df['Date_Parsed'] = pd.to_datetime(df['Month_Year'], format='%b %Y', errors='coerce')
        df = df.sort_values(['Client_ID', 'Date_Parsed'])

    calc_df = df.copy()
    calc_df['MoM_Change_%'] = calc_df.groupby('Client_ID')['Gross_Salary'].pct_change() * 100
    anomalies = calc_df[calc_df['MoM_Change_%'].abs() > 10.0]
    
    st.write("---")
    k1, k2 = st.columns(2) # Changed to 2 columns
    k1.metric("TOTAL CLIENTS", df['Client_ID'].nunique())
    k2.metric("PROCESSED SLIPS", len(df))
    st.write("---")

    all_client_ids = df['Client_ID'].unique()
    
    # Force single client selection. No "All Clients" option.
    selected_client = st.selectbox("Select Client to Analyze:", list(all_client_ids))
    
    # Filter dataframes to selected client strictly
    plot_df = df[df['Client_ID'] == selected_client]
    plot_calc_df = calc_df[calc_df['Client_ID'] == selected_client]

    # --- TABS IMPLEMENTATION ---
    tab_dash, tab_data = st.tabs(["📊 DASHBOARD & TRENDS", "🗄️ DATA AUDIT"])

    # TAB 1: DASHBOARD
    with tab_dash:
        st.subheader("BENCHMARK TREND ANALYSIS")
        fig_trend = px.line()
        px_colors = px.colors.qualitative.Plotly
        color_map = {c: px_colors[i % len(px_colors)] for i, c in enumerate(all_client_ids)}
        serp_key = os.getenv("SERPAPI_KEY")

        for client in plot_df['Client_ID'].unique():
            c_df = plot_df[plot_df['Client_ID'] == client].copy()
            job = c_df['Job_Title'].iloc[0] if 'Job_Title' in c_df.columns else "Unknown"
            
            # 1. Fetch External Industry Context (For Text Box)
            if job != "Unknown":
                with st.spinner(f"Scraping Web for '{job}'..."):
                    bench_val, src = fetch_real_benchmark(job, serp_key, llm_choice, api_key)
                    st.info(f"**{job} Industry Average:** INR {bench_val} | {src}")
                    
            merged = pd.merge(pd.DataFrame({'Date_Parsed': pd.date_range('2019-01-01', '2023-12-01', freq='MS')}), c_df[['Date_Parsed', 'Gross_Salary']], on='Date_Parsed', how='left')
            
            # 2. Plot Actual Line
            fig_trend.add_scatter(x=merged['Date_Parsed'], y=merged['Gross_Salary'], mode='lines+markers', name=f'{client} Actual', line=dict(color=color_map[client]), connectgaps=False)
            
            # 3. SMART FIX: Interpolate missing values mathematically based on client's own history
            missing = merged[merged['Gross_Salary'].isna()].copy()
            if not missing.empty:
                # Interpolate draws a straight line between the known months
                merged['Interpolated'] = merged['Gross_Salary'].interpolate(method='linear', limit_direction='both')
                missing['Expected_Salary'] = merged.loc[missing.index, 'Interpolated']
                
                fig_trend.add_scatter(x=missing['Date_Parsed'], y=missing['Expected_Salary'], mode='markers', marker=dict(color=color_map[client], size=14, symbol='x'), name=f'{client} Missing (Interpolated)')

        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), hovermode="x unified")
        fig_trend.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
        fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
        st.plotly_chart(fig_trend, use_container_width=True)

    # TAB 2: DATA AUDIT
    with tab_data:
        st.subheader("RAW DATABASE")
        st.dataframe(plot_df, use_container_width=True)

        st.subheader("MISSING DOCUMENT AUDIT")
        all_missing = []
        for client in plot_df['Client_ID'].unique():
            client_df = plot_df[plot_df['Client_ID'] == client]
            missing_dates = pd.date_range('2019-01-01', '2023-12-01', freq='MS').difference(pd.to_datetime(client_df['Date_Parsed']).dt.tz_localize(None))
            if len(missing_dates) > 0:
                st.write(f"**{client}** | Missing: {len(missing_dates)}")
                st.dataframe(pd.DataFrame({"Missing": missing_dates.strftime('%b %Y')}).T)
                for d in missing_dates: all_missing.append({"Client_ID": client, "Date": d.strftime('%b %Y')})
        if all_missing: st.download_button("EXPORT MISSING LOG", data=pd.DataFrame(all_missing).to_csv(index=False).encode('utf-8'), file_name="missing.csv")

else:
    st.info("System Standby. Open configuration above and upload data.")

# --- TERMINAL AI WIDGET ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "FINCRIME AGENT ONLINE. Awaiting command."}]

with st.popover("💬 TERMINAL AI", use_container_width=False):
    # NATIVE SCROLL BOX: Pushes input to bottom without CSS hacks
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): 
                st.markdown(msg["content"])

    prompt = st.chat_input("Query data (e.g., 'Hi' or 'Max salary?')...")
    
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        
        with chat_container:
            with st.chat_message("assistant"):
                if not all_data: 
                    st.error("SYSTEM HALT: Upload data first.")
                elif llm_choice == "Groq (Cloud)" and not api_key: 
                    st.error("SYSTEM HALT: Missing API Key.")
                else:
                    with st.spinner("Processing..."):
                        llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key) if llm_choice == "Groq (Cloud)" else ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="gemma-4-e4b-it", temperature=0)
                        try:
                            agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True, number_of_head_rows=3)
                            safe_prompt = f"Context: df1 is raw data, df2 is fraud alerts.\nUser: {prompt}\n\n(If greeting, reply exactly 'Final Answer: Hello! How can I assist you?')"
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
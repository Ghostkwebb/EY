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

@st.cache_data 
def fetch_real_benchmark(job_title, serp_key, llm_choice, groq_key):
    # 1. Hardcoded Fallbacks (Safety Net)
    fallbacks = {
        "Software Engineer": 75000,
        "Relationship Manager": 95000,
        "Data Analyst": 60000
    }
    
    if not serp_key:
        return fallbacks.get(job_title, 50000), "No SerpAPI key. Using fallback."
    
    # 2. Scrape Google
    params = {
        "q": f"average monthly salary for {job_title} in India Glassdoor",
        "hl": "en",
        "gl": "in",
        "api_key": serp_key
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        snippets = " ".join([res.get("snippet", "") for res in results.get("organic_results", [])[:3]])
        
        if not snippets: 
            return fallbacks.get(job_title, 50000), "No Google results found. Using fallback."
        
        # 3. Ask LLM (Better Prompt for India)
        if llm_choice == "Groq (Cloud)":
            llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=groq_key, temperature=0)
        else:
            llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", model="gemma-4-e4b-it", temperature=0)
            
        prompt = f"Search results: '{snippets}'. Extract average MONTHLY salary in INR. If it says 'Lakhs' or 'LPA' (like 6 Lakhs), assume 600000 and divide by 12. Return ONLY a single integer number. No commas."
        ans = llm.invoke(prompt)
        
        match = re.search(r'\d+', ans.content.replace(',', ''))
        val = int(match.group()) if match else 0
        
        if val > 300000: val = val // 12
        
        # 4. Sanity Check (If LLM gave garbage like 0 or 6)
        if val < 20000 or val > 200000:
            return fallbacks.get(job_title, 50000), f"LLM returned crazy value ({val}). Snippets: {snippets[:100]}..."
            
        return val, f"Source: Google Snippets -> {snippets[:200]}..."
    except Exception as e:
        return fallbacks.get(job_title, 50000), f"Error: {e}"

class SalaryData(BaseModel):
    Client_ID: str = Field(description="Unique client identifier, e.g., C-1001")
    Name: str = Field(description="Name of the employee")
    Job_Title: str = Field(description="Employee's job title or role")
    Month_Year: str = Field(description="Month and year of the slip, e.g., 'Jan 2019'")
    Gross_Salary: float = Field(description="The gross salary amount as a number")

load_dotenv()
st.set_page_config(page_title="Salary Benchmark Dashboard", layout="wide")

st.title("FinCrime: Salary Driver Dashboard (MVP)")

# --- 1. Settings & File Upload ---
st.sidebar.header("Settings")
llm_choice = st.sidebar.radio("Select LLM Mode:", ["LM Studio (Local)", "Groq (Cloud)"])
api_key = os.getenv("GROQ_API_KEY") if llm_choice == "Groq (Cloud)" else "lm-studio"

st.sidebar.header("Upload Salary Slips")
uploaded_files = st.sidebar.file_uploader(
    "Upload slips (PDF, CSV, Excel)", 
    type=["pdf", "csv", "xlsx"], 
    accept_multiple_files=True
)

# --- 2. Smart Hybrid Parse Logic ---
def parse_pdf(file, llm_choice, api_key):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
            
    # 1. FAST PATH: Try Regex first (0.01 seconds)
    try:
        client_id = re.search(r"Client ID:\s*(.+)", text).group(1).strip()
        name = re.search(r"Name:\s*(.+)", text).group(1).strip() 
        month_year = re.search(r"Month/Year:\s*(.+)", text).group(1).strip()
        job_title = re.search(r"Job Title:\s*(.+)", text).group(1).strip()
        gross = float(re.search(r"Gross Salary:\s*INR\s*(\d+)", text).group(1))
        
        return {
            "Client_ID": client_id, "Name": name, 
            "Job_Title": job_title, "Month_Year": month_year, 
            "Gross_Salary": gross
        }
    except AttributeError:
        # 2. SMART PATH: Regex failed (weird layout). Use LLM (2-5 seconds).
        if llm_choice == "Groq (Cloud)":
            llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key, temperature=0)
        else:
            llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="gemma-4-e4b-it", temperature=0)

        try:
            structured_llm = llm.with_structured_output(SalaryData)
            result = structured_llm.invoke(f"Extract salary details from this text. Return exact format.\n\nText: {text}")
            return result.model_dump()
        except Exception as e:
            # Both failed. 
            st.sidebar.error(f"Failed to parse {file.name}: {e}")
            return None

# --- 3. Process Files ---
all_data = []

if uploaded_files:
    total = len(uploaded_files)
    progress_bar = st.progress(0, text="Starting extraction...")
    
    for i, file in enumerate(uploaded_files):
        # Update progress bar
        pct = (i) / total
        progress_bar.progress(pct, text=f"Parsing {file.name} ({i+1}/{total})...")
        
        if file.name.endswith(".pdf"):
            data = parse_pdf(file, llm_choice, api_key)
            if data: all_data.append(data)
        elif file.name.endswith(".csv"):
            df_csv = pd.read_csv(file)
            all_data.extend(df_csv.to_dict('records'))
        elif file.name.endswith(".xlsx"):
            df_excel = pd.read_excel(file)
            all_data.extend(df_excel.to_dict('records'))
            
    progress_bar.progress(1.0, text="Extraction complete!")

# --- 4. Display & Analyze ---
if all_data:
    df = pd.DataFrame(all_data)
    
    if 'Month_Year' in df.columns:
        df['Date_Parsed'] = pd.to_datetime(df['Month_Year'], format='%b %Y', errors='coerce')
        df = df.sort_values(['Client_ID', 'Date_Parsed'])

    all_client_ids = df['Client_ID'].unique()
    px_colors = px.colors.qualitative.Plotly
    color_map = {client: px_colors[i % len(px_colors)] for i, client in enumerate(all_client_ids)}

    # --- Client Filter UI (Sidebar) ---
    st.sidebar.header("Filter Data")
    client_list = ["All Clients"] + list(all_client_ids)
    selected_client = st.sidebar.selectbox("Select Client to View", client_list)

    if selected_client != "All Clients":
        df = df[df['Client_ID'] == selected_client]

    st.subheader(f"Extracted Data: {selected_client}")
    st.dataframe(df, use_container_width=True)

    # --- 5. Missing Slip Logic ---
    st.subheader("Missing Salary Slips Analysis")
    clients = df['Client_ID'].unique()
    
    for client in clients:
        client_df = df[df['Client_ID'] == client]
        
        # Create ideal 60-month range (MVP assumes Jan 2019 start)
        min_date = pd.to_datetime('2019-01-01')
        max_date = pd.to_datetime('2023-12-01') 
        ideal_dates = pd.date_range(start=min_date, end=max_date, freq='MS')
        
        present_dates = pd.to_datetime(client_df['Date_Parsed']).dt.tz_localize(None)
        missing_dates = ideal_dates.difference(present_dates)
        
        st.write(f"**Client: {client}** | Missing Slips: {len(missing_dates)}")
        
        if len(missing_dates) > 0:
            missing_df = pd.DataFrame({"Missing_Month": missing_dates.strftime('%b %Y')})
            st.dataframe(missing_df.T) # Show horizontal
            st.write("**Benchmark Estimate for Missing Months:**")
            job_title = client_df['Job_Title'].iloc[0] if 'Job_Title' in client_df.columns else "Unknown"
            try:
                bench_df = pd.read_csv("mock_data/benchmark.csv")
                match = bench_df[bench_df['Job_Title'] == job_title]
                if not match.empty:
                    min_sal = match['Min_Salary'].values[0]
                    max_sal = match['Max_Salary'].values[0]
                    st.info(f"Industry Standard for '{job_title}': INR {min_sal} - INR {max_sal}")
                else:
                    st.warning(f"No benchmark found for {job_title}")
            except FileNotFoundError:
                st.warning("Benchmark CSV not found.")

    # --- 5.5 FinCrime Anomaly Detection ---
    st.subheader("⚠️ AML / FinCrime Alerts")
    
    # Calculate Month-over-Month (MoM) salary change
    calc_df = df.copy()
    calc_df['MoM_Change_%'] = calc_df.groupby('Client_ID')['Gross_Salary'].pct_change() * 100
    
    # Flag jumps or drops greater than 10%
    threshold = 10.0
    anomalies = calc_df[calc_df['MoM_Change_%'].abs() > threshold]
    
    if not anomalies.empty:
        suspects = ", ".join(anomalies['Client_ID'].unique())
        st.error(f"Alert: Found {len(anomalies)} unusual salary movements (> {threshold}% change). Flagged Clients: **{suspects}**")
        st.dataframe(
            anomalies[['Client_ID', 'Month_Year', 'Gross_Salary', 'MoM_Change_%']].style.format({'MoM_Change_%': '{:.2f}%'}),
            use_container_width=True
        )
    else:
        st.success(f"No abnormal salary jumps detected (Threshold: >{threshold}%).")
    
    # --- 6. Plot Salary Trend (With Gaps & Benchmarks) ---
    st.subheader("Salary Trend & Benchmarks")
    
    fig = px.line(title="Salary History vs Benchmarks")
    serp_key = os.getenv("SERPAPI_KEY")

    # Use the filtered df's clients, grabbing color from color_map (created in Phase 4)
    for client in df['Client_ID'].unique():
        client_color = color_map[client] # Stable color
        
        c_df = df[df['Client_ID'] == client].copy()
        job = c_df['Job_Title'].iloc[0] if 'Job_Title' in c_df.columns else "Unknown"
        
        # --- Live Web Benchmark via SerpAPI ---
        bench_val = 0
        bench_source = ""
        if job != "Unknown":
            with st.spinner(f"Fetching real benchmark for '{job}'..."):
                bench_val, bench_source = fetch_real_benchmark(job, serp_key, llm_choice, api_key)
                st.info(f"**Benchmark for {job}:** INR {bench_val} | {bench_source}")
                
        if bench_val == 0:
            st.warning(f"Could not fetch real benchmark for {job}. Check SerpApi Key. Using 0.")
            
        # Create ideal 60-month timeline (Jan 2019 to Dec 2023)
        ideal_dates = pd.date_range(start='2019-01-01', end='2023-12-01', freq='MS')
        merged = pd.DataFrame({'Date_Parsed': ideal_dates})
        merged = pd.merge(merged, c_df[['Date_Parsed', 'Gross_Salary']], on='Date_Parsed', how='left')
        
        # 1. Plot Actual Line (Match color)
        fig.add_scatter(
            x=merged['Date_Parsed'], 
            y=merged['Gross_Salary'],
            mode='lines+markers',
            name=f'{client} Actual',
            line=dict(color=client_color),
            connectgaps=False 
        )
        
        # 2. Plot Benchmark X (Match color, big size)
        missing = merged[merged['Gross_Salary'].isna()].copy()
        missing['Bench_Val'] = bench_val
        if not missing.empty:
            fig.add_scatter(
                x=missing['Date_Parsed'],
                y=missing['Bench_Val'],
                mode='markers',
                marker=dict(color=client_color, size=12, symbol='x'),
                name=f'{client} Live Benchmark Estimate'
            )

    st.plotly_chart(fig, use_container_width=True)

    # --- 7. LLM Chatbot ---
    st.subheader("Ask Data (LLM)")
    user_query = st.text_input("Ask question about uploaded salary data (e.g., 'What is max salary for C-1001?')")

    if user_query:
        if llm_choice == "Groq (Cloud)" and not api_key:
            st.error("Missing GROQ_API_KEY in .env file")
        else:
            if llm_choice == "Groq (Cloud)":
                llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key)
            else:
                llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="gemma-4-e4b-it", temperature=0)
                
            agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True)
            try:
                with st.spinner(f"Thinking using {llm_choice}..."):
                    response = agent.invoke(user_query)
                    st.success(response["output"])
            except Exception as e:
                st.error(f"Error: {e}")

else:
    st.info("Upload files in sidebar to begin.")
    
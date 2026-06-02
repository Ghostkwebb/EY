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

load_dotenv()
st.set_page_config(page_title="Salary Benchmark Dashboard", layout="wide")

st.title("FinCrime: Salary Driver Dashboard (MVP)")

# --- 1. File Upload ---
st.sidebar.header("Upload Salary Slips")
uploaded_files = st.sidebar.file_uploader(
    "Upload slips (PDF, CSV, Excel)", 
    type=["pdf", "csv", "xlsx"], 
    accept_multiple_files=True
)

# --- 2. Parse Logic ---
def parse_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    
    # MVP regex for fixed format
    try:
        client_id = re.search(r"Client ID:\s*(.+)", text).group(1).strip()
        name = re.search(r"Name:\s*(.+)", text).group(1).strip() # NEW
        month_year = re.search(r"Month/Year:\s*(.+)", text).group(1).strip()
        job_title = re.search(r"Job Title:\s*(.+)", text).group(1).strip()
        gross = float(re.search(r"Gross Salary:\s*INR\s*(\d+)", text).group(1))
        
        return {
            "Client_ID": client_id, 
            "Name": name, # NEW
            "Job_Title": job_title, 
            "Month_Year": month_year, 
            "Gross_Salary": gross
        }
    except AttributeError:
        return None # Fails if format unknown

# --- 3. Process Files ---
all_data = []

if uploaded_files:
    for file in uploaded_files:
        if file.name.endswith(".pdf"):
            data = parse_pdf(file)
            if data: all_data.append(data)
        elif file.name.endswith(".csv"):
            df_csv = pd.read_csv(file)
            all_data.extend(df_csv.to_dict('records'))
        elif file.name.endswith(".xlsx"):
            df_excel = pd.read_excel(file)
            all_data.extend(df_excel.to_dict('records'))

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
    
    bench_path = "mock_data/benchmark.csv"
    bench_df = pd.read_csv(bench_path) if os.path.exists(bench_path) else pd.DataFrame()

    fig = px.line(title="Salary History vs Benchmarks")

    # Use the filtered df's clients, but grab color from color_map
    for client in df['Client_ID'].unique():
        client_color = color_map[client] 
        c_df = df[df['Client_ID'] == client].copy()

        job = c_df['Job_Title'].iloc[0] if 'Job_Title' in c_df.columns else "Unknown"
        
        bench_val = 0
        if not bench_df.empty and job in bench_df['Job_Title'].values:
            match = bench_df[bench_df['Job_Title'] == job]
            bench_val = (match['Min_Salary'].values[0] + match['Max_Salary'].values[0]) / 2
            
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
                name=f'{client} Benchmark Estimate'
            )

    st.plotly_chart(fig, use_container_width=True)

    # --- 7. LLM Chatbot ---
    st.subheader("Ask Data (LLM)")
    
    # NEW: Toggle for local vs cloud
    llm_choice = st.radio("Select LLM Privacy Mode:", ["LM Studio (Local/Private)", "Groq (Cloud/Fast)"], horizontal=True)
    user_query = st.text_input("Ask question about uploaded salary data (e.g., 'What is max salary for C-1001?')")

    if user_query:
        llm = None
        error_msg = None
        
        if llm_choice == "Groq (Cloud/Fast)":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                error_msg = "Missing GROQ_API_KEY in .env file"
            else:
                llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=api_key)
        else:
            # LM Studio setup. Point to localhost port 1234.
            llm = ChatOpenAI(
                base_url="http://localhost:1234/v1",
                api_key="lm-studio", # LangChain needs dummy key
                model="gemma-4-e4b-it",
                temperature=0
            )

        if error_msg:
            st.error(error_msg)
        elif llm:
            agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True)
            try:
                with st.spinner(f"Thinking using {llm_choice}..."):
                    response = agent.invoke(user_query)
                    st.success(response["output"])
            except Exception as e:
                st.error(f"Error: {e}")

else:
    st.info("Upload files in sidebar to begin.")
    
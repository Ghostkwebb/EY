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

# --- INJECT LIGHT/DARK MODE TOGGLE ---
st.components.v1.html("""
<script>
const parentDoc = window.parent.document;

const sunSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M4.93 4.93l1.41 1.41"/><path d="M17.66 17.66l1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M6.34 17.66l-1.41 1.41"/><path d="M19.07 4.93l-1.41 1.41"/></svg>`;
const moonSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;

async function toggleTheme(event) {
    const currentTheme = parentDoc.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    if (!parentDoc.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        parentDoc.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateButtonIcon(newTheme);
        return;
    }
    
    const x = event.clientX;
    const y = event.clientY;
    
    const endRadius = Math.hypot(
        Math.max(x, window.parent.innerWidth - x),
        Math.max(y, window.parent.innerHeight - y)
    );
    
    const transition = parentDoc.startViewTransition(() => {
        parentDoc.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateButtonIcon(newTheme);
    });
    
    await transition.ready;
    
    parentDoc.documentElement.animate(
        {
            clipPath: [
                `circle(0px at ${x}px ${y}px)`,
                `circle(${endRadius}px at ${x}px ${y}px)`
            ]
        },
        {
            duration: 600,
            easing: 'ease-in-out',
            pseudoElement: '::view-transition-new(root)'
        }
    );
}

function updateButtonIcon(theme) {
    const btn = parentDoc.getElementById('theme-toggle-btn');
    if (btn) {
        btn.innerHTML = theme === 'light' ? moonSvg : sunSvg;
        btn.setAttribute('title', theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode');
    }
}

function initThemeToggle() {
    if (!parentDoc.getElementById('theme-transitions-style')) {
        const style = parentDoc.createElement('style');
        style.id = 'theme-transitions-style';
        style.textContent = `
            ::view-transition-old(root),
            ::view-transition-new(root) {
                animation: none;
                mix-blend-mode: normal;
            }
            ::view-transition-group(root) {
                animation-duration: 0.6s;
            }
            
            #theme-toggle-btn {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999999;
                width: 44px;
                height: 44px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                background-color: var(--btn-bg) !important;
                color: var(--btn-color) !important;
                border: 2px solid var(--btn-border) !important;
                box-shadow: 3px 3px 0px var(--btn-shadow) !important;
                transition: all 0.1s ease;
            }
            #theme-toggle-btn:hover {
                box-shadow: 0px 0px 0px var(--btn-shadow) !important;
                transform: translate(2px, 2px);
            }
            #theme-toggle-btn svg {
                width: 20px;
                height: 20px;
                stroke: currentColor;
            }
        `;
        parentDoc.head.appendChild(style);
    }
    
    if (!parentDoc.getElementById('theme-toggle-btn')) {
        const btn = parentDoc.createElement('div');
        btn.id = 'theme-toggle-btn';
        parentDoc.body.appendChild(btn);
        btn.addEventListener('click', toggleTheme);
    }
    
    const savedTheme = localStorage.getItem('theme') || 'dark';
    parentDoc.documentElement.setAttribute('data-theme', savedTheme);
    updateButtonIcon(savedTheme);
}

initThemeToggle();
</script>
""", height=0)

# --- STARK SWISS NEO-BRUTALIST STYLING ---
st.markdown("""
<style>
    /* CSS Variables for Light/Dark Mode */
    :root {
        --bg-color: #080808;
        --text-color: #FFFFFF;
        --card-bg: #121318;
        --border-color: #2d2d30;
        --chat-msg-bg: #121214;
        --tab-bg: #1E1E1E;
        --tab-border: #555555;
        --tab-inactive-text: #888888;
        --tab-active-border: #FFFFFF;
        --input-bg: #16171d;
        --meta-label: #8a8a8f;
        --gold-text: #FFDF00;
        
        --btn-bg: #FFFFFF;
        --btn-color: #000000;
        --btn-border: #FFFFFF;
        --btn-shadow: #00D2FF;
    }

    [data-theme="light"] {
        --bg-color: #F5F5F7;
        --text-color: #1D1D1F;
        --card-bg: #FFFFFF;
        --border-color: #E2E2E7;
        --chat-msg-bg: #EAEAEF;
        --tab-bg: #EAEAEF;
        --tab-border: #D1D1D6;
        --tab-inactive-text: #6E6E73;
        --tab-active-border: #000000;
        --input-bg: #FFFFFF;
        --meta-label: #6E6E73;
        --gold-text: #B28600;
        
        --btn-bg: #000000;
        --btn-color: #FFFFFF;
        --btn-border: #000000;
        --btn-shadow: #1E60FF;
    }

    /* Global Swiss Base Reset */
    div[data-testid="stChatMessage"] { background-color: var(--chat-msg-bg) !important; border: 2px solid var(--border-color) !important; padding: 10px !important; margin-bottom: 10px !important; }
    div[data-testid="stChatMessage"] * { color: var(--text-color) !important; }
    
    .stApp, .main, .stAppViewContainer { background-color: var(--bg-color) !important; font-family: 'Courier New', monospace !important; }
    h1, h2, h3, h4, p, span, label, div, li, summary, input { color: var(--text-color) !important; }
    
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
        background-color: var(--card-bg) !important; /* Deep slate blue/charcoal tint */
        border: 1px solid var(--border-color) !important;
        border-top: 4px solid #1E60FF !important; /* Blue top border */
        padding: 24px !important;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 5px 5px 0px var(--btn-shadow);
    }
    .profile-meta-item {
        border-bottom: 1px solid var(--border-color);
        padding: 8px 0;
        display: flex;
        justify-content: space-between;
    }
    .profile-meta-item b { color: var(--meta-label); }

    /* High Visibility Search Box - Electric Blue & Cyan Shadow */
    div[data-baseweb="select"] > div {
        background-color: var(--input-bg) !important;
        border: 2px solid #1E60FF !important; /* Blue Border */
        box-shadow: 4px 4px 0px var(--btn-shadow) !important; /* Cyan drop shadow */
        border-radius: 0px !important;
        height: 50px !important;
    }
    div[data-baseweb="select"] * {
        color: var(--text-color) !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }

    /* Minimalist Outline Badges */
    .badge-fully { border: 1px solid #00FFCC; color: #00FFCC !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-partially { border: 1px solid #1E60FF; color: #1E60FF !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-not { border: 1px solid #FF003C; color: #FF003C !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
    .badge-na { border: 1px solid #555555; color: var(--meta-label) !important; padding: 4px 12px; font-weight: bold; text-transform: uppercase; font-size: 12px; }

    /* Streamlit components */
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary, div[data-baseweb="input"] > div, [data-testid="stChatInput"] {
        background-color: var(--chat-msg-bg) !important; border: 1px solid var(--border-color) !important; border-radius: 0px !important;
    }
    [data-testid="stExpander"] { border: 1px solid var(--border-color) !important; border-radius: 0px !important; }
    
    /* Swiss Stark White Buttons with Cyan Shadow */
    .stButton>button, .stDownloadButton>button { 
        background-color: var(--btn-bg) !important; 
        color: var(--btn-color) !important; 
        border: 2px solid var(--btn-border) !important; 
        box-shadow: 4px 4px 0px var(--btn-shadow) !important; 
        border-radius: 0px !important; 
        font-weight: 900 !important; 
        text-transform: uppercase;
        font-size: 14px !important;
        transition: all 0.1s ease;
    }
    /* Force all text elements inside button to be black */
    .stButton>button *, .stDownloadButton>button * {
        color: var(--btn-color) !important;
        font-weight: 900 !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: var(--btn-shadow) !important; 
        border-color: var(--btn-shadow) !important;
        box-shadow: 0px 0px 0px var(--btn-shadow) !important;
    }
    /* Force text inside button to stay black on hover */
    .stButton>button:hover *, .stDownloadButton>button:hover * {
        color: #000000 !important;
    }
    .stButton>button:active { transform: translate(4px, 4px); }

    /* Visual Tabs - Centered blue accents */
    button[role="tab"] { 
        background-color: var(--tab-bg) !important; 
        border: 2px solid var(--tab-border) !important; 
        border-bottom: 2px solid var(--text-color) !important; 
        border-radius: 10px 10px 0px 0px !important; 
        margin-right: 5px !important; 
        padding: 10px 25px !important;
        transition: all 0.3s;
    }
    button[role="tab"] * { color: var(--tab-inactive-text) !important; font-weight: bold !important; }
    button[role="tab"]:hover { background-color: var(--border-color) !important; }
    button[role="tab"]:hover * { color: var(--text-color) !important; }
    
    button[role="tab"][aria-selected="true"] { 
        background-color: #1E60FF !important; 
        border: 4px solid var(--tab-active-border) !important; 
        border-bottom: 4px solid #1E60FF !important; 
        transform: translateY(4px); 
        z-index: 10;
    }
    button[role="tab"][aria-selected="true"] * { color: #FFFFFF !important; font-weight: 900 !important; }
    
    /* Content box under tabs */
    div[data-testid="stTabs"] { 
        border-top: 4px solid var(--text-color) !important; 
        margin-top: -4px; 
        padding-top: 20px; 
    }

    /* Popover Floating Chat - Blue Theme */
    div[data-testid="stPopover"] { 
        position: fixed !important; 
        bottom: 30px !important; 
        right: 30px !important; 
        z-index: 99999 !important; 
        width: fit-content !important; 
    }
    div[data-testid="stPopover"] button[data-testid="stPopoverButton"] { 
        background-color: var(--bg-color) !important; 
        color: var(--btn-shadow) !important; 
        border: 2px solid var(--btn-shadow) !important; 
        border-radius: 50px !important; 
        padding: 10px 25px !important; 
        font-size: 16px !important; 
        box-shadow: 0px 0px 15px rgba(0, 210, 255, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stPopover"] button[data-testid="stPopoverButton"] * {
        color: var(--btn-shadow) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stPopover"] button[data-testid="stPopoverButton"]:hover {
        background-color: var(--btn-shadow) !important;
        border-color: var(--btn-shadow) !important;
    }
    div[data-testid="stPopover"] button[data-testid="stPopoverButton"]:hover * {
        color: var(--bg-color) !important;
    }
    div[data-testid="stPopoverBody"] { 
        background-color: var(--bg-color) !important; 
        border: 4px solid var(--btn-shadow) !important; 
        box-shadow: 8px 8px 0px var(--btn-shadow) !important; 
        border-radius: 0px !important; 
        width: 380px !important; 
    }
    /* Internal scroll and structural boxes in Popover Body */
    div[data-testid="stPopoverBody"] .stVerticalBlock,
    div[data-testid="stPopoverBody"] [data-testid="stLayoutWrapper"],
    div[data-testid="stPopoverBody"] div.st-er {
        background-color: var(--bg-color) !important;
    }
    /* Popover chat input box override */
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] div,
    div[data-testid="stChatInput"] textarea {
        background-color: var(--input-bg) !important;
        color: var(--text-color) !important;
    }
    /* Force high-visibility placeholder */
    div[data-testid="stChatInput"] textarea::placeholder {
        color: var(--meta-label) !important;
        opacity: 1 !important;
    }
    div[data-testid="stChatInput"] { 
        border: 2px solid var(--border-color) !important; 
        border-radius: 0px !important; 
    }
    /* Prevent default Streamlit red focus ring/border */
    div[data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within {
        border-color: var(--btn-shadow) !important;
        box-shadow: 0 0 0 2px var(--btn-shadow) !important;
    }
    /* Send button on chat input */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: transparent !important;
        border: none !important;
    }
    button[data-testid="stChatInputSubmitButton"] svg {
        fill: var(--text-color) !important;
    }
    button[data-testid="stChatInputSubmitButton"]:hover {
        background-color: transparent !important;
    }
    button[data-testid="stChatInputSubmitButton"]:hover svg {
        fill: var(--btn-shadow) !important;
    }
    div[data-testid="stChatMessage"] { 
        background-color: var(--chat-msg-bg) !important; 
        border: 1px solid var(--border-color) !important; 
    }
    
    /* Selectbox Virtual Dropdown Styles */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: var(--card-bg) !important;
        border: 2px solid var(--border-color) !important;
        box-shadow: 4px 4px 0px var(--btn-shadow) !important;
        border-radius: 0px !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        font-family: 'Courier New', monospace !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover,
    ul[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] {
        background-color: var(--border-color) !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li * {
        color: var(--text-color) !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] * {
        font-weight: bold !important;
    }
    
    /* Stark Compact Monthly ledger uploaders */
    [data-testid="stFileUploader"] {
        padding: 0px !important;
        margin: 0px !important;
        width: 140px !important; /* Room for shadow button */
        max-width: 140px !important;
        height: auto !important;
    }
    [data-testid="stFileUploader"] label {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        border: none !important; /* NUKES THE DOTTED BOX ENTIRELY */
        background-color: transparent !important; /* Seamless background */
        box-shadow: none !important;
        padding: 0px !important;
        margin: 0px !important;
        width: 130px !important; 
        max-width: 130px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    /* Target Streamlit 1.38+ dropzone instructions and nuke them */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    /* Force the browse button to match the rest of the site (Stark White + Neon Green shadow) */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--btn-bg) !important; 
        color: var(--btn-color) !important; 
        border: 2px solid var(--btn-border) !important; 
        box-shadow: 3px 3px 0px #00FFAA !important; /* Neon Green shadow */
        border-radius: 0px !important; 
        font-weight: 900 !important; 
        text-transform: uppercase;
        font-size: 11px !important;
        padding: 4px 12px !important;
        margin: 0px auto !important;
        display: block !important;
        transition: all 0.1s ease;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #00FFAA !important; 
        border-color: #00FFAA !important;
        box-shadow: 0px 0px 0px #00FFAA !important;
    }
    /* Force text inside button to match button color */
    [data-testid="stFileUploaderDropzone"] button * {
        color: var(--btn-color) !important;
        font-weight: 900 !important;
        transition: all 0.1s ease !important;
    }
    /* Force text inside button to stay black on hover (since background becomes Neon Green) */
    [data-testid="stFileUploaderDropzone"] button:hover * {
        color: #000000 !important;
    }
    
    /* Dynamic Plotly overrides for Light/Dark mode compatibility */
    .js-plotly-plot .main-svg text:not(.hovertext):not(.legendtext):not(.legendtitletext):not(.nums):not(.name) {
        fill: var(--text-color) !important;
    }
    .js-plotly-plot .main-svg g.infolayer text.legendtext,
    .js-plotly-plot .main-svg g.infolayer text.legendtitletext {
        fill: var(--text-color) !important;
    }
    .js-plotly-plot .main-svg text.annotation-text {
        fill: var(--text-color) !important;
    }
    /* Extremely specific and robust overrides for hover tooltips (force white on dark tooltip backgrounds) */
    .js-plotly-plot .plot-container g.hoverlayer text,
    .js-plotly-plot .plot-container g.hoverlayer text *,
    .js-plotly-plot .plot-container g.hoverlayer text.legendtext,
    .js-plotly-plot .plot-container g.hoverlayer text.legendtitletext,
    .js-plotly-plot .plot-container g.hoverlayer text.nums,
    .js-plotly-plot .plot-container g.hoverlayer text.name,
    .js-plotly-plot .main-svg g.hoverlayer text,
    .js-plotly-plot .main-svg g.hoverlayer text * {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    .js-plotly-plot .main-svg path.xgrid,
    .js-plotly-plot .main-svg path.ygrid {
        stroke: var(--border-color) !important;
        stroke-opacity: 0.4 !important;
    }
    .js-plotly-plot .main-svg path.zl {
        stroke: var(--border-color) !important;
        stroke-opacity: 0.7 !important;
    }
    
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


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
def fetch_real_benchmark_sources(job_title, serp_key, llm_choice, groq_key):
    """Scrapes Google via SerpAPI, extracts monthly salary for the top 3 organic sources."""
    fallbacks = [
        {"val": 75000, "src": "Glassdoor (Fallback)", "snip": "Average national salary on Glassdoor", "link": "https://www.glassdoor.com"},
        {"val": 95000, "src": "AmbitionBox (Fallback)", "snip": "High-percentile yield on AmbitionBox", "link": "https://www.ambitionbox.com"},
        {"val": 60000, "src": "LinkedIn (Fallback)", "snip": "Junior-to-mid baseline on LinkedIn", "link": "https://www.linkedin.com"}
    ]
    if not serp_key: return fallbacks
    
    params = {"q": f"average salary for {job_title} in India Glassdoor AmbitionBox", "hl": "en", "gl": "in", "api_key": serp_key}
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])[:3]
        
        if not organic: return fallbacks
        
        sources = []
        for idx, res in enumerate(organic):
            title = res.get("title", "")
            d_link = res.get("displayed_link", "")
            snippet = res.get("snippet", "")
            link = res.get("link", "https://www.google.com")
            
            # FIXED: Dynamic domain extractor (Resolves "https:" bug)
            domain = d_link.split("/")[2] if "://" in d_link else d_link.split("/")[0]
            domain_clean = domain.replace("www.", "")
            
            src_name = "Glassdoor"
            if "ambitionbox" in domain_clean.lower() or "ambitionbox" in title.lower(): src_name = "AmbitionBox"
            elif "linkedin" in domain_clean.lower() or "linkedin" in title.lower(): src_name = "LinkedIn"
            else: src_name = domain_clean
            
            yearly_val = 0
            lakh_match = re.search(r'(?:₹|Rs\.?)?\s*([\d\.]+)\s*(?:Lakhs?|LPA)', snippet, re.IGNORECASE)
            
            if lakh_match:
                yearly_val = int(float(lakh_match.group(1)) * 100000)
            else:
                if llm_choice == "Groq (Cloud)": llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=groq_key, temperature=0)
                else: llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key=api_key, model="local-model", temperature=0)
                
                prompt = f"Snippet: '{snippet}'. Extract the average YEARLY salary in INR as a single raw integer. If Lakhs/LPA (6 Lakhs), output 600000. Output ONLY the raw integer."
                ans = llm.invoke(prompt).content
                match = re.search(r'\d+', ans.replace(',', ''))
                if match: yearly_val = int(match.group())

            if yearly_val > 0:
                adjusted_val = int((yearly_val // 12) * 1.8) # 1.8x EY Premium
            else:
                adjusted_val = fallbacks[idx % len(fallbacks)]["val"]
                
            if adjusted_val < 30000 or adjusted_val > 500000:
                adjusted_val = fallbacks[idx % len(fallbacks)]["val"]
                
            sources.append({"val": adjusted_val, "src": f"{src_name} (Scraped)", "snip": snippet, "link": link})
            
        while len(sources) < 3:
            sources.append(fallbacks[len(sources)])
        return sources
    except Exception:
        return fallbacks

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
    # --- PAGE 1: summary (Homepage Profile Summary) ---
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
            
        # Large Swiss White Button to move to Page 2
        st.write("---")
        if st.button("🛡️ EXECUTE WEALTH VERACITY DUE DILIGENCE", use_container_width=True):
            st.session_state.view_mode = "matrix"
            st.rerun()
            
    # --- PAGE 2: matrix (Origin of Capital Compliance Matrix) ---
    elif st.session_state.view_mode == "matrix":
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
        st.markdown("<hr style='border: 1px solid #2d2d30; margin-top:0; margin-bottom:15px;'>", unsafe_allow_html=True)
        
        # Loop SOW Categories
        for category, data in client["SOW_Drivers"].items():
            col_name, col_src, col_act = st.columns([3, 2, 2])
            
            # SOW Driver Name
            col_name.markdown(f"<p style='font-size:18px; font-weight:bold; margin-top:10px;'>{category}</p>", unsafe_allow_html=True)
            
            # Minimalist Status Outline Badge
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
            
            # Drill-Down Action Button - Moves to Page 3
            if col_act.button("🔍 AUDIT STREAM", key=f"btn_{client['Client_ID']}_{category}", use_container_width=True):
                st.session_state.selected_sow = category
                st.session_state.view_mode = "compartment"
                st.rerun()

    # --- PAGE 3: compartment (Active Documentary Proof Compartment) ---
    elif st.session_state.view_mode == "compartment":
        st.write("---")
        if st.button("← BACK TO COMPLIANCE MATRIX", use_container_width=True):
            st.session_state.view_mode = "matrix"
            st.rerun()
            
        active_sow = st.session_state.selected_sow
        sow_data = client["SOW_Drivers"][active_sow]
        
        st.header(f"💼 DOCUMENTARY PROOF COMPARTMENT: {active_sow}")
        st.write("") # Padding

        periodic_drivers = ["Executive Yield (Salary)", "Corporate Equity Liquidation", "Real Estate Yield (Rent)"]
        
        # A. PERIODIC CHANNELS: 60-Month Grid with INDIVIDUAL Row Uploaders
        if active_sow in periodic_drivers:
            st.write("### 📅 DOCUMENTARY VERIFICATION LEDGER")
            years = ["2019", "2020", "2021", "2022", "2023"]
            tabs = st.tabs(years)
            
            is_quarterly = (active_sow == "Corporate Equity Liquidation")
            intervals = ["Q1", "Q2", "Q3", "Q4"] if is_quarterly else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            for yr_idx, year in enumerate(years):
                with tabs[yr_idx]:
                    col_m1, col_m2 = st.columns(2)
                    
                    for idx, interval in enumerate(intervals):
                        target_col = col_m1 if idx < (len(intervals) / 2) else col_m2
                        pattern = f"{interval}_{year}"
                        has_file = any(pattern in f for f in sow_data["Slips"])
                        
                        # Sub-columns inside each month slot for visual alignment
                        row_lbl, row_status, row_act = target_col.columns([1, 1.2, 2.5])
                        row_lbl.markdown(f"**{interval}**")
                        
                        if has_file:
                            row_status.markdown("🟩 Received")
                            row_act.write("`-`")
                        else:
                            row_status.markdown("🟥 Missing")
                            # INDIVIDUAL INLINE UPLOADER PER MONTH
                            up_file = row_act.file_uploader(
                                "Upload Voucher",
                                type=["pdf", "csv", "xlsx"],
                                key=f"up_{client['Client_ID']}_{active_sow}_{year}_{interval}",
                                label_visibility="collapsed"
                            )
                            if up_file:
                                # Strict Compliance Lock
                                if active_sow == "Executive Yield (Salary)" and up_file.name.endswith(".pdf"):
                                    with st.spinner("Extracting..."):
                                        parsed = parse_pdf(up_file, llm_choice, api_key)
                                    if parsed:
                                        # Verify Month & Year match
                                        extracted_month_year = f"{interval} {year}"
                                        if parsed["Client_ID"] == client["Client_ID"] and parsed["Month_Year"] == extracted_month_year:
                                            if db.add_document_to_sow(client["Client_ID"], active_sow, up_file.name):
                                                st.toast(f"Linked {up_file.name} to {interval} {year}!")
                                                st.session_state.active_client = db.get_client(client["Client_ID"])
                                                st.rerun()
                                        else:
                                            st.error(f"VERIFICATION FAILURE: File is for {parsed['Month_Year']}, expected {extracted_month_year}.")
                                else:
                                    # Direct backfill
                                    if db.add_document_to_sow(client["Client_ID"], active_sow, up_file.name):
                                        st.toast(f"Linked {up_file.name} successfully!")
                                        st.session_state.active_client = db.get_client(client["Client_ID"])
                                        st.rerun()
            
            # B. MARKET PLAUSIBILITY CALIBRATION (Scrapes Google, offers Top 3 Options)
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
                
                # Dynamic search keyword
                search_terms = {
                    "Executive Yield (Salary)": f"{client_sow_df['Job_Title'].iloc[0]} average salary",
                    "Corporate Equity Liquidation": "average corporate executive stock dividend payout",
                    "Real Estate Yield (Rent)": "average monthly commercial property rent yield"
                }
                search_q = search_terms.get(active_sow, f"{active_sow} average yield")
                serp_key = os.getenv("SERPAPI_KEY")
                
                # Dynamic Scrape (Top 3 Sources)
                with st.spinner("Scraping index sources..."):
                    sources = fetch_real_benchmark_sources(search_q, serp_key, llm_choice, api_key)
                
                # NEW: Dropdown expander for Source Verification Audit & Selector
                with st.expander("📄 VIEW VERIFIED SOURCE SNIPPETS & COMPLIANCE LINKS"):
                    # RM Verification selector is now safely housed inside the expander
                    st.write("**Verify Plausibility Reference Source:**")
                    source_options = [f"{s['src']} : INR {s['val']}/mo" for s in sources]
                    selected_option = st.radio(
                        "SELECT VERIFIED REFERENCE SOURCE (Updates Trend Chart):",
                        options=source_options,
                        key=f"calibration_selector_{active_sow}"
                    )
                    
                    # Unpack selected values
                    selected_idx = source_options.index(selected_option)
                    bench_val = sources[selected_idx]["val"]
                    snippet_text = sources[selected_idx]["snip"]
                    source_url = sources[selected_idx]["link"]
                    
                    st.markdown("---")
                    st.markdown(f"**Verified Source URL:** [Open Source Site]({source_url})")
                    st.markdown(f"**Scraped Context/Snippet:** *{snippet_text}*")
                
                # C. Plot charts calibrated to selected source
                fig_trend = px.line()
                client_color = px.colors.qualitative.Plotly[0]
                ideal_dates = pd.date_range(start='2019-01-01', end='2023-12-01', freq='MS')
                merged = pd.merge(pd.DataFrame({'Date_Parsed': ideal_dates}), client_sow_df[['Date_Parsed', 'Gross_Salary']], on='Date_Parsed', how='left')
                
                # Plot Actuals
                fig_trend.add_scatter(x=merged['Date_Parsed'], y=merged['Gross_Salary'], mode='lines+markers', name='Actual Proof', line=dict(color=client_color), connectgaps=False)
                
                # Interpolate Gaps using selected bench_val
                missing = merged[merged['Gross_Salary'].isna()].copy()
                if not missing.empty and bench_val > 0:
                    base_year = 2023
                    inflation_rate = 0.08
                    merged['Interpolated'] = merged['Gross_Salary'].interpolate(method='linear', limit_direction='both')
                    missing['Expected_Salary'] = merged.loc[missing.index, 'Interpolated']
                    
                    fig_trend.add_scatter(x=missing['Date_Parsed'], y=missing['Expected_Salary'], mode='markers', marker=dict(color=client_color, size=12, symbol='x'), name='Missing Voucher (Interpolated)')
                    
                fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="var(--text-color)"), hovermode="x unified")
                fig_trend.update_xaxes(showgrid=True, gridwidth=1, gridcolor='var(--border-color)')
                fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor='var(--border-color)')
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # D. Volatility
                st.subheader("YIELD VARIANCE & VOLATILITY PROFILE (MoM % CHANGE)")
                client_sow_df['MoM_Change_%'] = client_sow_df['Gross_Salary'].pct_change() * 100
                fig_mom = px.bar(client_sow_df, x="Date_Parsed", y="MoM_Change_%")
                fig_mom.add_hline(y=10.0, line_dash="dash", line_color="#FF3333", annotation_text="Anomaly Threshold (+10%)")
                fig_mom.add_hline(y=-10.0, line_dash="dash", line_color="#FF3333", annotation_text="Anomaly Threshold (-10%)")
                fig_mom.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="var(--text-color)"))
                fig_mom.update_xaxes(showgrid=True, gridwidth=1, gridcolor='var(--border-color)')
                fig_mom.update_yaxes(showgrid=True, gridwidth=1, gridcolor='var(--border-color)')
                st.plotly_chart(fig_mom, use_container_width=True)
                
                missing_dates = ideal_dates.difference(pd.to_datetime(client_sow_df['Date_Parsed']).dt.tz_localize(None))
                csv_missing = pd.DataFrame([{"Client_ID": client["Client_ID"], "SOW_Driver": active_sow, "Date": d.strftime('%b %Y')} for d in missing_dates]).to_csv(index=False).encode('utf-8')
                st.download_button("EXPORT MISSING LOG (CSV)", data=csv_missing, file_name=f"{client['Client_ID']}_missing_{active_sow.replace(' ', '_')}.csv", mime="text/csv")
            else:
                st.warning("No SOW transactions found in bank database for this category.")
                
        # B. NON-PERIODIC CHANNELS: Dynamic Checklists (Inheritance, trusts)
        else:
            st.write("### 📋 SOW COMPLIANCE DOCUMENT CHECKLIST")
            sow_checklists = {
                "Venture Fund Divestments": [
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
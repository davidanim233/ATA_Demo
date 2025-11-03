import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ==============================================================
# PAGE CONFIG
# ==============================================================
st.set_page_config(
    page_title="OEM Tracing AI Assistant — ATA Portal",
    layout="centered",
    page_icon="🤖"
)

# ==============================================================
# RESOLVE IMAGE PATH
# ==============================================================
BASE_DIR = Path(__file__).parent
robot_logo = BASE_DIR / "assets" / "ata_logo_blue.png"

# ==============================================================
# QUERY PARAM HELPERS
# ==============================================================
def _qp(key: str, default: str = ""):
    try:
        return st.query_params.get(key, default)
    except Exception:
        return default

def _is_embed_mode() -> bool:
    return _qp("embed", "false").lower() in ("1", "true", "yes")

# ==============================================================
# STYLES
# ==============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {font-family:'Inter',sans-serif;background:linear-gradient(135deg,#F2F8FF 0%,#E6F0FA 100%);}
    h1,h2,h3{color:#003A70;font-weight:700;}
    .robot-name{font-size:26px;font-weight:700;color:#003A70;margin-bottom:6px;}
    .robot-desc{font-size:15px;color:#3A3A3A;line-height:1.5;}
    .result-card{background:white;border-radius:20px;padding:25px 35px;box-shadow:0 4px 15px rgba(0,0,0,0.07);margin:25px auto;width:720px;max-width:90%;}
    </style>
""", unsafe_allow_html=True)

if _is_embed_mode():
    st.markdown("""
        <style>
        header, .stDeployButton, footer { display: none !important; }
        .block-container { padding-top: 0.75rem; padding-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

# ==============================================================
# HEADER
# ==============================================================
col1, col2 = st.columns([1, 4], gap="medium")
with col1:
    if robot_logo.exists():
        st.image(str(robot_logo), width=85)
    else:
        st.write("🤖")
with col2:
    st.markdown("""
        <div class="robot-name">ATA — Analytics Team Agent</div>
        <div class="robot-desc">
            Built by the DIT Analytics Team (David, Ivan, Tanbeer)<br>
            Helping you query, explore, and understand OEM Socket Tracing Data faster.
        </div>
    """, unsafe_allow_html=True)
st.markdown("---")

# ==============================================================
# DEMO DATA + MOCK FUNCTION
# ==============================================================
demo_data = pd.DataFrame({
    "OEM": ["Mindray", "Philips", "GE Healthcare"],
    "Fiscal_Month": ["FY25-M01", "FY25-M02", "FY25-M03"],
    "Quantities": [245, 315, 289],
    "Region": ["US", "EU", "APAC"]
})

def generate_sql_mock(question: str):
    """Simulate SQL generation for demo."""
    q = question.lower()
    if "quantity" in q:
        return "SELECT OEM, SUM(QUANTITIES) FROM TRACING_ST_SMALL_NEW GROUP BY OEM;"
    elif "region" in q:
        return "SELECT REGION, SUM(QUANTITIES) FROM TRACING_ST_SMALL_NEW GROUP BY REGION;"
    else:
        return "SELECT * FROM TRACING_ST_SMALL_NEW LIMIT 10;"

def run_sql_mock(sql: str):
    """Simulate result preview."""
    return demo_data.sample(min(3, len(demo_data)))

# ==============================================================
# USER INPUT
# ==============================================================
prefill_q = _qp("q", "")
question = st.text_input("Ask ATA a question about OEM Tracing Data:", value=prefill_q)

# ==============================================================
# EXECUTION + RESULTS
# ==============================================================
if question:
    with st.spinner("ATA is analyzing your question and generating SQL..."):
        sql = generate_sql_mock(question)
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.subheader("ATA-Generated SQL Query")
    st.code(sql, language="sql")

    st.success("Query executed successfully (demo mode)!")
    view_option = st.radio(
        "Choose how to view the result:",
        ("Table", "Chart", "SQL Only"),
        horizontal=True
    )
    df = run_sql_mock(sql)
    if view_option == "Table":
        st.dataframe(df)
    elif view_option == "Chart":
        st.bar_chart(df.set_index("OEM")["Quantities"])
    elif view_option == "SQL Only":
        st.code(sql, language="sql")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("💡 Tip: Try asking — *Show total quantities by OEM for the last 3 months.*")

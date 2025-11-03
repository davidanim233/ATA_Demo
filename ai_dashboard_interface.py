import streamlit as st
import pandas as pd
import re
from pathlib import Path

# ==============================================================
# PAGE CONFIGURATION
# ==============================================================
st.set_page_config(
    page_title="ATA — Analytics Team Agent",
    layout="centered",
    page_icon="🤖",
)

# ==============================================================
# PATHS & LOGOS
# ==============================================================
BASE_DIR = Path(__file__).parent
robot_logo = BASE_DIR / "assets" / "ata_logo_blue.png"

# ==============================================================
# QUERY PARAMETER HELPERS
# ==============================================================
def _qp(key: str, default: str = ""):
    """Safely fetch query parameters."""
    try:
        return st.query_params.get(key, default)
    except Exception:
        return default


def _is_embed_mode() -> bool:
    """Detect if running inside Tableau iframe."""
    return _qp("embed", "false").lower() in ("1", "true", "yes")


# ==============================================================
# GLOBAL STYLES (CLEAN INTERFACE)
# ==============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #F2F8FF 0%, #E6F0FA 100%);
    }
    h1, h2, h3 {
        color: #003A70;
        font-weight: 700;
    }
    .robot-name {
        font-size: 26px;
        font-weight: 700;
        color: #003A70;
        margin-bottom: 6px;
    }
    .robot-desc {
        font-size: 15px;
        color: #3A3A3A;
        line-height: 1.5;
    }
    .result-card {
        background: white;
        border-radius: 20px;
        padding: 25px 35px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.07);
        margin: 25px auto;
        width: 720px;
        max-width: 90%;
    }
    /* Hide Streamlit branding */
    #MainMenu, footer, header, .stDeployButton, div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# Compact styling for iframe mode
if _is_embed_mode():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
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
# SQL GENERATION LOGIC (BASED ON YOUR VIEW)
# ==============================================================
def generate_sql_mock(question: str) -> str:
    """Generate Snowflake SQL dynamically based on question text."""
    q = question.lower().strip()

    table = "TRACING_ST_SMALL_NEW"
    filters = []
    group_by = ""
    order_by = ""
    limit = 10

    # --- FILTERS ---
    m_oem = re.search(r"for\s+([a-z0-9\s\-_]+)", q)
    if m_oem:
        oem_name = m_oem.group(1).strip().upper()
        filters.append(f"OEM ILIKE '%{oem_name}%'")

    m_state = re.search(r"in\s+(state\s+)?([a-z]{2,})", q)
    if m_state:
        state_val = m_state.group(2).upper()
        filters.append(f"STATE ILIKE '%{state_val}%'")

    m_months = re.search(r"last\s+(\d+)\s+months?", q)
    if m_months:
        months = int(m_months.group(1))
        filters.append(f"OEM_DATE >= DATEADD('month', -{months}, CURRENT_DATE())")

    # --- GROUP BY LOGIC ---
    if "by state" in q:
        group_by = "STATE"
    elif "by city" in q:
        group_by = "CITY"
    elif "by lob" in q:
        group_by = "LOB"
    else:
        group_by = "OEM"

    metric = "SUM(QUANTITIES) AS TOTAL_QUANTITIES"

    # --- TOP/LIMIT LOGIC ---
    if "top" in q:
        m_top = re.search(r"top\s+(\d+)", q)
        if m_top:
            limit = int(m_top.group(1))
        order_by = "ORDER BY TOTAL_QUANTITIES DESC"

    # --- FINAL SQL ---
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql = f"""
SELECT {group_by}, {metric}
FROM {table}
{where_clause}
GROUP BY {group_by}
{order_by}
LIMIT {limit};
""".strip()

    return sql

# ==============================================================
# DEMO DATA GENERATOR
# ==============================================================
def run_sql_mock(sql: str):
    """Return mock results consistent with schema."""
    mock_data = {
        "OEM": ["PHILIPS", "MINDRAY", "GE HEALTHCARE", "NIHON KODEN", "DRAEGER"],
        "STATE": ["TX", "CA", "NY", "IL", "FL"],
        "CITY": ["DALLAS", "LOS ANGELES", "NEW YORK", "CHICAGO", "MIAMI"],
        "LOB": ["CAPNOGRAPHY", "MONITORING", "VENTILATION", "INFUSION", "SURGICAL"],
        "TOTAL_QUANTITIES": [41500, 21000, 15800, 9200, 7100],
    }
    df = pd.DataFrame(mock_data)
    df = df.sample(frac=1).reset_index(drop=True)
    return df.head(5)

# ==============================================================
# USER INPUT
# ==============================================================
prefill_q = _qp("q", "")
question = st.text_input("Ask ATA a question about OEM Tracing Data:", value=prefill_q)

# ==============================================================
# EXECUTION & OUTPUT
# ==============================================================
if question:
    with st.spinner("ATA is analyzing your question and generating SQL..."):
        sql = generate_sql_mock(question)

    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.subheader("ATA-Generated SQL Query")
    st.code(sql, language="sql")

    st.success("✅ Query executed successfully (demo mode)!")
    view_option = st.radio(
        "Choose how to view the result:",
        ("Table", "Chart", "SQL Only"),
        horizontal=True
    )

    df = run_sql_mock(sql)
    if view_option == "Table":
        st.dataframe(df, use_container_width=True)
    elif view_option == "Chart":
        st.bar_chart(df.set_index(df.columns[0])["TOTAL_QUANTITIES"])
    else:
        st.code(sql, language="sql")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("💡 Try asking: *Top 5 OEMs by quantities in Texas for the last 3 months.*")

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64
from pathlib import Path

LOGO_PATH = Path("SEC_Thailand_Logo.svg.png")

st.set_page_config(
    layout="wide",
    page_title="FA Approval Dashboard",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "✅",
)

def get_image_as_base64(path: Path):
    if not path.is_file(): return None
    return base64.b64encode(path.read_bytes()).decode()

st.markdown(
    '<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">',
    unsafe_allow_html=True,
)
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700;800&display=swap');
:root {
    --primary-color: #00A99D;
    --text-dark: #111827;
    --text-mid: #374151;
    --text-light: #6B7280;
    --bg: #FFFFFF;
    --panel-bg: #F9FAFB;
    --border: #E5E7EB;
    --shadow-sm: 0 1px 2px rgba(0,0,0,.04);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,.03), 0 2px 4px -2px rgba(0,0,0,.03);
}
html, body, [class*="st-"], [class*="css-"] {
    font-family: 'Sarabun', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text-dark);
}
#MainMenu, footer, header[data-testid="stHeader"] {
    display: none !important;
}
.main .block-container {
    padding: 1.5rem 2.5rem 2rem 2.5rem;
    max-width: 1600px;
}
.header-grid {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    margin-bottom: 0.5rem;
}
.title-area {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.title-area .caret {
    font-size: 24px;
    color: #4B5563;
}
.title-area .main-title {
    font-size: 28px;
    font-weight: 800;
    color: var(--text-dark);
    margin: 0;
    margin-right: 0.75rem;
}
.controls-area {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.pill-buttons {
    display: flex;
    gap: 0.75rem;
}
}
.page-controls-grid {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    margin-bottom: 2rem;
}
.page-switcher {
    display: flex;
    gap: 0.5rem;
}
.search-area .stTextInput {
    width: 250px;
}
.pill-buttons .stButton>button,
.page-switcher .stButton>button {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-weight: 600;
    color: var(--text-mid);
    box-shadow: var(--shadow-sm);
}
.pill-buttons .stButton>button {
    padding: .4rem 1.1rem;
    height: 38px;
}
.page-switcher .stButton>button {
    padding: .3rem 1rem;
}
.page-switcher .stButton>button.active-page {
    border-color: var(--primary-color);
    background-color: #F0F9F8;
    color: var(--primary-color);
}
.search-area .stTextInput > div {
    border-radius: 8px;
    border-color: var(--border);
    background: #fff;
    height: 38px;
}
.search-area .stTextInput input {
    height: 38px;
}
.kpi-card {
    background: var(--panel-bg);
    border: 1px solid #F3F4F6;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: var(--shadow-md);
    height: 100%;
}
.kpi-card .icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #E0F2F1;
    color: var(--primary-color);
    flex-shrink: 0;
}
.kpi-card .title {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-light);
    margin: 0 0 .25rem 0;
}
.kpi-card .value {
    font-size: 2.25rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text-dark);
}
.kpi-card .suffix {
    font-size: .9rem;
    color: var(--text-light);
}
.chart-panel,
.framed-panel {
    background: var(--panel-bg);
    border: 2px solid #B1B1B1;
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
    height: 100%;
}
.chart-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-dark);
    margin: 0 0 .5rem 0;
}
.chart-legend {
    display: flex;
    gap: 1rem;
    margin: .25rem 0 1rem 0;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: .4rem;
    font-size: .8rem;
    color: var(--text-light);
}
.legend-dot,
.legend-square {
    width: 10px;
    height: 10px;
}
.legend-dot {
    border-radius: 50%;
}
.content-grid {
    display: grid;
    grid-template-columns: 0.8fr 1.2fr;
    gap: 1.5rem;
}
.faded-chart {
    opacity: 0.2;
}
.page-kpi-container {
    background: var(--panel-bg);
    border: 1px solid #F3F4F6;
    border-radius: 12px;
    padding: 1rem;
    display: flex;
    justify-content: space-around;
    gap: .75rem;
    margin-bottom: 1.5rem;
}
.page-kpi-item {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.page-kpi-item .icon {
    font-size: 1.5rem;
    color: var(--secondary-color);
}
.page-kpi-item .text .title {
    font-size: .92rem;
    color: var(--text-light);
}
.page-kpi-item .text .value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-dark);
}
.list-panel {
    position: relative;
    overflow: hidden;
    background: var(--panel-bg);
    border: 1px solid #F3F4F6;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
    height: 100%;
}
.list-title {
    color: #111827;
    font-weight: 800;
    font-size: 1.25rem;
    margin: 0 0 .5rem 0;
}
.list-item {
    margin-bottom: 1.5rem;
}
.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    border: 1px solid #f3f4f6;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 8px;
}
.info-row .name {
    font-size: 1rem;
    color: #111827;
    font-weight: 500;
}
.info-row .meta {
    font-size: .85rem;
    color: #6b7280;
}
.show-more-button-container {
    display: flex;
    justify-content: center;
    margin-top: 1.5rem;
}
.show-more-button-container .stButton>button {
    background: var(--primary-color);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: .55rem 2rem;
    font-size: 1rem;
    font-weight: 700;
}
.footer {
    text-align: right;
    font-size: .8rem;
    color: var(--text-light);
    margin-top: 2rem;
}
.stSelectbox > div[data-baseweb="select"] {
    min-width: 250px;
}
.framed-panel {
    border: 3px solid #333 !important;
    box-shadow: 0 8px 16px rgba(0,0,0,0.06);
    border-radius: 18px !important;
    padding: 1.8rem !important;
}
.fa-header {
    display: grid;
    grid-template-columns: 220px 1fr 140px;
    gap: 16px;
    align-items: center;
    margin: 6px 0 14px;
}

/* ====== GLOBAL HEADER (ทุกหน้าใช้ร่วมกัน) ====== */
.search-area .stTextInput > div{
    height:56px;
    border-radius:12px;
    border:1.5px solid #E5E7EB;
    background:#fff;
}
.search-area .stTextInput input{
    height:56px;
    font-size:16px;
}

/* Dropdown FA-1/FA-2/FA Dashboard Summary – ใหญ่และชัด */
.page-dropdown [data-baseweb="select"] span {
    font-size: 40px !important;
    font-weight: 800;
    color: #0F172A;
}
.page-dropdown [data-baseweb="select"] input {
    font-size: 40px !important;
    font-weight: 700;
    color: #0F172A;
}
.page-dropdown [data-baseweb="select"] div {
    font-size: 40px !important;
}

/* ปุ่มตัวกรอง – ความสูง/สไตล์เดียวกับ search */
.pill-buttons-row .stButton>button{
    height:56px;
    padding:0 18px;
    font-weight:800;
    background:#fff;
    border:2px solid #E5E7EB;
    border-radius:12px;
    margin:0 !important;
    box-shadow:none;
}
.pill-buttons-row .stButton>button:hover{
    border-color:#CBD5E1;
}

/* Extra FA header tweaks */
.fa-header .search-area .stTextInput>div{
    height:48px;
    border-radius:12px;
    border:1.5px solid #E5E7EB;
    background:#fff;
}
.fa-header .search-area input{
    height:48px;
    font-size:16px;
}
.fa-header .pill-buttons .stButton>button{
    height:48px;
    padding:0 18px;
    font-weight:800;
    background:#fff;
    border:2px solid #E5E7EB;
    border-radius:12px;
    box-shadow:none;
}
.fa-header .pill-buttons .stButton>button:hover{
    border-color:#CBD5E1;
}
    .header-logo img, .fa-header .header-logo img {
        height: 200px !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

@st.cache_data
def load_and_prepare_data(file_path: str):
    df = pd.DataFrame()
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception:
        df = pd.DataFrame({ "ให้ความเห็นชอบ FA": ["เอ บจก.", "บี บล.", "ซี ธนาคาร", "ดี ลูก บล."], "ประเภทคำขอ": ["รายใหม่", "ต่ออายุ", "รายใหม่", "ต่ออายุ"], "วันที่ยื่นคำขอ": pd.to_datetime(["2024-11-10", "2024-12-01", "2025-01-03", "2025-01-15"]), "วันที่ตรวจประวัติ": pd.to_datetime([None, "2024-12-10", None, None]), "วันที่อนุญาต": pd.to_datetime([None, None, None, None]), "วันครบอายุเห็นชอบ": pd.to_datetime(["2025-12-15", "2025-10-10", "2026-01-05", "2025-11-20"]), "dashboard": ["25%", "50%", "75%", "0%"], })
    df.columns = df.columns.str.strip()
    date_cols = ["วันครบอายุเห็นชอบ", "วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต"]
    for col in date_cols:
        if col in df.columns:
            s = pd.to_datetime(df[col], errors="coerce", format='mixed')
            mask = s.dt.year.gt(2300).fillna(False)
            s.loc[mask] = s.loc[mask] - pd.DateOffset(years=543)
            df[col] = s
            if col == "วันครบอายุเห็นชอบ":
                df["display_date"] = s.dt.strftime("%-d/%-m/%Y").fillna("N/A") if hasattr(s.dt, "strftime") else "N/A"
    if "display_date" not in df.columns: df["display_date"] = "N/A"
    df["progress_percent_raw"] = (pd.to_numeric(df.get("dashboard", "0").astype(str).str.replace("%","",regex=False), errors="coerce").fillna(0))
    df["Company (FA)"] = (df.get("ให้ความเห็นชอบ FA", pd.Series(dtype=str)).astype(str).str.split("\n", n=1).str[0].str.replace('"',"",regex=False).str.strip())
    df["ApplicationType"] = np.where(df.get("ให้ความเห็นชอบ FA", pd.Series(dtype=str)).astype(str).str.contains("เสมือนรายใหม่", na=False), "รายใหม่", df.get("ประเภทคำขอ",""))
    stage_conditions = [df.get("วันที่อนุญาต", pd.Series(index=df.index)).notna(), df.get("วันที่ตรวจประวัติ", pd.Series(index=df.index)).notna(), df.get("วันที่ยื่นคำขอ", pd.Series(index=df.index)).notna()]
    df["CurrentStage"] = np.select(stage_conditions, ["ได้รับอนุญาต","ตรวจประวัติ","ยื่นคำขอ"], default="N/A")
    return df

@st.cache_data
def load_fa2_progress_data(file_path: str):
    df = pd.DataFrame()
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception:
        df = pd.DataFrame({ "ให้ความเห็นชอบผู้ควบคุมฯ (แบบ FA-2)": ["สมชาย ใจดี", "ปนัดดา ชูชนะ", "วรรณวร งามโรจน์", "ณัฐธาวุฒิ เดชจินดา"], "ชื่อบริษัท FA": ["เอ บจก.", "บลู เวลธ์ บล.", "ธนาคาร บ้านบ้าน", "ลูก บล. ตัวอย่าง"], "progress_percent_raw": [50, 75, 75, 25], })
    df.columns = df.columns.str.strip()
    df.rename(columns={"ให้ความเห็นชอบผู้ควบคุมฯ (แบบ FA-2)": "Company (FA)"}, inplace=True)
    df["company_affiliation_text"] = df.get("ชื่อบริษัท FA", "N/A").fillna("N/A").astype(str)
    if "progress_percent_raw" not in df.columns:
        df["progress_percent_raw"] = np.random.choice([25,50,75,100], size=len(df))
    if "ApplicationType" not in df.columns:
        df["ApplicationType"] = "ทั้งหมด"
    return df

def generate_application_list_html(df_ongoing, num_items_to_show, is_fa2_list=False):
    if df_ongoing.empty: return "<div style='height:300px; display:flex; align-items:center; justify-content:center; color:#6B7280;'>ไม่มีข้อมูลที่กำลังดำเนินการ</div>"
    df_to_show = df_ongoing.head(num_items_to_show).copy()
    if "progress_percent_raw" not in df_to_show.columns: df_to_show["progress_percent_raw"] = np.random.choice([25, 50, 75, 100], size=len(df_to_show))
    def step_idx(p):
        if p >= 100: return 4;
        if p >= 75: return 3;
        if p >= 50: return 2;
        if p > 0:   return 1;
        return 0
    html = []
    for _, row in df_to_show.iterrows():
        idx = step_idx(row.get("progress_percent_raw", 0))
        bar = "<div style='position:relative; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>"
        bar += "<div style='position:absolute; top:50%; transform:translateY(-50%); left:12px; right:12px; height:4px; background:#e5e7eb; z-index:1;'></div>"
        pct = (idx/4)*100 if idx>0 else 0
        if pct>0: bar += f"<div style='position:absolute; top:50%; transform:translateY(-50%); left:12px; width:calc({pct}% - 12px); height:4px; background:var(--primary-color); z-index:1;'></div>"
        for i in range(5):
            active = i<=idx
            style = f"width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; z-index:2; background:{'var(--primary-color)' if active else '#fff'}; border:2px solid {'var(--primary-color)' if active else '#e5e7eb'};"
            icon = "<svg width='16' height='16' viewBox='0 0 16 16' fill='none' stroke='white' stroke-width='2' stroke-linecap='round'><path d='M5 8l2.5 2.5L12 6'/></svg>" if active else ""
            bar += f"<div style='{style}'>{icon}</div>"
        bar += "</div>"
        status = "<div style='font-weight:600; font-size:1rem; color:#374151; margin-bottom:4px;'>กำลังดำเนินการให้ความเห็นชอบ</div>"
        name = row.get("Company (FA)", "N/A")
        right = row.get("company_affiliation_text", "") if is_fa2_list else row.get("display_date", "")
        info = f"""<div class="info-row"><div class="name">{name}</div><div class="meta">{right}</div></div>"""
        html.append(f"<div class='list-item'>{status}{bar}{info}</div>")
    return "".join(html)

def render_controller_stats_chart():
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["มีสังกัด"], y=[518], marker_color="#60F3FE", text="518", textposition="outside"))
    fig.add_trace(go.Bar(x=["ไร้สังกัด"], y=[7], marker_color="#B2EBF2", text="7", textposition="outside"))
    fig.update_layout(
        showlegend=False, barmode="group", height=300,
        margin=dict(t=10, b=20, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", range=[0, 650]),
        xaxis=dict(showline=False),
        uniformtext_minsize=12, uniformtext_mode="hide"
    )
    chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False})
    components.html(f"""
    <style>
      .framed-panel {{
        border: 1.5px solid #E5E7EB;
        border-radius: 16px;
        background: #FFFFFF;
        padding: 16px 16px 8px 16px;
        box-shadow: 0 2px 0 rgba(0,0,0,0.02);
        max-width: 100%;
      }}
      .chart-header {{
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 700;
      }}
      .chart-legend {{
        display: flex; gap: 24px; align-items: center;
        margin: 4px 0 8px 4px; font-size: 12px; color: #111827;
      }}
      .legend-item {{ display: flex; align-items: center; gap: 8px; }}
      .legend-square {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
      .plotly-graph-div, .js-plotly-plot {{ width: 100% !important; }}
    </style>
    <div class="framed-panel">
      <h2 class="chart-header">ข้อมูลจำนวนผู้ควบคุมการปฏิบัติงาน</h2>
      <div class="chart-legend">
        <div class="legend-item"><span class="legend-square" style="background-color:#60F3FE;"></span>มีสังกัด</div>
        <div class="legend-item"><span class="legend-square" style="background-color:#B2EBF2;"></span>ไร้สังกัด</div>
      </div>
      {chart_html}
    </div>
    """, height=600, width=970, scrolling=False)

def render_fa_type_pie_chart(df):
    type_map = {
        "บล.": lambda x: x.strip() == "บล.",
        "บจก.": lambda x: x.strip() == "บจก.",
        "ธนาคาร": lambda x: "ธนาคาร" in x or "ธ." in x,
        "ลูก บล.": lambda x: "ลูก" in x and "บล." in x
    }
    if "คำนำหน้า" in df.columns:
        type_col = df["คำนำหน้า"].astype(str)
    elif "ให้ความเห็นชอบ FA" in df.columns:
        def extract_prefix(row):
            val = str(row)
            if "ธนาคาร" in val or "ธ." in val:
                return "ธนาคาร"
            elif "ลูก" in val and "บล." in val:
                return "ลูก บล."
            elif "บล." in val:
                return "บล."
            elif "บจก." in val:
                return "บจก."
            return "อื่นๆ"
        type_col = df["ให้ความเห็นชอบ FA"].apply(extract_prefix)
    else:
        return

    fa_counts = {}
    for group, func in type_map.items():
        fa_counts[group] = sum(type_col.apply(func))
    colors = ["#60F3FE", "#3AADDF", "#1060AA", "#10456F"]
    fig = go.Figure(data=[
        go.Pie(
            labels=list(fa_counts.keys()),
            values=list(fa_counts.values()),
            hole=0.7,
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            textinfo="value",
            textposition="inside",
            textfont=dict(size=14, color="white"),
            sort=False
        )
    ])
    total = sum(fa_counts.values())
    fig.update_layout(
        showlegend=False, height=300,
        margin=dict(t=10, b=10, l=10, r=10),
        annotations=[dict(text=str(total), x=0.5, y=0.5, font_size=48,
                          showarrow=False, font_color="#1F2937", yanchor="middle")],
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    chart_html = fig.to_html(full_html=False, include_plotlyjs="inline", config={"displayModeBar": False})
    components.html(f"""
    <style>
      .framed-panel {{
        border: 1.5px solid #E5E7EB;
        border-radius: 16px;
        background: #FFFFFF;
        padding: 16px 16px 8px 16px;
        box-shadow: 0 2px 0 rgba(0,0,0,0.02);
        max-width: 100%;
      }}
      .chart-header {{
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 700;
      }}
      .chart-legend {{ display: flex; gap: 24px; align-items: center; margin: 4px 0 8px 4px; font-size: 12px; color: #111827; }}
      .legend-item {{ display: flex; align-items: center; gap: 8px; }}
      .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
      .plotly-graph-div, .js-plotly-plot {{ width: 100% !important; }}
    </style>
    <div class="framed-panel">
      <h2 class="chart-header">ข้อมูลบริษัท FA แยกตามประเภท</h2>
      <div class="chart-legend">
        <div class="legend-item"><span class="legend-dot" style="background-color:#60F3FE;"></span>บล.</div>
        <div class="legend-item"><span class="legend-dot" style="background-color:#3AADDF;"></span>บจก.</div>
        <div class="legend-item"><span class="legend-dot" style="background-color:#1060AA;"></span>ธนาคาร</div>
        <div class="legend-item"><span class="legend-dot" style="background-color:#10456F;"></span>ลูก บล.</div>
      </div>
      {chart_html}
    </div>
    """, height=600, width=970, scrolling=False)

def render_fa_app_type_bar_chart(df):
    # กำหนด mapping กลุ่มประเภท FA
    categories = ["ธนาคาร", "บจก.", "บล."]
    app_types = ["รายใหม่", "ต่ออายุ"]

    # ฟังก์ชันดึงประเภทบริษัท
    def extract_fa_type(row):
        if "คำนำหน้า" in df.columns:
            val = str(row["คำนำหน้า"])
        else:
            val = str(row["ให้ความเห็นชอบ FA"])
            if "ธนาคาร" in val or "ธ." in val:
                return "ธนาคาร"
            elif "บจก." in val:
                return "บจก."
            elif "บล." in val:
                return "บล."
            else:
                return "อื่นๆ"
        if "ธนาคาร" in val or "ธ." in val:
            return "ธนาคาร"
        elif "บจก." in val:
            return "บจก."
        elif "บล." in val:
            return "บล."
        else:
            return "อื่นๆ"

    # ฟิลเตอร์เฉพาะ 3 กลุ่มหลัก
    filtered = df.copy()
    filtered["FA_TYPE"] = filtered.apply(extract_fa_type, axis=1)
    filtered = filtered[filtered["FA_TYPE"].isin(categories)]
    filtered["AppType"] = filtered["ประเภทคำขอ"].replace("", "ไม่ระบุ").fillna("ไม่ระบุ")

    # สร้าง dict สำหรับนับ
    data_count = {cat: {tp: 0 for tp in app_types} for cat in categories}
    for _, row in filtered.iterrows():
        cat = row["FA_TYPE"]
        tp = row["AppType"] if row["AppType"] in app_types else "ไม่ระบุ"
        if cat in categories and tp in app_types:
            data_count[cat][tp] += 1

    new_vals = [data_count[cat]["รายใหม่"] for cat in categories]
    renew_vals = [data_count[cat]["ต่ออายุ"] for cat in categories]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="รายใหม่", x=categories, y=new_vals,
        marker_color="#4285F4", text=new_vals, textposition="inside",
        textfont=dict(size=12, color="white")
    ))
    fig.add_trace(go.Bar(
        name="ต่ออายุ", x=categories, y=renew_vals,
        marker_color="#FBBC05", text=renew_vals, textposition="inside",
        textfont=dict(size=12, color="white")
    ))
    max_y = max(new_vals + renew_vals + [10])
    fig.update_layout(
        barmode="stack", showlegend=False, height=300,
        margin=dict(t=10, b=20, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", range=[0, max_y + 2]),
        xaxis=dict(showline=False), uniformtext_minsize=10
    )
    chart_html = fig.to_html(
        full_html=False,
        include_plotlyjs="inline",
        config={"displayModeBar": False}
    )
    components.html(f"""
    <style>
      .framed-panel {{
        border: 1.5px solid #E5E7EB;
        border-radius: 16px;
        background: #FFFFFF;
        padding: 16px 16px 8px 16px;
        box-shadow: 0 2px 0 rgba(0,0,0,0.02);
        max-width: 100%;
      }}
      .chart-header {{
        margin: 0 0 8px 0; font-size: 20px; font-weight: 700;
      }}
      .chart-legend {{
        display:flex; gap:24px; align-items:center;
        margin:4px 0 8px 4px; font-size:12px; color:#111827;
      }}
      .legend-item {{ display:flex; align-items:center; gap:8px; }}
      .legend-square {{ width:10px; height:10px; border-radius:2px; display:inline-block; }}
      .plotly-graph-div, .js-plotly-plot {{ width: 100% !important; }}
    </style>
    <div class="framed-panel">
      <h2 class="chart-header">สถิติ FA ตามประเภทคำขอ</h2>
      <div class="chart-legend">
        <div class="legend-item"><span class="legend-square" style="background-color:#4285F4;"></span>รายใหม่</div>
        <div class="legend-item"><span class="legend-square" style="background-color:#FBBC05;"></span>ต่ออายุ</div>
      </div>
      {chart_html}
    </div>
    """, height=600, width=970, scrolling=False)

def set_page(page_name):
    st.session_state.current_page = page_name

def set_filter(filter_name):
    st.session_state.active_filter = filter_name

def render_header_and_switcher():
    page_options = ["FA Dashboard Summary", "FA-1", "FA-2"]
    current = st.session_state.get("current_page", "FA Dashboard Summary")
    logo_b64 = get_image_as_base64(LOGO_PATH)
    c_dd, c_search, c_filters, c_logo = st.columns([0.18, 0.54, 0.22, 0.06])
    with c_dd:
        st.markdown('<div class="page-dropdown">', unsafe_allow_html=True)
        page = st.selectbox(
            "เลือกหน้า", page_options,
            index=page_options.index(current),
            label_visibility="collapsed",
            key="header_page_selectbox",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if page != current:
            st.session_state.current_page = page
            st.rerun()
    with c_search:
        st.markdown('<div class="search-area">', unsafe_allow_html=True)
        st.text_input(
            "Search", key="company_search",
            label_visibility="collapsed",
            placeholder="พิมพ์ชื่อบริษัทเพื่อค้นหา"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with c_filters:
        st.markdown('<div class="pill-buttons-row">', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        b1.button("ทั้งหมด", on_click=set_filter, args=("ทั้งหมด",), key="btn_all", use_container_width=True)
        b2.button("รายใหม่", on_click=set_filter, args=("รายใหม่",), key="btn_new", use_container_width=True)
        b3.button("ต่ออายุ", on_click=set_filter, args=("ต่ออายุ",), key="btn_renew", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c_logo:
        if logo_b64:
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end;">'
                f'<img src="data:image/png;base64,{logo_b64}" style="height:56px;" />'
                f'</div>',
                unsafe_allow_html=True
            )

def render_kpi_header():
    kpi_cols = st.columns(4, gap="large")
    kpis = [
        {"icon": "history", "title": "จำนวนที่อยู่ระหว่างขอความเห็นชอบ", "value": "25"},
        {"icon": "task_alt", "title": "จำนวนคำขอที่ดำเนินแล้วเสร็จ", "value": "10"},
        {"icon": "inventory_2", "title": "จำนวนบริษัท ฯ ที่ต้องเตรียมยื่นคำขอ", "value": "15"},
        {"icon": "event_available", "title": "จำนวนคำขอปี 2568 ที่ดำเนินการรวม", "value": "45"},
    ]
    for i, k in enumerate(kpis):
        with kpi_cols[i]:
            st.markdown(f"""<div class="kpi-card">
                <div class="icon"><span class="material-icons-outlined">{k['icon']}</span></div>
                <div><div class="title">{k['title']}</div><div class="value">{k['value']} <span class="suffix">บริษัท ฯ.</span></div></div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)

def render_dashboard_summary():
    render_kpi_header()
    chart_cols = st.columns(3, gap="large")
    with chart_cols[0]: render_controller_stats_chart()
    with chart_cols[1]: render_fa_type_pie_chart(df_processed)
    with chart_cols[2]: render_fa_app_type_bar_chart(df_processed)

def render_fa_page(page_type, df_processed, df_fa2):
    render_kpi_header()
    st.markdown('<div class="content-grid">', unsafe_allow_html=True)
    col1, col2 = st.columns([0.40, 0.60])
    with col1:
        st.markdown('<div class="faded-chart">', unsafe_allow_html=True)
        (render_fa_type_pie_chart(df_processed) if page_type == "FA-1" else render_controller_stats_chart())
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        title_text = f"สถานะคำขอที่กำลังดำเนินการ {page_type}"
        ses_key = f"num_{page_type.lower()}_items"
        if ses_key not in st.session_state:
            st.session_state[ses_key] = 3
        is_fa2 = (page_type == "FA-2")
        df_ongoing = df_fa2 if is_fa2 else (
            df_processed[df_processed["CurrentStage"] != "ได้รับอนุญาต"]
            .sort_values(by="วันที่ยื่นคำขอ")
        )
        search_term = st.session_state.get("company_search", "")
        if search_term:
            df_ongoing = df_ongoing[df_ongoing["Company (FA)"].str.contains(search_term, case=False, na=False)]
        active_filter = st.session_state.get("active_filter", "ทั้งหมด")
        if active_filter != "ทั้งหมด" and "ApplicationType" in df_ongoing.columns:
            df_ongoing = df_ongoing[df_ongoing["ApplicationType"] == active_filter]
        total_items  = len(df_ongoing)
        init_visible = min(st.session_state[ses_key], total_items)
        full_list_html = generate_application_list_html(
            df_ongoing, total_items, is_fa2_list=is_fa2
        )
        SCROLL_HEIGHT = 460
        IFRAME_HEIGHT = int(max(530, min(780, SCROLL_HEIGHT + 220)))
        components.html(f"""
<!doctype html>
<html lang="th"><head><meta charset="utf-8" />
<style>
  :root {{ --primary:#00A99D; --primary-color:#00A99D; --border:#E5E7EB; }}
  * {{ box-sizing:border-box; }}
  html,body{{margin:0;font-family:'Sarabun',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#FBFBFD}}
  .card{{ width:100%; border:1.5px solid var(--border); border-radius:16px; background:#FFFFFF;
          padding:18px 20px 22px; box-shadow:0 4px 14px rgba(0,0,0,.06); }}
  .title{{ margin:0 0 10px 0; font-size:24px; font-weight:800; color:#0F172A; }}
  .band{{ background:linear-gradient(90deg,#FAFAFF 0%,#FFF6E5 100%); border-radius:12px; padding:0; }}
  .scroller{{ max-height:{SCROLL_HEIGHT}px; overflow-y:auto; padding:12px; border-radius:12px; }}
  .scroller::-webkit-scrollbar{{ width:10px; }} .scroller::-webkit-scrollbar-thumb{{ background:#E5E7EB; border-radius:8px; }}
  .scroller{{ scrollbar-width:thin; scrollbar-color:#E5E7EB transparent; }}
  .list-item{{ margin-bottom:16px; }}
  .info-row{{ display:flex; justify-content:space-between; align-items:center; background:#fff; border:1px solid #F3F4F6; border-radius:8px; padding:12px 16px; margin-top:8px; }}
  .info-row .name{{ font-size:16px; color:#111827; font-weight:600; }}
  .info-row .meta{{ font-size:13px; color:#6B7280; }}
  .more-wrap{{display:flex;justify-content:center;margin-top:14px}}
  .more-btn{{ text-decoration:none; display:inline-block; border-radius:10px; padding:12px 28px; font-weight:800; background:#28BF7B; color:#fff; letter-spacing:.2px; box-shadow:0 6px 16px rgba(40,191,123,.25); cursor:pointer; }}
  .more-btn[aria-disabled="true"]{{pointer-events:none;opacity:.45}}
</style>
</head>
<body>
  <div class="card">
    <div class="title">{title_text}</div>
    <div class="band">
      <div id="listScroller" class="scroller">
        {full_list_html}
      </div>
    </div>
    <div class="more-wrap">
      <a id="moreBtn" class="more-btn" href="#" aria-disabled="{str(init_visible>=total_items).lower()}">เพิ่มเติม</a>
    </div>
  </div>
  <script>
    (function(){{
      const STEP = 3;
      const initVisible = {init_visible};
      const host = document.getElementById('listScroller');
      const items = Array.from(host.querySelectorAll('.list-item'));
      const btn = document.getElementById('moreBtn');
      function apply(n){{ items.forEach((el,i)=> el.style.display = (i<n)?'block':'none'); btn.setAttribute('aria-disabled',(n>=items.length)?'true':'false'); }}
      let current = Math.min(initVisible, items.length);
      apply(current);
      btn.addEventListener('click', function(e){{
        e.preventDefault();
        if (btn.getAttribute('aria-disabled')==='true') return;
        current = Math.min(items.length, current + STEP);
        apply(current);
        host.scrollTo({{ top: host.scrollHeight, behavior: 'smooth' }});
      }});
    }})();
  </script>
</body></html>
        """, height=530, width=1020, scrolling=False)
    st.markdown('</div>', unsafe_allow_html=True)

today = datetime.now().strftime("%d/%m/%Y")
st.markdown(
    f"""
    <style>
    .custom-footer-date {{
        position: fixed;
        right: 24px;
        bottom: 18px;
        font-weight: bold;
        font-size: 20px;
        color: #111;
        background: none;
        z-index: 9999;
        text-align: right;
    }}
    </style>
    <div class="custom-footer-date">
        ข้อมูล ณ วันที่ {today}
    </div>
    """,
    unsafe_allow_html=True
)

if "current_page" not in st.session_state:
    st.session_state.current_page = "FA Dashboard Summary"
if "active_filter" not in st.session_state:
    st.session_state.active_filter = "ทั้งหมด"
if "company_search" not in st.session_state:
    st.session_state.company_search = ""

df_processed = load_and_prepare_data("testdata/FA-1 (ปี 2565)(test).xlsx")
df_fa2_progress = load_fa2_progress_data("testdata/FA-2 (ปี 2565)(test) progress.xlsx")

render_header_and_switcher()

page = st.session_state.get("current_page", "FA Dashboard Summary")
if page == "FA Dashboard Summary":
    render_dashboard_summary()
elif page == "FA-1":
    render_fa_page("FA-1", df_processed, df_fa2_progress)
elif page == "FA-2":
    render_fa_page("FA-2", df_processed, df_fa2_progress)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="FA Application Dashboard", page_icon="📊")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Sarabun', sans-serif;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .st-emotion-cache-z5fcl4 {
        padding-top: 0rem;
    }
    .st-emotion-cache-1r6slb0, .st-emotion-cache-1kyxreq {
        border-radius: 8px;
        border: 1px solid #e9ecef;
        padding: 1.25rem;
    }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 15px 20px;
        border: 1px solid #e9ecef;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #555;
    }
    h3 {
        font-size: 1.1rem;
        font-weight: 600;
        padding-bottom: 10px;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #F0F2F6;
        color: #333;
        border: none;
    }
    .stButton>button:hover, .stButton>button:focus {
        background-color: #E6F0F8;
        color: #0068C9;
        border: none;
    }
    .stButton>button.active-button {
        background-color: #0068C9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_csv(file_path, encoding="utf-8")
    df.columns = df.columns.str.strip()
    date_cols = ["วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce") - pd.DateOffset(years=543)

    df = df.assign(
        RenewalYearBE=pd.to_numeric(df["วันครบอายุเห็นชอบ"].str.split("/").str[-1], errors="coerce").fillna(0).astype(int),
        progress_percent=pd.to_numeric(df["dashboard"].astype(str).str.replace("%", "", regex=False), errors="coerce").fillna(0),
        CompanyNameClean=df["ให้ความเห็นชอบ FA"].str.split("\n").str[0].str.replace('"', "").str.strip(),
        ProcessingDays=(datetime.now() - df["วันที่ยื่นคำขอ"]).dt.days.where(df["วันที่อนุญาต"].isna(), (df["วันที่อนุญาต"] - df["วันที่ยื่นคำขอ"]).dt.days),
        Quarter=df["วันที่ยื่นคำขอ"].dt.quarter,
    ).rename(columns={"CompanyNameClean": "Company (FA)"})
    
    df["SLA_Status"] = pd.cut(df["ProcessingDays"], bins=[-np.inf, 30, 45, np.inf], labels=["ปกติ", "ใกล้ครบกำหนด", "เกินกำหนด"])
    df["ApplicationType"] = np.where(df["ให้ความเห็นชอบ FA"].str.contains("เสมือนรายใหม่", na=False), "รายใหม่", df["ประเภทคำขอ"])
    
    stage_conditions = [df["วันที่อนุญาต"].notna(), df["วันที่ตรวจประวัติ"].notna(), df["วันที่ยื่นคำขอ"].notna()]
    stage_choices = ["ได้รับอนุญาต", "ตรวจประวัติ", "ยื่นคำขอ"]
    df["CurrentStage"] = np.select(stage_conditions, stage_choices, default="N/A")
    return df

df_processed = load_and_prepare_data("Dataset/FA-1 (ปี 2565)(Sheet1).csv")

left_col, right_col = st.columns([1, 3])

with left_col:
    st.subheader("Dashboard")
    st.selectbox("Low-Fi Dropdown", ["FA Data", "FA-1", "FA-2", "FA-3"], key="fa_data_select", label_visibility="collapsed")
    st.markdown("---")
    
    st.markdown("<h6>Status % คำขอ</h6>", unsafe_allow_html=True)
    status_pct = st.selectbox("Status % คำขอ", ["ทั้งหมด", 0, 25, 50, 75, 100], format_func=lambda x: f"{x} %" if x != "ทั้งหมด" else "ทั้งหมด", key="status_pct_filter", label_visibility="collapsed")
    
    st.markdown("<h6>สถิติ Quarter คำขอ</h6>", unsafe_allow_html=True)
    quarter = st.selectbox("สถิติ Quarter คำขอ", ["ทั้งหมด", 1, 2, 3, 4], key="quarter_filter", label_visibility="collapsed")
    
    with st.container(border=True):
        st.subheader("สถิติบริษัท FA แยกจำนวน")
        fa_type_counts = df_processed["คำนำหน้า"].value_counts()
        fig_donut_sidebar = go.Figure(data=[go.Pie(labels=fa_type_counts.index, values=fa_type_counts.values, hole=.6, marker_colors=px.colors.qualitative.Pastel)])
        fig_donut_sidebar.update_traces(textinfo='value', textposition='inside', showlegend=False)
        fig_donut_sidebar.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200, annotations=[dict(text=f'{fa_type_counts.sum()}', x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig_donut_sidebar, use_container_width=True)

        for fa_type, count in fa_type_counts.items():
            st.markdown(f"• {fa_type} ` {count} `")

df_filtered = df_processed.copy()
if status_pct != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered['progress_percent'] >= status_pct]
if quarter != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered['Quarter'] == quarter]

with right_col:
    top_filter_col1, top_filter_col2, btn_col1, btn_col2, btn_col3, date_col = st.columns([1.5, 1.5, 0.8, 0.8, 0.8, 1.2])
    
    with top_filter_col1:
        fa_company_select = st.selectbox("FA Data", ["FA Data"] + df_filtered["Company (FA)"].unique().tolist(), label_visibility="collapsed")
    with top_filter_col2:
        fa_type_select = st.selectbox("FA Type", ["FA type"] + df_filtered["คำนำหน้า"].unique().tolist(), label_visibility="collapsed")
    with date_col:
        st.date_input("Date/Time", value=None, label_visibility="collapsed")

    if fa_company_select != "FA Data":
        df_filtered = df_filtered[df_filtered["Company (FA)"] == fa_company_select]
    if fa_type_select != "FA type":
        df_filtered = df_filtered[df_filtered["คำนำหน้า"] == fa_type_select]

    if 'active_filter' not in st.session_state:
        st.session_state.active_filter = 'ทั้งหมด'

    def set_filter(filter_name):
        st.session_state.active_filter = filter_name

    with btn_col1: st.button('ทั้งหมด', on_click=set_filter, args=('ทั้งหมด',), use_container_width=True)
    with btn_col2: st.button('รายใหม่', on_click=set_filter, args=('รายใหม่',), use_container_width=True)
    with btn_col3: st.button('ต่ออายุ', on_click=set_filter, args=('ต่ออายุ',), use_container_width=True)
    
    st.components.v1.html(f"""<script>
        const buttons = Array.from(window.parent.document.querySelectorAll('.stButton button'));
        const activeFilter = '{st.session_state.active_filter}';
        buttons.forEach(btn => {{
            btn.classList.remove('active-button');
            if (btn.innerText.trim() === activeFilter) {{
                btn.classList.add('active-button');
            }}
        }});
    </script>""", height=0)

    if st.session_state.active_filter != 'ทั้งหมด':
        df_filtered = df_filtered[df_filtered['ApplicationType'] == st.session_state.active_filter]
    
    st.markdown("---")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("คำขอที่กำลังดำเนินการ", (df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum())
    kpi2.metric("ใกล้ครบกำหนด 45 วัน", (df_filtered['SLA_Status'] == 'ใกล้ครบกำหนด').sum())
    kpi3.metric("บริษัท FA. ที่จะต่ออายุปี 2568", (df_processed['RenewalYearBE'] == 2568).sum())

    vis_col1, vis_col2 = st.columns([2, 1.2])
    with vis_col1:
        with st.container(border=True):
            st.subheader("สถานะคำขอที่กำลังดำเนินการ")
            stage_counts = df_filtered[df_filtered['CurrentStage'] != 'ได้รับอนุญาต']['CurrentStage'].value_counts()
            for stage in ['ยื่นคำขอ', 'ตรวจประวัติ', 'ได้รับอนุญาต']:
                value = stage_counts.get(stage, 0)
                st.markdown(f"**{stage}**")
                progress_val = value / len(df_filtered) if not df_filtered.empty else 0
                st.progress(progress_val)

    with vis_col2:
        with st.container(border=True):
            st.subheader("ให้ความเห็นชอบ/ FA แยกจำนวน")
            sla_counts = df_filtered["SLA_Status"].value_counts()
            if not sla_counts.empty:
                fig_donut_main = go.Figure(data=[go.Pie(labels=sla_counts.index, values=sla_counts.values, hole=.6, marker_colors=['#2ECC71', '#F39C12', '#E74C3C'])])
                fig_donut_main.update_traces(textinfo='value', textposition='outside', showlegend=True)
                fig_donut_main.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=250, legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5))
                st.plotly_chart(fig_donut_main, use_container_width=True)

    with st.container(border=True):
        st.subheader(f"รายชื่อ บ. FA ที่จะต่ออายุปี 2568 ทั้งหมด/ รายละเอียดทั้งหมด")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True, column_config={
            "Company (FA)": st.column_config.TextColumn("Company (FA)", width="large"),
            "ApplicationType": "ประเภทคำขอ",
            "CurrentStage": "สถานะปัจจุบัน",
            "SLA_Status": "สถานะ SLA",
            "progress_percent": st.column_config.ProgressColumn("Progress", format="%d%%", min_value=0, max_value=100),
        }, column_order=["Company (FA)", "ApplicationType", "CurrentStage", "SLA_Status", "progress_percent"])  
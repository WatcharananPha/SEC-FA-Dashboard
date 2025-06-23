import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os

st.set_page_config(layout="wide", page_title="E-Approval Dashboard", page_icon="📊")

# --- CSS STYLES WITH ENHANCED COLOR PALETTE ---
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
    
    :root {
        --primary-color: #2563EB; /* A strong blue for highlights */
        --success-color: #16A34A; /* A rich green */
        --warning-color: #F59E0B; /* A vibrant amber/orange */
        --danger-color: #DC2626;  /* A clear red */
        --text-color-dark: #1F2937; /* Darker text for more contrast */
        --text-color-light: #4B5563;
        --background-color: #F9FAFB;
        --container-bg-color: #FFFFFF;
        --border-color: #E5E7EB;
    }

    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Sarabun', sans-serif;
        background-color: var(--background-color);
    }

    .main .block-container {
        padding: 1rem 2.5rem 2.5rem 2.5rem;
    }

    #MainMenu, footer, header {
        display: none;
    }

    .st-emotion-cache-1r6slb0, .st-emotion-cache-1kyxreq, [data-testid="stMetric"] {
        background-color: var(--container-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 1.25rem 1.5rem;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        color: var(--text-color-light);
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.25rem;
        color: var(--primary-color); 
    }

    h3 {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-color-dark);
        padding-bottom: 10px;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    h6 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-color-dark);
        margin-bottom: 0.5rem;
        padding-top: 0.5rem;
    }

    .stButton>button:not(.primary-button) {
        border-radius: 8px;
        background-color: var(--container-bg-color);
        color: var(--text-color-light);
        border: 1px solid #D1D5DB;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton>button:hover:not(.primary-button) {
        background-color: #F3F4F6;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
    }

    .stButton>button.active-button {
        background-color: #DBEAFE;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
    }
    
    .stButton>button.primary-button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button.primary-button:hover {
        background-color: #1D4ED8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_prepare_data(file_path):
    expected_cols = [
        'ลำดับที่', 'คำนำหน้า', 'ให้ความเห็นชอบ FA', 'สถิติ (Quarter)', 'ประเภทคำขอ',
        'วันที่ยื่นคำขอ', 'เลขที่หนังสือนับ 1 คำขอ/ลงวันที่', 'วันที่ตรวจประวัติ',
        'เลขที่หนังสือ', 'วันที่อนุญาต', 'วันที่ชำระเงินครั้งที่ 1 และ 2',
        'บันทึกใน ALS', 'dashboard', 'ขึ้น web', 'วันครบอายุเห็นชอบ'
    ]
    
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
        df.columns = df.columns.str.strip()
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
    except FileNotFoundError:
        st.error(f"ไม่พบไฟล์ที่: {file_path}. กรุณาตรวจสอบว่าไฟล์อยู่ในตำแหน่งที่ถูกต้อง")
        return pd.DataFrame(columns=expected_cols)

    date_cols = ["วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต", "วันครบอายุเห็นชอบ"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
            df.loc[df[col].notna(), col] = df.loc[df[col].notna(), col].apply(lambda x: x - pd.DateOffset(years=543))

    df = df.assign(
        RenewalYearBE=pd.to_numeric(df["วันครบอายุเห็นชอบ"].astype(str).str.split("/").str[-1], errors="coerce").fillna(0).astype(int),
        progress_percent=pd.to_numeric(df["dashboard"].astype(str).str.replace("%", "", regex=False), errors="coerce").fillna(0),
        CompanyNameClean=df["ให้ความเห็นชอบ FA"].astype(str).str.split("\n").str[0].str.replace('"', "").str.strip(),
        ProcessingDays=(datetime.now() - df["วันที่ยื่นคำขอ"]).dt.days.where(df["วันที่อนุญาต"].isna(), (df["วันที่อนุญาต"] - df["วันที่ยื่นคำขอ"]).dt.days),
        Quarter=pd.to_numeric(df["สถิติ (Quarter)"], errors="coerce").fillna(0).astype(int)
    ).rename(columns={"CompanyNameClean": "Company (FA)"})
    
    df["SLA_Status"] = pd.cut(df["ProcessingDays"], bins=[-np.inf, 30, 45, np.inf], labels=["ปกติ", "ใกล้ครบกำหนด", "เกินกำหนด"])
    df["ApplicationType"] = np.where(df["ให้ความเห็นชอบ FA"].str.contains("เสมือนรายใหม่", na=False), "รายใหม่", df["ประเภทคำขอ"])
    
    stage_conditions = [df["วันที่อนุญาต"].notna(), df["วันที่ตรวจประวัติ"].notna(), df["วันที่ยื่นคำขอ"].notna()]
    stage_choices = ["ได้รับอนุญาต", "ตรวจประวัติ", "ยื่นคำขอ"]
    df["CurrentStage"] = np.select(stage_conditions, stage_choices, default="N/A")
    return df

def format_thai_date(dt):
    if pd.isna(dt):
        return ""
    year_be = dt.year + 543
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    return f"{dt.day}-{thai_months[dt.month-1]}-{str(year_be)[-2:]}"

def generate_application_list_html(df_ongoing, num_items_to_show):
    items_html = []
    df_to_show = df_ongoing.head(num_items_to_show)

    for _, row in df_to_show.iterrows():
        progress = row.get('progress_percent', 0)
        active_step_index = int(progress / 25) if progress < 100 else 4
        
        stepper_items = []
        for i in range(5): # Always 5 steps
            is_active = i <= active_step_index
            circle_class = "bg-green-500 text-white" if is_active else "bg-white border-2 border-gray-400"
            icon = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>' if is_active else ''
            
            stepper_items.append(f'<div class="w-8 h-8 flex items-center justify-center rounded-full {circle_class} z-10">{icon}</div>')
            if i < 4:
                line_class = "border-green-500" if i < active_step_index else "border-gray-300"
                stepper_items.append(f'<div class="flex-auto border-t-2 border-dotted {line_class}"></div>')
        
        stepper_html = f'<div class="flex items-center my-3">{"".join(stepper_items)}</div>'
        company_name = row['Company (FA)']
        expiry_date = format_thai_date(row['วันครบอายุเห็นชอบ'])
        
        info_box_html = f"""
        <div class="bg-gray-100 p-3 rounded-lg hover:bg-gray-200 transition-colors duration-200">
            <div class="flex justify-between items-center">
                <span class="font-semibold text-sm text-gray-800">{company_name}</span>
                <span class="font-mono text-xs text-gray-600">{expiry_date}</span>
            </div>
        </div>
        """
        items_html.append(f"""
        <div class="mb-5">
            <p class="font-semibold text-gray-700 -mb-1">กำลังดำเนินการให้ความเห็นชอบ</p>
            {stepper_html}
            {info_box_html}
        </div>
        """)
    return "".join(items_html)


file_path = "Dataset/FA-1 (ปี 2565)(Sheet1).csv"
df_processed = load_and_prepare_data(file_path)

if 'active_filter' not in st.session_state:
    st.session_state.active_filter = 'ทั้งหมด'
if 'num_items_to_show' not in st.session_state:
    st.session_state.num_items_to_show = 2

# --- TOP FILTERS ---
top_c1, top_c2, space, btn_c1, btn_c2, btn_c3, date_c = st.columns([1.2, 1.2, 0.6, 0.7, 0.7, 0.7, 1])
with top_c1:
    fa_data_select = st.selectbox("FA Data", ["FA Data", "FA-1 (ปี 2565)", "FA-2", "FA-3"], label_visibility="collapsed")
with top_c2:
    st.text_input("Dataset", value=fa_data_select, label_visibility="collapsed", disabled=True)

def set_filter(filter_name):
    st.session_state.active_filter = filter_name

with btn_c1: st.button('ทั้งหมด', on_click=set_filter, args=('ทั้งหมด',), use_container_width=True, key='btn_all')
with btn_c2: st.button('รายใหม่', on_click=set_filter, args=('รายใหม่',), use_container_width=True, key='btn_new')
with btn_c3: st.button('ต่ออายุ', on_click=set_filter, args=('ต่ออายุ',), use_container_width=True, key='btn_renew')
with date_c:
    st.date_input("Date/Time", value=None, label_visibility="collapsed")

st.components.v1.html(f"""<script>
    const buttons = Array.from(window.parent.document.querySelectorAll('.stButton button:not(.primary-button)'));
    const activeFilter = '{st.session_state.active_filter}';
    buttons.forEach(btn => {{
        if (btn.innerText.trim() === activeFilter) {{ btn.classList.add('active-button'); }} 
        else {{ btn.classList.remove('active-button'); }}
    }});
</script>""", height=0)

df_filtered = df_processed.copy()
if st.session_state.active_filter != 'ทั้งหมด':
    df_filtered = df_filtered[df_filtered['ApplicationType'] == st.session_state.active_filter]

# --- MAIN LAYOUT ---
left_col, right_col = st.columns([1, 2.5])
with left_col:
    st.markdown("<h6>Status % คำขอ</h6>", unsafe_allow_html=True)
    status_pct = st.selectbox(
        "Status % Filter",
        options=["ทั้งหมด"] + sorted(df_processed['progress_percent'].unique()),
        format_func=lambda x: f"{x} %" if x != "ทั้งหมด" else "ทั้งหมด",
        key="status_pct_filter",
        label_visibility="collapsed"
    )

    st.markdown("<h6>สถิติ Quarter คำขอ</h6>", unsafe_allow_html=True)
    quarter = st.selectbox(
        "Quarter Filter",
        ["ทั้งหมด", 1, 2, 3, 4],
        key="quarter_filter",
        label_visibility="collapsed"
    )

    if status_pct != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered['progress_percent'] == status_pct]
    
    if quarter != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered['Quarter'] == quarter]

    with st.container(border=True):
        st.subheader("สถิติบริษัท FA แยกจำนวน")
        fa_type_counts = df_filtered["คำนำหน้า"].value_counts()
        color_palette_sidebar = ['#3B82F6', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899']
        fig_donut_sidebar = go.Figure(data=[go.Pie(labels=fa_type_counts.index, values=fa_type_counts.values, hole=.6, marker_colors=color_palette_sidebar)])
        fig_donut_sidebar.update_traces(textinfo='value', textposition='inside', showlegend=False, textfont_size=14)
        fig_donut_sidebar.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=240, annotations=[dict(text=f'{fa_type_counts.sum()}', x=0.5, y=0.5, font_size=24, showarrow=False, font_color="#1F2937")])
        st.plotly_chart(fig_donut_sidebar, use_container_width=True)
        for fa_type, count in fa_type_counts.items():
            st.markdown(f"• {fa_type} `{count}`")

with right_col:
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("คำขอที่กำลังดำเนินการ", (df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum())
    kpi2.metric("ใกล้ครบกำหนด 45 วัน", (df_filtered['SLA_Status'] == 'ใกล้ครบกำหนด').sum())
    kpi3.metric("บริษัท FA. ที่จะต่ออายุปี 2568", (df_processed['RenewalYearBE'] == 2568).sum())

    vis_col1, vis_col2 = st.columns([2, 1.2])
    with vis_col1:
        with st.container(border=True, height=520):
            st.subheader("สถานะคำขอที่กำลังดำเนินการ")
            df_ongoing = df_filtered[df_filtered['CurrentStage'] != 'ได้รับอนุญาต'].copy()
            html_content = generate_application_list_html(df_ongoing, st.session_state.num_items_to_show)
            st.markdown(html_content, unsafe_allow_html=True)
            if len(df_ongoing) > st.session_state.num_items_to_show:
                if st.button("เพิ่มเติม...", use_container_width=True, key="more_button", type="primary"):
                    st.session_state.num_items_to_show += 2
                    st.rerun()

    with vis_col2:
        with st.container(border=True, height=520):
            st.subheader("ให้ความเห็นชอบ/ FA แยกจำนวน")
            sla_counts = df_filtered["SLA_Status"].value_counts().reindex(["ปกติ", "ใกล้ครบกำหนด", "เกินกำหนด"]).fillna(0)
            sla_colors = ['#16A34A', '#F59E0B', '#DC2626']
            if not sla_counts.empty:
                fig_donut_main = go.Figure(data=[go.Pie(labels=sla_counts.index, values=sla_counts.values, hole=.6, marker_colors=sla_colors)])
                fig_donut_main.update_traces(textinfo='value+percent', textposition='outside', showlegend=True, sort=False)
                fig_donut_main.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=420, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_donut_main, use_container_width=True)

    with st.container(border=True):
        st.subheader(f"รายชื่อ บ. FA ที่จะต่ออายุปี 2568 ทั้งหมด/ รายละเอียดทั้งหมด")
        st.dataframe(df_filtered, use_container_width=True, height=350, hide_index=True, column_config={
            "Company (FA)": st.column_config.TextColumn("Company (FA)", width="large"),
            "ApplicationType": "ประเภทคำขอ",
            "CurrentStage": "สถานะปัจจุบัน",
            "SLA_Status": "สถานะ SLA",
            "progress_percent": st.column_config.ProgressColumn("Progress",format="%d%%",min_value=0,max_value=100),
        }, column_order=["Company (FA)", "ApplicationType", "CurrentStage", "SLA_Status", "progress_percent"])
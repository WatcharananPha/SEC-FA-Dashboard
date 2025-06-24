import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="FA Approval Dashboard", page_icon="SEC_Thailand_Logo.svg.png")

st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
    :root {
        --primary-color: #3B82F6; --primary-color-light: #DBEAFE;
        --success-color: #16A34A; --warning-color: #FBBF24; --danger-color: #EF4444;
        --text-color-dark: #1F2937; --text-color-light: #6B7280; --text-color-header: #374151;
        --background-color: #F9FAFB; --container-bg-color: #FFFFFF; --border-color: #E5E7EB;
    }
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Sarabun', sans-serif; background-color: var(--background-color);
    }
    #MainMenu, footer, header { display: none; }
    .main .block-container { padding: 1.5rem 2.5rem 2.5rem 2.5rem; }
    .st-emotion-cache-1r6slb0, .st-emotion-cache-1kyxreq, [data-testid="stMetric"], .st-emotion-cache-1wivapv, .st-emotion-cache-1v0mbdj {
        background-color: var(--container-bg-color); border: 1px solid var(--border-color);
        border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        padding: 1.25rem 1.5rem;
    }
    h3 { font-size: 1.1rem; font-weight: 600; color: var(--text-color-header);
        padding-bottom: 0.75rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); }
    .filter-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
    .filter-header h6 { font-size: 0.95rem; font-weight: 600; color: var(--text-color-dark); margin-bottom: 0; }
    .reset-button {
        font-size: 0.8rem; color: var(--text-color-light); background-color: #F3F4F6;
        border: 1px solid #E5E7EB; border-radius: 6px; padding: 2px 8px; cursor: pointer;
    }
    .reset-button:hover { background-color: #E5E7EB; }
    .stButton>button:not(.primary-button) {
        border-radius: 9999px; background-color: #E5E7EB; color: var(--text-color-light);
        border: none; font-weight: 600; transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover:not(.primary-button) { background-color: #D1D5DB; }
    .stButton>button.active-button {
        background-color: var(--primary-color-light); color: var(--primary-color);
    }
    .stButton>button.primary-button {
        background-color: var(--primary-color); color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    .stButton>button.primary-button:hover { background-color: #1D4ED8; }
    [data-testid="stCheckbox"] p { font-size: 14px; color: var(--text-color-dark); }
    .kpi-metric { text-align: left; }
    .kpi-title { font-size: 0.9rem; font-weight: 600; color: var(--text-color-light); display: flex; align-items: center; gap: 8px; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: var(--text-color-header); margin-top: 4px; }
    .kpi-icon { background-color: var(--primary-color-light); border-radius: 8px; padding: 6px; display: flex; align-items: center; justify-content: center; }
    .kpi-icon svg { width: 20px; height: 20px; color: var(--primary-color); }
    div[data-testid="stButton-ResetStatus"], div[data-testid="stButton-ResetQuarter"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_excel(file_path, engine='openpyxl')
    df.columns = df.columns.str.strip()

    date_cols = ["วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต", "วันครบอายุเห็นชอบ"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
        conversion_mask = df[col].notna() & (df[col].dt.year > 2300)
        df.loc[conversion_mask, col] = df.loc[conversion_mask, col] - pd.DateOffset(years=543)

    df['progress_percent_raw'] = pd.to_numeric(df["dashboard"].astype(str).str.replace("%", "", regex=False), errors="coerce").fillna(0)
    df['progress_group'] = np.select(
        [df['progress_percent_raw'] == 0, df['progress_percent_raw'] <= 25, df['progress_percent_raw'] <= 50, df['progress_percent_raw'] <= 75, df['progress_percent_raw'] > 75],
        [0, 25, 50, 75, 100], default=0
    )
    
    df = df.assign(
        RenewalYearBE=(df["วันครบอายุเห็นชอบ"].dt.year + 543).fillna(0).astype(int),
        CompanyNameClean=df["ให้ความเห็นชอบ FA"].astype(str).str.split("\n", n=1).str[0].str.replace('"', '', regex=False).str.strip(),
        ProcessingDays=(datetime.now() - df["วันที่ยื่นคำขอ"]).dt.days.where(df["วันที่อนุญาต"].isna(), (df["วันที่อนุญาต"] - df["วันที่ยื่นคำขอ"]).dt.days),
        Quarter=pd.to_numeric(df["สถิติ (Quarter)"], errors="coerce").fillna(0).astype(int),
        ApplicationType=np.where(df["ให้ความเห็นชอบ FA"].str.contains("เสมือนรายใหม่", na=False), "รายใหม่", df["ประเภทคำขอ"])
    ).rename(columns={"CompanyNameClean": "Company (FA)"})
    
    df["SLA_Status"] = pd.cut(df["ProcessingDays"], bins=[-np.inf, 30, 45, np.inf], labels=["ปกติ", "ใกล้ครบกำหนด", "เกินกำหนด"])
    
    stage_conditions = [df["วันที่อนุญาต"].notna(), df["วันที่ตรวจประวัติ"].notna(), df["วันที่ยื่นคำขอ"].notna()]
    stage_choices = ["ได้รับอนุญาต", "ตรวจประวัติ", "ยื่นคำขอ"]
    df["CurrentStage"] = np.select(stage_conditions, stage_choices, default="N/A")
    
    return df

def format_thai_date(dt):
    if pd.isna(dt): return ""
    year_be = dt.year + 543
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    return f"{dt.day}-{thai_months[dt.month-1]}-{str(year_be)[-2:]}"

class StepperBar:
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0
        self.active_color = 'var(--primary-color)'
        self.completed_color = 'var(--success-color)'
        self.inactive_color = 'var(--border-color)'
        self.text_color = 'var(--text-color-light)'

    def set_current_step(self, step):
        self.current_step = step

    def display(self):
        html_parts = [f"<div style='display:flex; align-items:center; width:100%; font-family: Sarabun, sans-serif;'>"]
        for i, step_label in enumerate(self.steps):
            if i < self.current_step:
                circle_bg, border, text_color = self.completed_color, self.completed_color, self.completed_color
                content = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='white' width='14' height='14'><path fill-rule='evenodd' d='M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z' clip-rule='evenodd'></path></svg>"
            elif i == self.current_step:
                circle_bg, border, text_color = self.active_color, self.active_color, self.active_color
                content = ""
            else:
                circle_bg, border, text_color = 'white', self.inactive_color, self.text_color
                content = ""
            
            html_parts.append(f"""
            <div style='text-align:center;'>
                <div style='width:24px; height:24px; border-radius:50%; background-color:{circle_bg}; border: 2px solid {border}; 
                            display:flex; align-items:center; justify-content:center; margin: 0 auto 4px auto;'>{content}</div>
                <div style='font-size:12px; font-weight: 600; color:{text_color};'>{step_label}</div>
            </div>""")

            if i < len(self.steps) - 1:
                line_color = self.completed_color if i < self.current_step else self.inactive_color
                html_parts.append(f"<div style='flex-grow:1; height:2px; background-color:{line_color}; transform:translateY(-12px);'></div>")
                
        html_parts.append("</div>")
        return "".join(html_parts)

def generate_application_list_html(df_ongoing, num_items_to_show, total_items):
    df_to_show = df_ongoing.head(num_items_to_show)
    if df_to_show.empty:
        return "<div style='height: 300px; display: flex; align-items: center; justify-content: center;'><p class='text-center text-gray-500'>ไม่มีข้อมูลที่กำลังดำเนินการ</p></div>"

    html_parts = ["<div class='flex flex-col space-y-8'>"]
    steps = ['ยื่นคำขอ', 'พิจารณา', 'อนุมัติ']
    stepper = StepperBar(steps=steps)

    for _, row in df_to_show.iterrows():
        progress = row['progress_percent_raw']
        current_step_index = 1 if 0 < progress < 100 else 2 if progress >= 100 else 0
        stepper.set_current_step(current_step_index)
        
        stepper_html = stepper.display()
        expiry_date_formatted = format_thai_date(row['วันครบอายุเห็นชอบ'])
        
        info_box_html = f"""
        <div class="bg-gray-50 border border-gray-200 p-3 rounded-lg mt-4">
            <div class="flex justify-between items-center">
                <span class="font-semibold text-sm text-gray-800">{row['Company (FA)']}</span>
                <span class="font-mono text-sm text-gray-600">{expiry_date_formatted}</span>
            </div>
        </div>"""
        html_parts.append(f"<div>{stepper_html}{info_box_html}</div>")
        
    html_parts.append("</div>")
    
    if total_items > num_items_to_show:
        html_parts.append("""
        <a href="?show_more=true" target="_self" style="display: block; text-decoration: none; margin-top: 1.5rem;">
            <div style="width: 100%; background-color: var(--primary-color); color: white; border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; text-align: center;">
                เพิ่มเติม...
            </div>
        </a>""")
        
    return "".join(html_parts)

def kpi_metric(title, value, icon_svg):
    st.markdown(f"""
    <div class="kpi-metric">
        <div class="kpi-title"><span class="kpi-icon">{icon_svg}</span><span>{title}</span></div>
        <div class="kpi-value">{value}</div>
    </div>""", unsafe_allow_html=True)

df_processed = load_and_prepare_data("testdata/FA-1 (ปี 2565)(test).xlsx")

if 'active_filter' not in st.session_state: st.session_state.active_filter = 'ทั้งหมด'
if 'num_items_to_show' not in st.session_state: st.session_state.num_items_to_show = 2
if 'status_filters' not in st.session_state: st.session_state.status_filters = {0: False, 25: False, 50: False, 75: False, 100: False}
if 'quarter_filters' not in st.session_state: st.session_state.quarter_filters = {1: False, 2: False, 3: False, 4: False, 'all': True}

top_c1, top_c2, space, btn_c1, btn_c2, btn_c3, date_c = st.columns([1.5, 2, 0.5, 0.8, 0.8, 0.8, 1.5])
with top_c1:
    fa_data_select = st.selectbox("FA Data", ["FA Data", "FA-1 (ปี 2565)"], index=1, label_visibility="collapsed")
with top_c2:
    st.text_input("Dataset", value=fa_data_select, label_visibility="collapsed", disabled=True)
def set_filter(filter_name): st.session_state.active_filter = filter_name
with btn_c1: st.button('ทั้งหมด', on_click=set_filter, args=('ทั้งหมด',), use_container_width=True)
with btn_c2: st.button('รายใหม่', on_click=set_filter, args=('รายใหม่',), use_container_width=True)
with btn_c3: st.button('ต่ออายุ', on_click=set_filter, args=('ต่ออายุ',), use_container_width=True)
with date_c:
    st.date_input("Date/Time", value=None, label_visibility="collapsed")

st.components.v1.html(f"""<script>
    const buttons = window.parent.document.querySelectorAll('.stButton button:not(.primary-button)');
    buttons.forEach(btn => {{
        btn.classList.remove('active-button');
        if (btn.innerText.trim() === '{st.session_state.active_filter}') {{ btn.classList.add('active-button'); }}
    }});
</script>""", height=0)

st.markdown("<br>", unsafe_allow_html=True)
left_col, right_col = st.columns([1, 2.8])

with left_col: 
    def reset_status_filters():
        st.session_state.status_filters = {k: False for k in st.session_state.status_filters}
    st.markdown('<div class="filter-header"><h6>Status % คำขอ</h6><button class="reset-button" onclick="window.parent.document.querySelector(\'div[data-testid=\\"stButton-ResetStatus\\"] button\').click()">Reset</button></div>', unsafe_allow_html=True)
    st.session_state.status_filters[0] = st.checkbox('ดำเนินการ 0 %', value=st.session_state.status_filters.get(0, False), key='status_0')
    st.session_state.status_filters[25] = st.checkbox('ดำเนินการ 25 %', value=st.session_state.status_filters.get(25, False), key='status_25')
    st.session_state.status_filters[50] = st.checkbox('ดำเนินการ 50 %', value=st.session_state.status_filters.get(50, False), key='status_50')
    st.session_state.status_filters[75] = st.checkbox('ดำเนินการ 75 %', value=st.session_state.status_filters.get(75, False), key='status_75')
    st.session_state.status_filters[100] = st.checkbox('ดำเนินการเสร็จสิ้น', value=st.session_state.status_filters.get(100, False), key='status_100')
    st.button("ResetStatus", on_click=reset_status_filters, key="ResetStatus")

    def reset_quarter_filters():
        st.session_state.quarter_filters = {k: False for k in st.session_state.quarter_filters}
        st.session_state.quarter_filters['all'] = True
    st.markdown('<div class="filter-header" style="margin-top: 1.5rem;"><h6>สถิติแบ่งตาม Quarter</h6><button class="reset-button" onclick="window.parent.document.querySelector(\'div[data-testid=\\"stButton-ResetQuarter\\"] button\').click()">Reset</button></div>', unsafe_allow_html=True)
    st.session_state.quarter_filters[1] = st.checkbox('Quarter 1', value=st.session_state.quarter_filters.get(1, False), key='q1')
    st.session_state.quarter_filters[2] = st.checkbox('Quarter 2', value=st.session_state.quarter_filters.get(2, False), key='q2')
    st.session_state.quarter_filters[3] = st.checkbox('Quarter 3', value=st.session_state.quarter_filters.get(3, False), key='q3')
    st.session_state.quarter_filters[4] = st.checkbox('Quarter 4', value=st.session_state.quarter_filters.get(4, False), key='q4')
    st.session_state.quarter_filters['all'] = st.checkbox('ทั้งหมด', value=st.session_state.quarter_filters.get('all', True), key='q_all')
    st.button("ResetQuarter", on_click=reset_quarter_filters, key="ResetQuarter")

    df_filtered = df_processed.copy()
    if st.session_state.active_filter != 'ทั้งหมด':
        df_filtered = df_filtered[df_filtered['ApplicationType'] == st.session_state.active_filter]
    
    selected_statuses = [k for k, v in st.session_state.status_filters.items() if v]
    if selected_statuses:
        df_filtered = df_filtered[df_filtered['progress_group'].isin(selected_statuses)]
    
    if not st.session_state.quarter_filters.get('all', True):
        selected_quarters = [k for k, v in st.session_state.quarter_filters.items() if v and k != 'all']
        if selected_quarters:
            df_filtered = df_filtered[df_filtered['Quarter'].isin(selected_quarters)]

    with st.container(border=True): 
        st.subheader("สถิติบริษัท FA แยกจำนวน")
        fa_type_counts = df_filtered["คำนำหน้า"].value_counts()
        if not fa_type_counts.empty:
            colors = ['#FBBF24', '#60A5FA', '#34D399', '#A78BFA']
            fig = go.Figure(data=[go.Pie(labels=fa_type_counts.index, values=fa_type_counts.values, hole=.7,
                marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
                hoverinfo='label+value', textinfo='value', textposition='inside', showlegend=False, textfont_size=14)])
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=220,
                annotations=[dict(text=f'{fa_type_counts.sum()}', x=0.5, y=0.5, font_size=30, showarrow=False, font_color="#1F2937")])
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            for (fa_type, count), color in zip(fa_type_counts.items(), colors):
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                         <span style="height: 10px; width: 10px; background-color: {color}; border-radius: 50%;"></span>
                         <span style="font-size: 14px;">{fa_type}</span>
                    </div>
                    <span style="font-size: 14px; font-weight: 600; color: var(--text-color-light);">{count}</span>
                </div>""", unsafe_allow_html=True)

with right_col:
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1: kpi_metric("คำขอที่กำลังดำเนินการ", (df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum(), '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C6.34 4.016 5.25 5.282 5.25 6.608v11.285c0 1.326 1.09 2.592 2.421 2.592h8.108a2.25 2.25 0 002.25-2.25v-4.874c0-.67-.283-1.278-.744-1.693l-4.16-4.162" /></svg>')
    with kpi2:
        today = pd.to_datetime(datetime.now().date())
        due_soon_count = (df_filtered["วันครบอายุเห็นชอบ"].notna() & (df_filtered["วันครบอายุเห็นชอบ"] <= today + pd.Timedelta(days=45))).sum()
        kpi_metric("ใกล้ครบกำหนด 45 วัน", due_soon_count, '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>')
    with kpi3: kpi_metric("บริษัท FA. ที่จะต่ออายุปี 2568", (df_processed['RenewalYearBE'] == 2568).sum(), '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21m0 0h4.5V3.545M12.75 21h7.5V10.75M2.25 21h1.5m18 0h-18M2.25 9l4.5-1.636M18.75 3l-1.5.545m0 6.205l3 1m-3-1l-3-1m-3 1l-3 1" /></svg>')

    vis_col1, vis_col2 = st.columns([1.8, 1.2])
    with vis_col1:
        with st.container(border=True, height=520):
            st.subheader("สถานะคำขอที่กำลังดำเนินการ")
            df_ongoing = df_filtered[df_filtered['CurrentStage'] != 'ได้รับอนุญาต'].sort_values(by="วันที่ยื่นคำขอ")
            html_content = generate_application_list_html(df_ongoing, st.session_state.num_items_to_show, len(df_ongoing))
            st.markdown(html_content, unsafe_allow_html=True)

    with vis_col2:
        with st.container(border=True, height=520):
            st.subheader("สถิติ FA ตามประเภทคำขอ")
            if not df_filtered.empty:
                chart_data = df_filtered.groupby(['คำนำหน้า', 'ApplicationType'], observed=True).size().unstack(fill_value=0)
                if not chart_data.empty:
                    fig = go.Figure()
                    colors = {'รายใหม่': '#3B82F6', 'ต่ออายุ': '#FBBF24'}
                    app_types_in_order = [col for col in ['ต่ออายุ', 'รายใหม่'] if col in chart_data.columns]
                    for app_type in app_types_in_order:
                        fig.add_trace(go.Bar(x=chart_data.index, y=chart_data[app_type], name=app_type, marker_color=colors.get(app_type)))
                    fig.update_layout(barmode='stack', bargap=0.2, margin=dict(l=10, r=10, t=50, b=10), height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E5E7EB'), font=dict(family='Sarabun, sans-serif'))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div style='height: 380px; display: flex; align-items: center; justify-content: center;'><p class='text-center text-gray-500'>ไม่มีข้อมูล</p></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 380px; display: flex; align-items: center; justify-content: center;'><p class='text-center text-gray-500'>ไม่มีข้อมูล</p></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader(f"รายชื่อ บ. FA ที่จะต่ออายุปี 2568 ทั้งหมด/ รายละเอียดทั้งหมด")
        df_display = df_processed if st.session_state.active_filter == 'ทั้งหมด' else df_filtered
        st.dataframe(df_display, use_container_width=True, height=350, hide_index=True, column_config={
            "Company (FA)": st.column_config.TextColumn("Company (FA)", width="large"),
            "คำนำหน้า": "คำนำหน้า",
            "ApplicationType": "ประเภทคำขอ",
            "progress_percent_raw": st.column_config.ProgressColumn("Progress", format="%d%%", min_value=0, max_value=100),
        }, column_order=["Company (FA)", "คำนำหน้า", "ApplicationType", "progress_percent_raw"])
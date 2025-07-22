import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64
from pathlib import Path

LOGO_PATH = "SEC_Thailand_Logo.svg.png"

st.set_page_config(layout="wide", page_title="FA Approval Dashboard", page_icon=LOGO_PATH)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
    :root {
        --primary-color: #3B82F6;
        --primary-color-light: #DBEAFE;
        --success-color: #16A34A;
        --warning-color: #FBBF24;
        --danger-color: #EF4444;
        --text-color-dark: #1F2937;
        --text-color-light: #6B7280;
        --text-color-header: #374151;
        --background-color: #F0F2F5;
        --container-bg-color: #FFFFFF;
        --border-color: #E5E7EB;
        --card-shadow: 0 2px 8px 0 rgba(31,41,55,0.06);
    }
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Sarabun', sans-serif;
        background-color: var(--background-color);
        background-image: linear-gradient(135deg, #e6f7ff 0%, #f3f4f6 50%, #fffbe6 100%);
        background-attachment: fixed;
    }
    #MainMenu, footer, header {
        display: none;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    div[data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    h6 {
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
    }
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    .kpi-metric {
        text-align: left;
        background-color: var(--container-bg-color);
        border: 1.5px solid var(--border-color);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        box-shadow: var(--card-shadow);
        margin-bottom: 1rem;
    }
    h3, h6 {
        color: var(--text-color-header);
        font-weight: 600;
    }
    h3 {
        font-size: 1.1rem;
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    h6 {
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    .kpi-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-color-light);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-color-header);
        margin-top: 4px;
    }
    .kpi-icon {
        background-color: var(--primary-color-light);
        border-radius: 10px;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .kpi-icon svg {
        width: 20px;
        height: 20px;
        color: var(--primary-color);
    }
</style> """, unsafe_allow_html=True)

@st.cache_data
def load_controller_data(file_path):
    df_controller = pd.read_excel(file_path, engine='openpyxl')
    df_controller.columns = df_controller.columns.str.strip()
    return df_controller

@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_excel(file_path, engine='openpyxl')
    df.columns = df.columns.str.strip()
    if 'วันครบอายุเห็นชอบ' in df.columns:
        raw_dates = df['วันครบอายุเห็นชอบ'].copy()
        def format_date_for_display(val):
            if pd.isna(val):
                return 'N/A'
            if isinstance(val, (datetime, pd.Timestamp)):
                return f"{val.day}/{val.month}/{val.year}"
            return str(val)
        df['display_date'] = raw_dates.apply(format_date_for_display)
    else:
        df['display_date'] = 'N/A'
    date_cols = ["วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต", "วันครบอายุเห็นชอบ"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
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

@st.cache_data
def load_fa2_progress_data(file_path):
    df = pd.read_excel(file_path, engine='openpyxl')
    df.columns = df.columns.str.strip()
    df.rename(columns={'ให้ความเห็นชอบผู้ควบคุมฯ (แบบ FA-2)': 'Company (FA)'}, inplace=True)
    if 'ชื่อบริษัท FA' in df.columns:
        df['company_affiliation_text'] = df['ชื่อบริษัท FA'].fillna('N/A').astype(str)
    else:
        df['company_affiliation_text'] = 'รายชื่อบริษัท "N/A"'
    df["display_date"] = ""
    return df

def generate_application_list_html_optimized(df_ongoing, num_items_to_show, total_items):
    if df_ongoing.empty:
        return "<div style='height: 300px; display: flex; align-items: center; justify-content: center;'><p class='text-center text-gray-500'>ไม่มีข้อมูลที่กำลังดำเนินการ</p></div>"
    df_to_show = df_ongoing.head(num_items_to_show).copy()
    if "dashboard" in df_to_show.columns:
        df_to_show['progress_percent_raw'] = pd.to_numeric(df_to_show["dashboard"].astype(str).str.replace("%", "", regex=False), errors="coerce").fillna(0)
    else:
        df_to_show['progress_percent_raw'] = 0
    def get_step_index(progress):
        if progress >= 100: return 4
        elif progress >= 75: return 3
        elif progress >= 50: return 2
        elif progress > 0: return 1
        else: return 0
    df_to_show['step_index'] = df_to_show['progress_percent_raw'].apply(get_step_index)
    df_to_show = df_to_show.reset_index(drop=True)
    df_to_show.rename(columns={'Company (FA)': 'Company_FA'}, inplace=True)
    is_fa2_list = 'company_affiliation_text' in df_to_show.columns
    html_items = []
    for row in df_to_show.itertuples(index=False):
        progress_bar_container_style = "position:relative; display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;"
        track_line_style = "position:absolute; top:50%; transform: translateY(-50%); left:12px; right:12px; height:4px; background:#e5e7eb; z-index:1;"
        track_line_html = f"<div style='{track_line_style}'></div>"
        progress_percent = (row.step_index / 4) * 100 if row.step_index > 0 else 0
        progress_line_style = f"position:absolute; top:50%; transform: translateY(-50%); left:12px; width:calc({progress_percent}% - {12 * (progress_percent/100)}px); height:4px; background:#22c55e; z-index:1;"
        progress_line_html = f"<div style='{progress_line_style}'></div>" if progress_percent > 0 else ""
        circles_html = ""
        for i in range(5):
            is_active = i <= row.step_index
            if is_active:
                style = "width:24px; height:24px; border-radius:50%; background:#22c55e; display:flex; align-items:center; justify-content:center; z-index:2;"
                icon = "<svg width='16' height='16' viewBox='0 0 16 16'><path d='M5 8l2.5 2.5L12 6' stroke='white' stroke-width='2' fill='none' stroke-linecap='round'/></svg>"
                circles_html += f"<div style='{style}'>{icon}</div>"
            else:
                style = "width:24px; height:24px; border-radius:50%; background:#fff; border:2px solid #e5e7eb; z-index:2;"
                circles_html += f"<div style='{style}'></div>"
        step_html = f"<div style='{progress_bar_container_style}'>{track_line_html}{progress_line_html}{circles_html}</div>"
        status_text = "<div style='color:#374151;font-weight:600;font-size:15px;margin-bottom:4px;'>กำลังดำเนินการให้ความเห็นชอบ</div>"
        if is_fa2_list:
            right_content = getattr(row, 'company_affiliation_text', '')
        else:
            right_content = getattr(row, 'display_date', '')
        info_box_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#f9fafb; border-radius:8px; padding:12px 16px; margin-bottom:8px; border: 1px solid #f3f4f6;">
            <div style="font-size:15px; color:#111827; font-weight:500;">{row.Company_FA}</div>
            <div style="font-size:13px; color:#6b7280;">{right_content}</div>
        </div>
        """
        html_items.append(f"<div style='margin-bottom:18px'>{step_html}{status_text}{info_box_html}</div>")
    list_html = "".join(html_items)
    return f"<div style='display:flex;flex-direction:column;'>{list_html}</div>"

def kpi_metric(title, value, icon_svg):
    st.markdown(f"""
    <div class="kpi-metric">
        <div class="kpi-title"><span class="kpi-icon">{icon_svg}</span><span>{title}</span></div>
        <div class="kpi-value">{value}</div>
    </div>""", unsafe_allow_html=True)

df_processed = load_and_prepare_data("testdata/FA-1 (ปี 2565)(test).xlsx")
df_controller = load_controller_data("testdata/FA-2 (ปี 2565)(test).xlsx")
df_fa2_progress = load_fa2_progress_data("testdata/FA-2 (ปี 2565)(test) progress.xlsx")

if 'active_filter' not in st.session_state: st.session_state.active_filter = 'ทั้งหมด'
if 'num_items_to_show' not in st.session_state: st.session_state.num_items_to_show = 2
if 'num_fa2_items_to_show' not in st.session_state: st.session_state.num_fa2_items_to_show = 3

logo_col, search_col, space_col, btn_c1, btn_c2, btn_c3 = st.columns([1.5, 5.5, 1, 1, 1, 1])

with logo_col:
    if Path(LOGO_PATH).is_file():
        b64_logo = base64.b64encode(Path(LOGO_PATH).read_bytes()).decode()
        st.markdown(f'<img src="data:image/png;base64,{b64_logo}" style="height: 120px;">', unsafe_allow_html=True)

with search_col:
    company_search = st.text_input("ค้นหาชื่อบริษัท FA...", placeholder="พิมพ์ชื่อบริษัทเพื่อค้นหา", label_visibility="collapsed")

def set_filter(filter_name):
    st.session_state.active_filter = filter_name

with btn_c1: st.button('ทั้งหมด', on_click=set_filter, args=('ทั้งหมด',), use_container_width=True)
with btn_c2: st.button('รายใหม่', on_click=set_filter, args=('รายใหม่',), use_container_width=True)
with btn_c3: st.button('ต่ออายุ', on_click=set_filter, args=('ต่ออายุ',), use_container_width=True)

left_col, right_col = st.columns([1, 2.8])

df_filtered = df_processed.copy()
if company_search:
    df_filtered = df_filtered[df_filtered['Company (FA)'].str.contains(company_search, case=False, na=False)]

with left_col:
    st.markdown("<h6 style='color: #000;'>Status % คำขอ</h6>", unsafe_allow_html=True)
    status_options = {
        'ดำเนินการ 0 %': 0, 'ดำเนินการ 25 %': 25, 'ดำเนินการ 50 %': 50,
        'ดำเนินการ 75 %': 75, 'ดำเนินการเสร็จสิ้น': 100
    }
    selected_labels = st.multiselect(
        'Filter by Status %', options=list(status_options.keys()),
        placeholder="เลือกสถานะคำขอ...", label_visibility="collapsed"
    )
    selected_status_values = [status_options[label] for label in selected_labels]
    st.markdown("<h6 style='color: #000;'>สถิติแบ่งตาม Quarter</h6>", unsafe_allow_html=True)
    
    quarter_options = {'ทั้งหมด': 'all', 'Quarter 1': 1, 'Quarter 2': 2, 'Quarter 3': 3, 'Quarter 4': 4}
    selected_labels_quarter = st.multiselect(
        'Filter by Quarter', options=list(quarter_options.keys()),
        placeholder="เลือก Quarter...", label_visibility="collapsed"
    )
    selected_quarter_values = [quarter_options[label] for label in selected_labels_quarter]
    is_all_selected = 'all' in selected_quarter_values or not selected_quarter_values
    if st.session_state.active_filter != 'ทั้งหมด':
        df_filtered = df_filtered[df_filtered['ApplicationType'] == st.session_state.active_filter]
    if selected_status_values:
        df_filtered = df_filtered[df_filtered['progress_group'].isin(selected_status_values)]
    if not is_all_selected:
        df_filtered = df_filtered[df_filtered['Quarter'].isin([q for q in selected_quarter_values if q != 'all'])]
    with st.container(border=True):
        st.subheader("สถิติบริษัท FA แยกจำนวน")
        fa_type_counts = df_filtered["คำนำหน้า"].value_counts()
        if not fa_type_counts.empty:
            colors = ['#FBBF24', '#60A5FA', '#34D399', '#A78BFA']
            fig = go.Figure(data=[go.Pie(labels=fa_type_counts.index, values=fa_type_counts.values, hole=.7, marker=dict(colors=colors, line=dict(color='#ffffff', width=2)), hoverinfo='label+value', textinfo='value', textposition='inside', textfont_size=14)])
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), width=400, height=320, annotations=[dict(text=f'{fa_type_counts.sum()}', x=0.5, y=0.5, font_size=30, showarrow=False, font_color="#1F2937")])
            st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
            for (fa_type, count), color in zip(fa_type_counts.items(), colors):
                st.markdown(f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;"><div style="display: flex; align-items: center; gap: 8px;"><span style="height: 10px; width: 10px; background-color: {color}; border-radius: 50%;"></span><span style="font-size: 14px;">{fa_type}</span></div><span style="font-size: 14px; font-weight: 600; color: var(--text-color-light);">{count}</span></div>""", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("สถิติจำนวนผู้ควบคุม")
        if not df_controller.empty and "คำนำหน้า" in df_controller.columns:
            count_no_affiliation = (df_controller["คำนำหน้า"] == "ไร้สังกัด").sum()
            count_with_affiliation = (df_controller["คำนำหน้า"] != "ไร้สังกัด").sum()
            controller_counts = pd.Series({"มีสังกัด": count_with_affiliation, "ไร้สังกัด": count_no_affiliation})
            colors = ['#1f77b4', '#ff7f0e']
            fig_controller = go.Figure(go.Bar(x=controller_counts.values, y=controller_counts.index, orientation='h', marker_color=colors, text=controller_counts.values, textposition='inside', insidetextanchor='end', textfont=dict(color='black', size=14)))
            fig_controller.update_layout(width=400, height=150, margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, color='black', tickfont=dict(color='black')), yaxis=dict(autorange="reversed", color='black', tickfont=dict(color='black')), showlegend=False)
            st.plotly_chart(fig_controller, use_container_width=False, config={'displayModeBar': False})
            col1, col2 = st.columns(2)
            with col1: st.metric(label="มีสังกัด", value=f"{count_with_affiliation} คน")
            with col2: st.metric(label="ไร้สังกัด", value=f"{count_no_affiliation} คน")

with right_col:
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1: kpi_metric("คำขอปัจจุบัน", (df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum(), '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C6.34 4.016 5.25 5.282 5.25 6.608v11.285c0 1.326 1.09 2.592 2.421 2.592h8.108a2.25 2.25 0 002.25-2.25v-4.874c0-.67-.283-1.278-.744-1.693l-4.16-4.162" /></svg>')
    with kpi2:
        today = pd.to_datetime(datetime.now().date())
        due_soon_count = (df_filtered["วันครบอายุเห็นชอบ"].notna() & (df_filtered["วันครบอายุเห็นชอบ"] <= today + pd.Timedelta(days=45))).sum()
        kpi_metric("คำขอที่ดำเนินการแล้วเสร็จ", due_soon_count, '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 0 11-18 0 9 9 0 0118 0z" /></svg>')
    with kpi3: kpi_metric("จำนวนบริษัท FA รวมของปี 2568", df_processed['ลำดับที่'].count(), '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21m0 0h4.5V3.545M12.75 21h7.5V10.75M2.25 21h1.5m18 0h-18M2.25 9l4.5-1.636M18.75 3l-1.5.545m0 6.205l3 1m-3-1l-3-1m-3 1l-3 1" /></svg>')
    vis_col1, vis_col2 = st.columns([1.2, 1.0])
    with vis_col1:
        with st.container(height=650):
            st.subheader("สถานะคำขอที่กำลังดำเนินการ FA-1")
            df_ongoing = df_filtered[df_filtered['CurrentStage'] != 'ได้รับอนุญาต'].sort_values(by="วันที่ยื่นคำขอ")
            html_content = generate_application_list_html_optimized(
                df_ongoing, st.session_state.num_items_to_show, len(df_ongoing)
            )
            st.markdown(html_content, unsafe_allow_html=True)
            if len(df_ongoing) > st.session_state.num_items_to_show:
                st.markdown('<div id="custom-view-more-btn-wrapper" style="display:flex; justify-content:center; margin-top:10px; margin-bottom:10px;">', unsafe_allow_html=True)
                if st.button('เพิ่มเติม ▶', key="show_more_apps_viewport_final"):
                    st.session_state.num_items_to_show += 1
                st.markdown('</div>', unsafe_allow_html=True)

    with vis_col2:
        with st.container(border=True, height=650):
            st.subheader("สถิติ FA ตามประเภทคำขอ")
            if not df_filtered.empty:
                chart_data = df_filtered.groupby(['คำนำหน้า', 'ApplicationType'], observed=True).size().unstack(fill_value=0)
                if not chart_data.empty:
                    fig = go.Figure()
                    colors = {'รายใหม่': '#3B82F6', 'ต่ออายุ': '#FBBF24'}
                    app_types_in_order = [col for col in ['ต่ออายุ', 'รายใหม่'] if col in chart_data.columns]
                    for app_type in app_types_in_order:
                        fig.add_trace(go.Bar(
                            x=chart_data.index, y=chart_data[app_type], name=app_type,
                            marker_color=colors.get(app_type), text=chart_data[app_type], textposition='auto'
                        ))
                    fig.update_layout(
                        barmode='stack', bargap=0.2, margin=dict(l=10, r=10, t=50, b=10),
                        width=550, height=500, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E5E7EB')
                    )
                    st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
                else:
                    st.markdown("<div style='height:480px;display:flex;align-items:center;justify-content:center'><p>ไม่มีข้อมูล</p></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:480px;display:flex;align-items:center;justify-content:center'><p>ไม่มีข้อมูล</p></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("สถานะคำขอที่กำลังดำเนินการ FA-2")
        fa2_progress_html_content = generate_application_list_html_optimized(
            df_fa2_progress, st.session_state.num_fa2_items_to_show, len(df_fa2_progress)
        )
        st.markdown(fa2_progress_html_content, unsafe_allow_html=True)

        if len(df_fa2_progress) > st.session_state.num_fa2_items_to_show:
            st.markdown('<div id="custom-view-more-btn-wrapper" style="display:flex; justify-content:center; margin-top:10px; margin-bottom:10px;">', unsafe_allow_html=True)
            if st.button('เพิ่มเติม ▶', key="show_more_fa2_apps_viewport_final"):
                st.session_state.num_fa2_items_to_show += 1
            st.markdown('</div>', unsafe_allow_html=True)
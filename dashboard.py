import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-8')
    df.columns = df.columns.str.strip()

    df['RenewalYearBE'] = pd.to_numeric(df['วันครบอายุเห็นชอบ'].str.split('/').str[-1], errors='coerce').fillna(0).astype(int)

    expiry_date_ad = pd.to_datetime(df['วันครบอายุเห็นชอบ'], format='%d/%m/%Y', errors='coerce') - pd.DateOffset(years=543)
    df['CountdownStartDateBE'] = (expiry_date_ad - pd.DateOffset(days=45) + pd.DateOffset(years=543)).dt.strftime('%d/%m/%Y')

    date_cols_to_convert = ['วันที่ยื่นคำขอ', 'วันที่ตรวจประวัติ', 'วันที่อนุญาต']
    for col in date_cols_to_convert:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce') - pd.DateOffset(years=543)

    df['ให้ความเห็นชอบ FA (แบบ FA-1)'] = df['ให้ความเห็นชอบ FA'].str.split('\n').str[0].str.replace('"', '').str.strip()
    df['ApplicationTypeClean'] = np.where(df['ให้ความเห็นชอบ FA'].str.contains('เสมือนรายใหม่', na=False), 'เสมือนรายใหม่', df['ประเภทคำขอ'])
    
    payment_text = df['วันที่ชำระเงินครั้งที่ 1 และ 2'].str.lower().str.strip()
    cond_paid_fully = payment_text.str.contains("จ่ายครบแล้ว", na=False) | (payment_text.str.contains("#1|# 1", na=False) & payment_text.str.contains("#2|# 2", na=False))
    cond_paid_partially = payment_text.str.contains("#1|# 1", na=False)
    df['PaymentStageStatus'] = np.select([cond_paid_fully, cond_paid_partially], ["ชำระครบ 2 ครั้ง", "ชำระครั้งที่ 1 เท่านั้น"], default="ยังไม่ชำระ")

    today = pd.to_datetime(datetime.now().date())
    df['ProcessingDays'] = np.where(df['วันที่อนุญาต'].notna(), (df['วันที่อนุญาต'] - df['วันที่ยื่นคำขอ']).dt.days, (today - df['วันที่ยื่นคำขอ']).dt.days)
    
    stage_name_map = {'วันที่อนุญาต': 'ได้รับอนุญาต', 'วันที่ตรวจประวัติ': 'ตรวจประวัติ', 'วันที่ยื่นคำขอ': 'ยื่นคำขอ'}
    df['CurrentStage'] = df[stage_name_map.keys()].notna().idxmax(axis=1).map(stage_name_map).fillna('N/A')
    
    df['SLA_Status'] = pd.cut(df['ProcessingDays'], bins=[-np.inf, 30, 45, np.inf], labels=['On Track', 'At Risk', 'Overdue'])
    
    df['Days_Submit_To_Check'] = (df['วันที่ตรวจประวัติ'] - df['วันที่ยื่นคำขอ']).dt.days
    df['Days_Check_To_Approve'] = (df['วันที่อนุญาต'] - df['วันที่ตรวจประวัติ']).dt.days
    
    return df

file_path = "Dataset/FA-1 (ปี 2565)(Sheet1).csv"
df_processed = load_and_prepare_data(file_path)

st.subheader("FA Application Dashboard")
top_col1, top_col2, top_col3 = st.columns([2, 3, 2])

with top_col1:
    fa_type_options = ["ทั้งหมด"] + df_processed['คำนำหน้า'].dropna().unique().tolist()
    fa_type_select = st.selectbox("เลือกประเภท FA", options=fa_type_options)

with top_col2:
    app_type_options = ["ทั้งหมด"] + df_processed['ApplicationTypeClean'].dropna().unique().tolist()
    filter_type = st.radio("ประเภทคำขอ:", options=app_type_options, horizontal=True)

top_col3.markdown(f"<p style='text-align: right; font-weight: bold;'>วันที่ปัจจุบัน: {datetime.now().strftime('%d %b %Y')}</p>", unsafe_allow_html=True)

df_filtered = df_processed
if fa_type_select != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered['คำนำหน้า'] == fa_type_select]
if filter_type != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered['ApplicationTypeClean'] == filter_type]

st.markdown("---")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="คำขอที่กำลังดำเนินการ", value=f"{(df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum()} รายการ")
kpi2.metric(label="ใกล้ครบกำหนด (At Risk)", value=f"{(df_filtered['SLA_Status'] == 'At Risk').sum()} รายการ")
kpi3.metric(label="บ. FA ที่จะต่ออายุปี 68", value=f"{(df_processed['RenewalYearBE'] == 2568).sum()} รายการ")
kpi4.metric(label="ชำระค่าธรรมเนียมเสร็จสิ้น", value=f"{(df_filtered['PaymentStageStatus'] == 'ชำระครบ 2 ครั้ง').sum()} รายการ")

st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 3])

with col1:
    st.selectbox("Status % ", ["ตัวเลือก", "Item 1", "Item 2"])
    st.selectbox("ไตรมาส", ["ตัวเลือก", "Item 1", "Item 2"])

with col2:
    pie_col1, pie_col2 = st.columns(2)
    with pie_col1:
        st.subheader("การชำระค่าธรรมเนียม")
        status_counts = df_filtered['PaymentStageStatus'].value_counts()
        if not status_counts.empty:
            fig = px.pie(status_counts, names=status_counts.index, values=status_counts.values, hole=.3).update_traces(showlegend=False, textposition='inside', textinfo='percent+label').update_layout(margin=dict(l=10, r=10, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with pie_col2:
        st.subheader("สัดส่วนประเภท FA")
        prefix_counts = df_filtered['คำนำหน้า'].value_counts()
        if not prefix_counts.empty:
            fig = px.pie(prefix_counts, names=prefix_counts.index, values=prefix_counts.values, hole=.3).update_traces(showlegend=False, textposition='inside', textinfo='percent+label').update_layout(margin=dict(l=10, r=10, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

with col3:
    st.subheader("สถานะระยะเวลาดำเนินการ (SLA 45 วัน)")
    pending_df = df_filtered.query("CurrentStage != 'ได้รับอนุญาต'").sort_values('ProcessingDays', ascending=True)
    if not pending_df.empty:
        fig = px.bar(pending_df, x='ProcessingDays', y='ให้ความเห็นชอบ FA (แบบ FA-1)', color='SLA_Status', orientation='h',
                     labels={'ProcessingDays': 'จำนวนวันที่ใช้ไป', 'ให้ความเห็นชอบ FA (แบบ FA-1)': 'ชื่อบริษัท'},
                     color_discrete_map={'On Track': '#2ca02c', 'At Risk': '#ff7f0e', 'Overdue': '#d62728'},
                     text='ProcessingDays').update_layout(yaxis={'categoryorder': 'total ascending'}, height=max(400, len(pending_df) * 35)).add_vline(x=45, line_width=3, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("ไม่มีข้อมูลคำขอที่กำลังดำเนินการตามตัวกรองที่เลือก")

st.markdown("---")

details_col1, details_col2 = st.columns(2)

with details_col1:
    st.subheader("แสดงรายละเอียดการจ่ายเงิน")
    st.dataframe(df_filtered[['ให้ความเห็นชอบ FA (แบบ FA-1)', 'PaymentStageStatus', 'วันที่ชำระเงินครั้งที่ 1 และ 2']].rename(columns={'วันที่ชำระเงินครั้งที่ 1 และ 2': 'รายละเอียด'}), use_container_width=True)

with details_col2:
    st.subheader("แสดงระยะเวลาที่ใช้ในแต่ละขั้นตอน")
    df_bottleneck = df_filtered.dropna(subset=['Days_Submit_To_Check', 'Days_Check_To_Approve']).sort_values('ProcessingDays', ascending=True)
    if not df_bottleneck.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(y=df_bottleneck['ให้ความเห็นชอบ FA (แบบ FA-1)'], x=df_bottleneck['Days_Submit_To_Check'], name='ยื่น -> ตรวจ', orientation='h'))
        fig.add_trace(go.Bar(y=df_bottleneck['ให้ความเห็นชอบ FA (แบบ FA-1)'], x=df_bottleneck['Days_Check_To_Approve'], name='ตรวจ -> อนุมัติ', orientation='h'))
        fig.update_layout(barmode='stack', yaxis={'categoryorder': 'total ascending'}, legend_title="ขั้นตอน", margin=dict(l=0, r=0, t=0, b=0), height=max(400, len(df_bottleneck) * 35))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("ไม่มีข้อมูลที่เสร็จสมบูรณ์เพียงพอสำหรับวิเคราะห์ Bottleneck")

st.markdown("---")

st.subheader("ตารางแสดงข้อมูลบริษัท")
display_option = st.radio(
    "เลือกมุมมองข้อมูล:",
    ("รายชื่อ บ. ทั้งหมด", "บ. FA ที่จะต่ออายุปี 68"),
    horizontal=True,
    key="data_display_option"
)

if display_option == "บ. FA ที่จะต่ออายุปี 68":
    df_renewal = df_filtered[df_filtered['RenewalYearBE'] == 2568]
    
    if df_renewal.empty:
        st.info("ไม่พบข้อมูลบริษัทที่จะต่ออายุในปี 2568 ตามตัวกรองที่เลือก")
    else:
        df_display = df_renewal.assign(
            progress_percent=lambda df: pd.to_numeric(
                df['dashboard'].str.replace('%', '', regex=False),
                errors='coerce'
            ).fillna(0).astype(int)
        )

        st.dataframe(
            df_display,
            column_order=[
                "ให้ความเห็นชอบ FA (แบบ FA-1)", 
                "วันครบอายุเห็นชอบ", 
                "progress_percent"
            ],
            column_config={
                "ให้ความเห็นชอบ FA (แบบ FA-1)": st.column_config.TextColumn(
                    "ชื่อบริษัท (FA)"
                ),
                "วันครบอายุเห็นชอบ": st.column_config.TextColumn(
                    "วันครบอายุเห็นชอบ"
                ),
                "progress_percent": st.column_config.ProgressColumn(
                    "ความคืบหน้าการดำเนินงาน",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            use_container_width=True
        )
else:
    st.dataframe(df_filtered, use_container_width=True)
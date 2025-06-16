import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data
def load_and_prepare_data():
    raw_data = {
        'ให้ความเห็นชอบ FA': ["เอเชีย เวลท์ บล. บจก.\nเสมือนรายใหม่", "แอดไวเซอรี่ พลัส บจก.", "คิงส์ฟอร์ด บล. บมจ.\nเสมือนรายใหม่", "ฟินันเซีย ไซรัส บล. บมจ.", "เคจีไอ (ประเทศไทย) บล. บมจ.", "ทิสโก้ บล. บจก.", "เมย์แบงก์ บล. บมจ."],
        'ประเภทคำขอ': ['รายใหม่', 'ต่ออายุ', 'รายใหม่', 'ต่ออายุ', 'รายใหม่', 'ต่ออายุ', 'ต่ออายุ'],
        'วันที่ยื่นคำขอ': ['2024-05-28', '2024-05-15', '2024-06-15', '2024-06-25', '2024-07-01', '2024-05-10', '2024-06-03'],
        'วันที่ตรวจประวัติ': ['2024-06-02', '2024-05-20', '2024-06-20', '2024-06-30', pd.NaT, '2024-05-25', pd.NaT],
        'เสนอบันทึก ผช.ผอฝ.': ['2024-06-12', '2024-05-30', pd.NaT, pd.NaT, pd.NaT, '2024-06-10', pd.NaT],
        'วันที่อนุญาต': [pd.NaT, '2024-06-10', pd.NaT, pd.NaT, pd.NaT, '2024-07-10', pd.NaT],
        'วันที่ชำระเงินครั้งที่ 1 และ 2': ['ยังไม่จ่าย', 'จ่ายครบแล้ว', 'ยังไม่จ่าย', 'จ่ายครบแล้ว', 'จ่ายครบแล้ว', 'จ่ายครบแล้ว', 'ยังไม่จ่าย'],
        'วันครบอายุเห็นชอบ': ['2026-05-09', '2025-04-19', '2026-06-01', '2025-07-15', '2026-06-19', '2025-05-01', '2026-04-30']
    }
    df = pd.DataFrame(raw_data)

    date_cols = ['วันที่ยื่นคำขอ', 'วันที่ตรวจประวัติ', 'เสนอบันทึก ผช.ผอฝ.', 'วันที่อนุญาต', 'วันครบอายุเห็นชอบ']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['CompanyName'] = df['ให้ความเห็นชอบ FA'].str.split('\n').str[0]
    df['ApplicationTypeClean'] = np.where(df['ให้ความเห็นชอบ FA'].str.contains('เสมือนรายใหม่'), 'เสมือนรายใหม่', df['ประเภทคำขอ'])
    df['PaymentStatus'] = np.where(df['วันที่ชำระเงินครั้งที่ 1 และ 2'] == 'จ่ายครบแล้ว', 'จ่ายแล้ว', 'ยังไม่จ่าย')

    today = pd.to_datetime('2025-06-16')

    completed_days = (df['วันที่อนุญาต'] - df['วันที่ยื่นคำขอ']).dt.days
    pending_days = (today - df['วันที่ยื่นคำขอ']).dt.days
    df['ProcessingDays'] = np.where(df['วันที่อนุญาต'].notna(), completed_days, pending_days)
    stage_name_map = {'วันที่อนุญาต': 'ได้รับอนุญาต', 'เสนอบันทึก ผช.ผอฝ.': 'เสนอบันทึกฯ', 'วันที่ตรวจประวัติ': 'ตรวจประวัติ', 'วันที่ยื่นคำขอ': 'ยื่นคำขอ'}
    df['CurrentStage'] = 'N/A'
    for stage_col, stage_name in stage_name_map.items():
        df.loc[df[stage_col].notna(), 'CurrentStage'] = stage_name
    df['DaysRemaining'] = 45 - df['ProcessingDays']
    df['SLA_Status'] = pd.cut(df['ProcessingDays'], bins=[-np.inf, 30, 45, np.inf], labels=['On Track', 'At Risk', 'Overdue'])
    df['UrgencyStatus'] = pd.cut(df['DaysRemaining'], bins=[-np.inf, -1, 10, 25, np.inf], labels=['Overdue', 'เร่งด่วน', 'ต้องให้ความสนใจ', 'ตามแผน'])
    df['RenewalYear'] = df['วันครบอายุเห็นชอบ'].dt.year

    df['Days_Submit_To_Check'] = (df['วันที่ตรวจประวัติ'] - df['วันที่ยื่นคำขอ']).dt.days
    df['Days_Check_To_Propose'] = (df['เสนอบันทึก ผช.ผอฝ.'] - df['วันที่ตรวจประวัติ']).dt.days
    df['Days_Propose_To_Approve'] = (df['วันที่อนุญาต'] - df['เสนอบันทึก ผช.ผอฝ.']).dt.days
    
    return df

df = load_and_prepare_data()

st.sidebar.header("ตัวกรองข้อมูล (Filters)")
app_type_options = ["ทั้งหมด (All)"] + df['ApplicationTypeClean'].unique().tolist()
app_types_selected = st.sidebar.multiselect("ประเภทคำขอ:", options=app_type_options, default="ทั้งหมด (All)")
payment_status_options = ["ทั้งหมด (All)"] + df['PaymentStatus'].unique().tolist()
payment_statuses_selected = st.sidebar.multiselect("สถานะการชำระเงิน:", options=payment_status_options, default="ทั้งหมด (All)")
company_search = st.sidebar.text_input("ค้นหาชื่อบริษัท:")

conditions = []
if "ทั้งหมด (All)" not in app_types_selected and app_types_selected:
    conditions.append(df['ApplicationTypeClean'].isin(app_types_selected))
if "ทั้งหมด (All)" not in payment_statuses_selected and payment_statuses_selected:
    conditions.append(df['PaymentStatus'].isin(payment_statuses_selected))
if company_search:
    conditions.append(df['CompanyName'].str.contains(company_search, case=False))
df_filtered = df[np.all(conditions, axis=0)] if conditions else df

st.title("📊 FA Application & Renewal Tracking Dashboard")
st.markdown(f"**จำลองข้อมูล ณ วันที่: 16 มิถุนายน 2568**")
st.markdown("---")
st.header("ภาพรวมและตัวชี้วัดหลัก (KPIs)")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
pending_apps = (df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum()
at_risk_apps = (df_filtered['SLA_Status'] == 'At Risk').sum()
overdue_apps = (df_filtered['SLA_Status'] == 'Overdue').sum()
renewals_2025 = (df['RenewalYear'] == 2025).sum()
kpi1.metric(label="คำขอที่กำลังดำเนินการ (Pending)", value=f"{pending_apps} รายการ") # ตอบ: เหลือกี่ บ.
kpi2.metric(label="ใกล้ครบกำหนด SLA (At Risk)", value=f"{at_risk_apps} รายการ")
kpi3.metric(label="เกินกำหนด SLA (Overdue)", value=f"{overdue_apps} รายการ", delta="ต้องเร่งดำเนินการ", delta_color="inverse")
kpi4.metric(label="รอต่ออายุปี 2568 (ทั้งหมด)", value=f"{renewals_2025} รายการ") # ตอบ: Req. 2

st.markdown("---")
st.header("การแสดงผลข้อมูลเชิงลึก (Visualizations)")
st.subheader("1. ภาพรวมระยะเวลาดำเนินการ (เวลาที่ใช้ไป)")
pending_df = df_filtered.query("CurrentStage != 'ได้รับอนุญาต'").sort_values('ProcessingDays', ascending=False)
if not pending_df.empty:
    fig_sla = px.bar(pending_df, x='ProcessingDays', y='CompanyName', color='SLA_Status', orientation='h',
                     title='ระยะเวลาดำเนินการของคำขอที่ยังไม่เสร็จสิ้น',
                     labels={'ProcessingDays': 'จำนวนวันที่ใช้ไป', 'CompanyName': 'ชื่อบริษัท'},
                     color_discrete_map={'On Track': '#2ca02c', 'At Risk': '#ff7f0e', 'Overdue': '#d62728'},
                     text='ProcessingDays')
    fig_sla.update_layout(yaxis={'categoryorder':'total ascending'})
    fig_sla.add_vline(x=45, line_width=2, line_dash="dash", line_color="red", annotation_text="SLA 45 วัน")
    st.plotly_chart(fig_sla, use_container_width=True)
else:
    st.info("ไม่มีข้อมูลคำขอที่กำลังดำเนินการตามตัวกรองที่เลือก")

st.subheader("2. Countdown: วันที่เหลือก่อนครบกำหนด SLA")
st.markdown("แสดงเฉพาะคำขอที่ยังไม่เกินกำหนด 45 วัน เรียงตามความเร่งด่วน")
df_countdown = df_filtered.query("CurrentStage != 'ได้รับอนุญาต' and DaysRemaining >= 0").sort_values('DaysRemaining', ascending=True)
if not df_countdown.empty:
    fig_countdown = px.bar(df_countdown, x='DaysRemaining', y='CompanyName', color='UrgencyStatus', orientation='h',
                           title='จำนวนวันที่เหลือก่อนครบกำหนด 45 วัน',
                           labels={'DaysRemaining': 'จำนวนวันที่เหลือ', 'CompanyName': 'ชื่อบริษัท', 'UrgencyStatus': 'ระดับความเร่งด่วน'},
                           color_discrete_map={'ตามแผน': '#2ca02c', 'ต้องให้ความสนใจ': '#ff7f0e', 'เร่งด่วน': '#d62728'},
                           text='DaysRemaining')
    fig_countdown.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_countdown, use_container_width=True)
else:
    st.info("ไม่มีคำขอที่อยู่ในสถานะ Countdown (เนื่องจากเกินกำหนด SLA ไปหมดแล้ว)")

st.subheader("3. วิเคราะห์คอขวด (Bottleneck) ของกระบวนการ")
st.markdown("แสดงระยะเวลาที่ใช้ในแต่ละขั้นตอนสำหรับเคสที่เสร็จสมบูรณ์แล้ว")
df_bottleneck = df_filtered.dropna(subset=['Days_Submit_To_Check', 'Days_Check_To_Propose', 'Days_Propose_To_Approve'])
df_bottleneck = df_bottleneck.sort_values('ProcessingDays', ascending=True)
if not df_bottleneck.empty:
    fig_bottleneck = go.Figure()
    fig_bottleneck.add_trace(go.Bar(y=df_bottleneck['CompanyName'], x=df_bottleneck['Days_Submit_To_Check'], name='ยื่น -> ตรวจ', orientation='h', marker_color='#1f77b4'))
    fig_bottleneck.add_trace(go.Bar(y=df_bottleneck['CompanyName'], x=df_bottleneck['Days_Check_To_Propose'], name='ตรวจ -> เสนอ', orientation='h', marker_color='#ff7f0e'))
    fig_bottleneck.add_trace(go.Bar(y=df_bottleneck['CompanyName'], x=df_bottleneck['Days_Propose_To_Approve'], name='เสนอ -> อนุมัติ', orientation='h', marker_color='#2ca02c'))
    fig_bottleneck.update_layout(barmode='stack', title_text='ระยะเวลาแต่ละขั้นตอน (วัน)', xaxis_title="จำนวนวัน", yaxis_title="บริษัท", yaxis={'categoryorder':'total ascending'}, legend_title="ขั้นตอน")
    st.plotly_chart(fig_bottleneck, use_container_width=True)
else:
    st.info("ไม่มีข้อมูลที่เสร็จสมบูรณ์เพียงพอสำหรับวิเคราะห์ Bottleneck ตามตัวกรองที่เลือก")

col1, col2 = st.columns(2)
with col1:
    st.subheader("4. บริษัทที่ต้องต่ออายุปี 2568")
    renew_df_2025 = df.query("RenewalYear == 2025")[['CompanyName', 'วันครบอายุเห็นชอบ']].sort_values('วันครบอายุเห็นชอบ')
    renew_df_2025['วันครบอายุเห็นชอบ'] = renew_df_2025['วันครบอายุเห็นชอบ'].dt.strftime('%d-%b-%Y')
    st.dataframe(renew_df_2025, use_container_width=True)
with col2:
    st.subheader("5. สรุปตามประเภทคำขอและการชำระเงิน")
    if not df_filtered.empty:
        count_df = df_filtered.groupby(['ApplicationTypeClean', 'PaymentStatus'], as_index=False).size()
        fig_app_type = px.bar(count_df, x='ApplicationTypeClean', y='size', color='PaymentStatus', title='จำนวนคำขอแบ่งตามประเภทและสถานะการชำระเงิน', labels={'ApplicationTypeClean': 'ประเภทคำขอ', 'size': 'จำนวนบริษัท', 'PaymentStatus': 'สถานะการชำระเงิน'}, barmode='stack', text_auto=True)
        st.plotly_chart(fig_app_type, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลตามตัวกรองที่เลือก")

st.markdown("---")
st.header("ตารางข้อมูลแบบละเอียด (Detailed View)")
display_cols = ['CompanyName', 'ApplicationTypeClean', 'วันที่ยื่นคำขอ', 'CurrentStage', 'ProcessingDays', 'DaysRemaining', 'SLA_Status', 'PaymentStatus', 'วันครบอายุเห็นชอบ', 'Days_Submit_To_Check', 'Days_Check_To_Propose', 'Days_Propose_To_Approve']
st.dataframe(df_filtered[display_cols], use_container_width=True)
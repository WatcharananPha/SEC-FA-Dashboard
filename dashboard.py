import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="FA Application Dashboard", page_icon="📊")

COLOR_DARK_BG = "#2A3642"
COLOR_LIGHT_BG = "#F0F2F6"
COLOR_CARD_BG = "#FFFFFF"
COLOR_ACCENT_ORANGE = "#E87A63"
COLOR_ACCENT_GREEN = "#A8E6CF"
COLOR_TEXT = "#2A3642"

st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    html, body, [class*="st-"], [class*="css-"] {{ font-family: 'Montserrat', sans-serif; }}
    .main .block-container {{ background-color: {COLOR_LIGHT_BG}; }}
    [data-testid="stSidebar"] {{ background-color: {COLOR_DARK_BG}; padding: 0 20px; }}
    [data-testid="stSidebar"] h1 {{ color: white; padding-top: 15px; font-weight: 700; }}
    [data-testid="stSidebar"] h3 {{ color: #A0AEC0; font-weight: 600; }}
    .sidebar-link {{ display: block; padding: 10px 15px; margin-bottom: 8px; color: #E2E8F0; text-decoration: none; border-radius: 8px; font-weight: 600; transition: all 0.3s; }}
    .sidebar-link:hover {{ background-color: #4A5568; color: white; text-decoration: none; }}
    .st-emotion-cache-1r6slb0 {{ background-color: {COLOR_CARD_BG}; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #E0E0E0; padding: 2em; }}
    [data-testid="metric-container"] {{ background-color: {COLOR_CARD_BG}; border: 1px solid #E0E0E0; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    [data-testid="stMetricLabel"] p {{ color: #555; font-weight: 600; text-transform: uppercase; }}
    [data-testid="stMetricValue"] {{ font-size: 2.2rem; font-weight: 700; color: {COLOR_TEXT}; }}
    h1, h2, h3 {{ color: {COLOR_TEXT}; font-weight: 700; }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_csv(file_path, encoding="utf-8")
    df.columns = df.columns.str.strip()

    for col in ["วันที่ยื่นคำขอ", "วันที่ตรวจประวัติ", "วันที่อนุญาต"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], format="%d/%m/%Y", errors="coerce"
            ) - pd.DateOffset(years=543)

    df = df.assign(
        RenewalYearBE=pd.to_numeric(
            df["วันครบอายุเห็นชอบ"].str.split("/").str[-1], errors="coerce"
        )
        .fillna(0)
        .astype(int),
        progress_percent=pd.to_numeric(
            df["dashboard"].astype(str).str.replace("%", "", regex=False),
            errors="coerce",
        ).fillna(0),
        CompanyNameClean=df["ให้ความเห็นชอบ FA"]
        .str.split("\n")
        .str[0]
        .str.replace('"', "")
        .str.strip(),
        ApplicationTypeClean=np.where(
            df["ให้ความเห็นชอบ FA"].str.contains("เสมือนรายใหม่", na=False),
            "เสมือนรายใหม่",
            df["ประเภทคำขอ"],
        ),
        PaymentStageStatus=np.select(
            [
                df["วันที่ชำระเงินครั้งที่ 1 และ 2"]
                .str.lower()
                .str.contains("จ่ายครบแล้ว|#1.*#2|#2.*#1", na=False, regex=True),
                df["วันที่ชำระเงินครั้งที่ 1 และ 2"]
                .str.lower()
                .str.contains("#1|# 1", na=False),
            ],
            ["ชำระครบ 2 ครั้ง", "ชำระครั้งที่ 1 เท่านั้น"],
            default="ยังไม่ชำระ",
        ),
        ProcessingDays=lambda df: (datetime.now() - df["วันที่ยื่นคำขอ"]).dt.days.where(
            df["วันที่อนุญาต"].isna(), (df["วันที่อนุญาต"] - df["วันที่ยื่นคำขอ"]).dt.days
        ),
        CurrentStage=lambda df: df[["วันที่อนุญาต", "วันที่ตรวจประวัติ", "วันที่ยื่นคำขอ"]]
        .notna()
        .idxmax(axis=1)
        .map(
            {
                "วันที่อนุญาต": "ได้รับอนุญาต",
                "วันที่ตรวจประวัติ": "ตรวจประวัติ",
                "วันที่ยื่นคำขอ": "ยื่นคำขอ",
            }
        )
        .fillna("N/A"),
        SLA_Status=lambda df: pd.cut(
            df["ProcessingDays"],
            bins=[-np.inf, 30, 45, np.inf],
            labels=["On Track", "At Risk", "Overdue"],
        ),
        Days_Submit_To_Check=lambda df: (df["วันที่ตรวจประวัติ"] - df["วันที่ยื่นคำขอ"]).dt.days,
        Days_Check_To_Approve=lambda df: (df["วันที่อนุญาต"] - df["วันที่ตรวจประวัติ"]).dt.days,
    ).rename(columns={"CompanyNameClean": "ให้ความเห็นชอบ FA (แบบ FA-1)"})

    return df


df_processed = load_and_prepare_data("Dataset/FA-1 (ปี 2565)(Sheet1).csv")

with st.container(border=True):
    filter_col1, filter_col2 = st.columns([1, 2])
    fa_type_select = filter_col1.selectbox(
        "เลือกประเภท FA",
        ["ทั้งหมด"] + df_processed["คำนำหน้า"].dropna().unique().tolist(),
        label_visibility="collapsed",
    )
    filter_type = filter_col2.radio(
        "ประเภทคำขอ:",
        ["ทั้งหมด"] + df_processed["ApplicationTypeClean"].dropna().unique().tolist(),
        horizontal=True,
    )

df_filtered = df_processed
if fa_type_select != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered["คำนำหน้า"] == fa_type_select]
if filter_type != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered["ApplicationTypeClean"] == filter_type]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(
    label="คำขอที่อยู่ระหว่างการดำเนินการ",
    value=f"{(df_filtered['CurrentStage'] != 'ได้รับอนุญาต').sum()}",
)
kpi2.metric(
    label="ใกล้ครบกำหนด 45 วัน", value=f"{(df_filtered['SLA_Status'] == 'At Risk').sum()}"
)
kpi3.metric(
    label="บ. FA ที่จะต่ออายุ ปี 2568",
    value=f"{(df_processed['RenewalYearBE'] == 2568).sum()}",
)
kpi4.metric(
    label="จำนวนบริษัทที่ขออนุญาตทั้งหมด",
    value=f"{(df_filtered['PaymentStageStatus'] == 'ชำระครบ 2 ครั้ง').sum()}",
)

chart_col1, chart_col2 = st.columns([2, 3])
col1, col2, col3 = st.columns([1, 2, 3])

with col1:
    st.selectbox(
        "โชว์ status % ",
        [
            "ทั้งหมด",
            "ยังไม่ดำเนินการ",
            "ตรวจสอบประวัติ (25 %)",
            "สัมภาษณ์ระบบงาน (50 %)",
            "จัดเตรียมบันทึกเสนออนุมัติ (75 %)",
            "อนุมัติความเห็นชอบ (100 %)",
        ],
    )
    st.selectbox(
        "แสดงสถิติ : Quarter",
        ["ทั้งหมด", "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"],
    )

with chart_col1, st.container(border=True):
    st.subheader("การชำระค่าธรรมเนียม")
    status_counts = df_filtered["PaymentStageStatus"].value_counts()
    if not status_counts.empty:
        fig = px.pie(
            status_counts,
            names=status_counts.index,
            values=status_counts.values,
            hole=0.5,
            color_discrete_sequence=[
                COLOR_ACCENT_ORANGE,
                COLOR_ACCENT_GREEN,
                "#CCCCCC",
            ],
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            showlegend=False,
            marker=dict(line=dict(color=COLOR_CARD_BG, width=4)),
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor=COLOR_CARD_BG
        )
        st.plotly_chart(fig, use_container_width=True)

with chart_col2, st.container(border=True):
    st.subheader("Status ของการดำเนินการ")
    df_bottleneck = df_filtered.dropna(
        subset=["Days_Submit_To_Check", "Days_Check_To_Approve"]
    ).sort_values("ProcessingDays", ascending=True)
    if not df_bottleneck.empty:
        fig = go.Figure(
            data=[
                go.Bar(
                    name="Submit → Check",
                    y=df_bottleneck["ให้ความเห็นชอบ FA (แบบ FA-1)"],
                    x=df_bottleneck["Days_Submit_To_Check"],
                    orientation="h",
                    marker_color=COLOR_ACCENT_ORANGE,
                ),
                go.Bar(
                    name="Check → Approve",
                    y=df_bottleneck["ให้ความเห็นชอบ FA (แบบ FA-1)"],
                    x=df_bottleneck["Days_Check_To_Approve"],
                    orientation="h",
                    marker_color=COLOR_ACCENT_GREEN,
                ),
            ]
        )
        fig.update_layout(
            barmode="stack",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            height=max(400, len(df_bottleneck) * 35),
            paper_bgcolor=COLOR_CARD_BG,
            plot_bgcolor=COLOR_CARD_BG,
            xaxis=dict(showgrid=False),
            yaxis=dict(categoryorder="total ascending", showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough completed data to analyze bottlenecks.")

with st.container(border=True):
    st.subheader("รายละเอียดของ บ. FA ทั้งหมด")
    display_option = st.radio(
        "ตัวเลือก :", ("บริษัททั้งหมด", "บ. FA ที่จะต่ออายุปี 68 ทั้งหมด"), horizontal=True
    )

    if display_option == "Companies Renewing in 2568":
        df_display = df_filtered[df_filtered["RenewalYearBE"] == 2568]
        column_order = [
            "ให้ความเห็นชอบ FA (แบบ FA-1)",
            "วันครบอายุเห็นชอบ",
            "progress_percent",
        ]
    else:
        df_display = df_filtered
        column_order = [
            "ให้ความเห็นชอบ FA (แบบ FA-1)",
            "ApplicationTypeClean",
            "CurrentStage",
            "progress_percent",
        ]

    if not df_display.empty:
        st.dataframe(
            df_display,
            column_order=column_order,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ให้ความเห็นชอบ FA (แบบ FA-1)": st.column_config.TextColumn(
                    "Company (FA)", width="large"
                ),
                "วันครบอายุเห็นชอบ": st.column_config.TextColumn("Renewal Date"),
                "ApplicationTypeClean": "Application Type",
                "CurrentStage": "Stage",
                "SLA_Status": "SLA",
                "progress_percent": st.column_config.ProgressColumn(
                    "Progress", format="%d%%", min_value=0, max_value=100
                ),
            },
        )
    else:
        st.info("No data available for the selected view and filters.")

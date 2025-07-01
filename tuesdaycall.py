# ========================== #
# 🔧 Imports and Setup
# ========================== #
import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO
from datetime import date
from calendar import monthrange

# Streamlit page config
st.set_page_config(page_title="Current Sales Performance", layout="wide")

# ========================== #
# 🧾 App Title and Instructions
# ========================== #
st.title("\U0001F4CA Current Sales Performance Overview")

st.markdown("""
### \U0001F5C2️ How to Export Your Sales CSV from Power BI

1. Open **Power BI**
2. Navigate to the **WZ Sales Analysis** dashboard
3. Scroll to the bottom and click **KPI Details**
4. At the top, select the **Employee** view
5. Click the **three dots (\u22EF)** in the upper-right of the chart
6. Choose **Export Data**
7. Set **Data format** to `Summarized data` and file type to `.CSV`
8. Download and save the CSV file
9. Upload it below ⬇️
""")

# ========================== #
# 📤 File Upload Section
# ========================== #
uploaded_file = st.file_uploader("📂 Upload your sales CSV file", type=["csv"])

# Ensure folder exists
os.makedirs("uploaded_files", exist_ok=True)

# Previously uploaded CSV
csv_files = [f for f in os.listdir("uploaded_files") if f.endswith(".csv")]
if csv_files:
    selected_csv = st.selectbox("📁 Or select a previously uploaded CSV:", csv_files)
    if selected_csv and not uploaded_file:
        uploaded_file = open(os.path.join("uploaded_files", selected_csv), "rb")

# RQ Excel file upload
rq_file = st.file_uploader("📄 Upload the RQ Excel file", type=["xlsx"])

# Previously uploaded RQ file
rq_files = [f for f in os.listdir("uploaded_files") if f.endswith(".xlsx")]
if rq_files:
    selected_rq = st.selectbox("📁 Or select a previously uploaded RQ file:", rq_files)
    if selected_rq and not rq_file:
        rq_file = open(os.path.join("uploaded_files", selected_rq), "rb")

# ========================== #
# 🗓️ Date Range Input
# ========================== #
st.markdown("**Select Reporting Period (for GP Daily Average):**")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", date(2025, 5, 1))
with col2:
    end_date = st.date_input("End Date", date(2025, 5, 20))
num_days = (end_date - start_date).days + 1

# ========================== #
# 💾 Save Uploaded Files
# ========================== #
if uploaded_file is not None:
    with open(os.path.join("uploaded_files", uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

if rq_file is not None:
    with open(os.path.join("uploaded_files", rq_file.name), "wb") as f:
        f.write(rq_file.getbuffer())

# ========================== #
# 📊 Data Cleaning & Processing
# ========================== #
try:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip() for col in df.columns]

    if 'SMT Qty' not in df.columns:
        st.error("\u274C 'SMT Qty' column missing.")
        st.stop()

    df.rename(columns={
        'Employee Full Name': 'Employee',
        'GA': 'News',
        'VZ Perks Rate': 'Perks',
        '(RQ) Consumer SMT Prem Unlim %': 'Premium Unlimited',
        'VMP Take Rate': 'VMP',
        'VZPH Qty': 'VZPH',
        'VZ CC QTY': 'Verizon Visa'
    }, inplace=True)

    df = df[df['Employee'].astype(str).str.split().str.len() >= 2]
    df = df[~df['Employee'].str.lower().isin(['rep enc', 'unknown'])]
    df['Employee'] = df['Employee'].apply(lambda name: " ".join(sorted(name.strip().split())).title())

    numeric_cols = ['Perks', 'VMP', 'Premium Unlimited', 'GP', 'News', 'Upgrades', 'SMT GA', 'SMB GA', 'SMT Qty', 'VZ VHI GA', 'VZ FIOS GA', 'VZPH', 'Verizon Visa']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.replace('$', '').str.replace(',', ''), errors='coerce')

    df.fillna(0, inplace=True)

    df_grouped = df.groupby('Employee', as_index=False).agg({
        'News': 'sum', 'Upgrades': 'sum', 'SMT GA': 'sum', 'Perks': 'mean', 'VMP': 'mean',
        'GP': 'sum', 'SMB GA': 'sum', 'Premium Unlimited': 'mean', 'VZ VHI GA': 'sum',
        'VZ FIOS GA': 'sum', 'VZPH': 'sum', 'Verizon Visa': 'sum', 'SMT Qty': 'sum'
    })

    df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0, df_grouped['News'] / df_grouped['Upgrades'], 0).round(2)
    df_grouped['GP Per Smart'] = np.where(df_grouped['SMT Qty'] != 0, df_grouped['GP'] / df_grouped['SMT Qty'], 0).round(2)
    df_grouped['VHI/FIOS'] = df_grouped['VZ VHI GA'] + df_grouped['VZ FIOS GA']

    # ========================== #
    # 📥 Merge with RQ Excel File
    # ========================== #
    if rq_file is not None:
        try:
            rq_excel = pd.ExcelFile(rq_file)
            rq_df = rq_excel.parse(rq_excel.sheet_names[0])
            rq_data = rq_df.iloc[2:].copy()
            rq_data.columns = rq_df.iloc[1]

            rq_filtered = rq_data[['Employee Name', '(Q) FiOS Sales', '(Q) 5G Consumer Internet']].copy()
            rq_filtered.columns = ['Employee', 'FiOS Sales', '5G Internet']
            rq_filtered['Employee'] = rq_filtered['Employee'].apply(lambda name: " ".join(sorted(str(name).strip().split())).title())
            rq_filtered['FiOS Sales'] = pd.to_numeric(rq_filtered['FiOS Sales'], errors='coerce').fillna(0)
            rq_filtered['5G Internet'] = pd.to_numeric(rq_filtered['5G Internet'], errors='coerce').fillna(0)
            rq_filtered['VHI/FIOS'] = rq_filtered['FiOS Sales'] + rq_filtered['5G Internet']

            df_grouped.drop(columns=['VHI/FIOS'], inplace=True, errors='ignore')
            df_grouped = pd.merge(df_grouped, rq_filtered[['Employee', 'VHI/FIOS']], on='Employee', how='left')
            df_grouped['VHI/FIOS'] = df_grouped['VHI/FIOS'].fillna(0)
            st.success("RQ File merged. VHI/FIOS updated.")

        except Exception as rq_error:
            st.warning(f"⚠️ RQ File error: {rq_error}")

    # ========================== #
    # ➕ Add Summary Row
    # ========================== #
    summary_row = pd.DataFrame({...})  # (keep your summary row code here)
    df_final = pd.concat([df_grouped, summary_row], ignore_index=True)

    # ========================== #
    # 🔢 Format and Round Columns
    # ========================== #
    for col in df_final.columns:
        if col != 'Employee' and df_final[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
            df_final[col] = df_final[col].round(2)

    df_final['GP'] = df_final['GP'].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
    df_final['GP Per Smart'] = df_final['GP Per Smart'].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)

    df_final.drop(columns=[col for col in ['SMT Qty', 'Total Boxes', 'VZ VHI GA', 'VZ FIOS GA'] if col in df_final.columns], inplace=True)

    # ========================== #
    # 🧮 Display Table with Goals
    # ========================== #
    st.markdown("""...""", unsafe_allow_html=True)  # goal banner

    display_columns = [...]
    df_final = df_final[display_columns]

    def highlight_goals(val, col): ...
    styled_df = df_final.style.format(...).apply(...)

    st.subheader("📄 Performance Table with Goals & Totals")
    st.dataframe(styled_df, use_container_width=True)

    # ========================== #
    # 📈 GP Summary & Projection
    # ========================== #
    total_gp = df_grouped['GP'].sum()
    daily_avg_gp = total_gp / num_days if num_days > 0 else 0
    num_days_in_month = monthrange(end_date.year, end_date.month)[1]
    projected_gp = daily_avg_gp * num_days_in_month

    st.markdown(f"""...""")

    # ========================== #
    # 📥 Export CSV Button
    # ========================== #
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV Report",
        data=csv,
        file_name="sales_performance_summary.csv",
        mime='text/csv'
    )

except Exception as e:
    st.error(f"❌ File processing error: {e}")

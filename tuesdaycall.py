import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="Current Sales Performance", layout="wide")

st.title("📊 Current Sales Performance Overview")
st.markdown("""
### 🗂️ How to Export Your Sales CSV from Power BI

1. Open **Power BI**
2. Navigate to the **WZ Sales Analysis** dashboard
3. Scroll to the bottom and click **KPI Details**
4. At the top, select the **Employee** view
5. Click the **three dots (⋯)** in the upper-right of the chart
6. Choose **Export Data**
7. Set **Data format** to `Summarized data` and file type to `.CSV`
8. Download and save the CSV file
9. Upload it below ⬇️
""")

uploaded_file = st.file_uploader("\U0001F4C1 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]

        if 'SMT Qty' not in df.columns:
            st.error("\u274C The required column 'SMT Qty' was not found in your CSV.")
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

        # Grouping and Aggregation
        df_grouped = df.groupby('Employee', as_index=False).agg({
            'News': 'sum',
            'Upgrades': 'sum',
            'SMT GA': 'sum',
            'Perks': 'mean',  # Mean instead of sum
            'VMP': 'mean',    # Corrected to average instead of sum
            'GP': 'sum',
            'SMB GA': 'sum',
            'Premium Unlimited': 'mean',
            'VZ VHI GA': 'sum',
            'VZ FIOS GA': 'sum',
            'VZPH': 'sum',
            'Verizon Visa': 'sum',
            'SMT Qty': 'sum'
        })

        df_grouped['Total Boxes'] = df_grouped['News'] + df_grouped['Upgrades']
        df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0, df_grouped['News'] / df_grouped['Upgrades'], 0).round(2)
        df_grouped['GP Per Smart'] = np.where(df_grouped['SMT Qty'] != 0, df_grouped['GP'] / df_grouped['SMT Qty'], 0).round(2)
        df_grouped['VHI/FIOS'] = df_grouped['VZ VHI GA'] + df_grouped['VZ FIOS GA']

        final_cols = [
            'Employee', 'News', 'Upgrades', 'Total Boxes', 'Ratio', 'SMT GA',
            'Perks', 'VMP', 'GP Per Smart', 'GP', 'SMB GA', 'Premium Unlimited',
            'VHI/FIOS', 'VZPH', 'Verizon Visa'
        ]
        df_display = df_grouped[final_cols].copy()

        st.success("\u2705 File processed successfully!")
        st.subheader("\U0001F4C4 Performance Table with Goals & Totals")
        st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"\u274C Error while processing file:\n\n{e}")

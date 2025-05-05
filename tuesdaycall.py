import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Current Sales Performance", layout="wide")



st.title("\U0001F4CA Current Sales Performance Overview")
uploaded_file = st.file_uploader("\U0001F4C1 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        # st.write("✅ Columns loaded:", df.columns.tolist())  # Debugging info commented out

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

        # Ensure all needed columns are numeric
        numeric_cols = ['Perks', 'VMP', 'Premium Unlimited', 'GP', 'News', 'Upgrades', 'SMT GA', 'SMB GA', 'SMT Qty', 'VZ VHI GA', 'VZ FIOS GA', 'VZPH', 'Verizon Visa']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.replace('$', '').str.replace(',', ''), errors='coerce')

        df.fillna(0, inplace=True)

        df_grouped = df.groupby('Employee', as_index=False)[numeric_cols].sum()
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

        total_gp_value = df_grouped['GP'].sum()
        totals = {
            'Employee': 'TOTALS / AVG',
            'News': df_grouped['News'].sum(),
            'Upgrades': df_grouped['Upgrades'].sum(),
            'Total Boxes': df_grouped['Total Boxes'].sum(),
            'Ratio': round(df_grouped['Ratio'].mean(), 2),
            'SMT GA': df_grouped['SMT GA'].sum(),
            'Perks': f"{df_grouped['Perks'].mean():.2f}%",
            'VMP': f"{df_grouped['VMP'].mean():.2f}%",
            'GP Per Smart': f"${(total_gp_value / df_grouped['SMT Qty'].sum()):,.2f}" if df_grouped['SMT Qty'].sum() > 0 else "$0.00",
            'GP': f"${total_gp_value:,.2f}",
            'SMB GA': df_grouped['SMB GA'].sum(),
            'Premium Unlimited': f"{df_grouped['Premium Unlimited'].mean():.2f}%",
            'VHI/FIOS': df_grouped['VHI/FIOS'].sum(),
            'VZPH': df_grouped['VZPH'].sum(),
            'Verizon Visa': df_grouped['Verizon Visa'].sum()
        }
        df_display = pd.concat([df_display, pd.DataFrame([totals])], ignore_index=True)

        st.success("\u2705 File processed successfully!")
        st.subheader("\U0001F4C4 Performance Table with Goals & Totals")
        st.dataframe(df_display, use_container_width=True)

        st.subheader("\U0001F4CA Current Month Trend")
        st.markdown(f"\U0001F4A1 **Trend so far:** `${total_gp_value:,.2f}` in Gross Profit this month.")

    except Exception as e:
        st.error(f"\u274C Error while processing file:\n\n{e}")

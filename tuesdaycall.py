import streamlit as st
import pandas as pd
import numpy as np

# --- Page Setup ---
st.set_page_config(page_title="Current Sales Performance", layout="wide")
st.title("📊 Current Sales Performance Overview")

# --- File Upload ---
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df.rename(columns={'SMT Qty': 'SMT QTY'}, inplace=True)

        # --- Rename & Filter Columns ---
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

        # Normalize name format
        df['Employee'] = df['Employee'].apply(lambda name: " ".join(sorted(name.strip().split())).title())

        # --- Clean Numeric Columns ---
        percent_cols = ['Perks', 'VMP', 'Premium Unlimited']
        for col in percent_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')

        money_cols = ['GP']
        for col in money_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')

        qty_cols = ['News', 'Upgrades', 'SMT GA', 'SMB GA', 'SMT QTY', 'VZ VHI GA', 'VZ FIOS GA', 'VZPH', 'Verizon Visa']
        for col in qty_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.fillna(0, inplace=True)

        # --- Group and Calculate ---
        df_grouped = df.groupby('Employee', as_index=False).sum()
        df_grouped['Total Boxes'] = df_grouped['News'] + df_grouped['Upgrades']
        df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0, df_grouped['News'] / df_grouped['Upgrades'], 0).round(2)
        df_grouped['GP Per Smart'] = np.where(df_grouped['SMT QTY'] != 0, df_grouped['GP'] / df_grouped['SMT QTY'], 0).round(2)
        df_grouped['VHI/FIOS'] = df_grouped['VZ VHI GA'] + df_grouped['VZ FIOS GA']

        # --- Reorder Columns ---
        final_cols = [
            'Employee', 'News', 'Upgrades', 'Total Boxes', 'Ratio',
            'SMT GA', 'Perks', 'VMP', 'GP Per Smart', 'GP', 'SMB GA',
            'Premium Unlimited', 'VHI/FIOS', 'VZPH', 'Verizon Visa'
        ]
        df_display = df_grouped[final_cols].copy()

        # --- Top Row: Goals ---
        goals = {
            'Employee': 'Goal',
            'Ratio': 0.5,
            'Perks': '56%',
            'VMP': '55%',
            'GP Per Smart': '$460.00',
            'SMB GA': 3,
            'Premium Unlimited': '65%',
            'VHI/FIOS': 7,
            'VZPH': 2,
            'Verizon Visa': 1
        }
        goals_row = {col: goals.get(col, '') for col in final_cols}
        df_display.loc[-1] = goals_row
        df_display.index = df_display.index + 1
        df_display.sort_index(inplace=True)

        # --- Bottom Row: Totals & Averages ---
        totals = {
            'Employee': 'TOTALS / AVG',
            'News': df_grouped['News'].sum(),
            'Upgrades': df_grouped['Upgrades'].sum(),
            'Total Boxes': df_grouped['Total Boxes'].sum(),
            'Ratio': df_grouped['Ratio'].mean().round(2),
            'SMT GA': df_grouped['SMT GA'].sum(),
            'Perks': f"{df_grouped['Perks'].mean():.2f}%",
            'VMP': f"{df_grouped['VMP'].mean():.2f}%",
            'GP Per Smart': f"${(df_grouped['GP'].sum() / df_grouped['SMT QTY'].sum()):,.2f}" if df_grouped['SMT QTY'].sum() > 0 else "$0.00",
            'GP': f"${df_grouped['GP'].sum():,.2f}",
            'SMB GA': df_grouped['SMB GA'].sum(),
            'Premium Unlimited': f"{df_grouped['Premium Unlimited'].mean():.2f}%",
            'VHI/FIOS': df_grouped['VHI/FIOS'].sum(),
            'VZPH': df_grouped['VZPH'].sum(),
            'Verizon Visa': df_grouped['Verizon Visa'].sum()
        }
        df_display.loc[len(df_display)] = totals

        # --- Format Display ---
        def format_currency(val):
            try:
                return f"${float(val):,.2f}"
            except:
                return val

        def format_percent(val):
            try:
                return f"{float(val):.2f}%"
            except:
                return val

        for col in ['GP', 'GP Per Smart']:
            df_display[col] = df_display[col].apply(format_currency)

        for col in ['Perks', 'VMP', 'Premium Unlimited']:
            df_display[col] = df_display[col].apply(format_percent)

        st.success("✅ File processed successfully!")
        st.subheader("📄 Performance Table with Goals & Totals")
        st.dataframe(df_display, use_container_width=True)

        # --- Trend Summary ---
        st.subheader("📊 Current Month Trend")
        st.markdown("This section can be updated weekly with narrative summaries or charts showing progress toward goals.")

    except Exception as e:
        st.error(f"❌ Error: {e}")


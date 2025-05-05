import streamlit as st
import pandas as pd
import numpy as np

# --- Page Setup ---
st.set_page_config(page_title="Current Sales Performance", layout="wide")
st.title("📊 Current Sales Performance Overview")

uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df.rename(columns={'SMT Qty': 'SMT QTY'}, inplace=True)

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

        percent_cols = ['Perks', 'VMP', 'Premium Unlimited']
        for col in percent_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')

        money_cols = ['GP']
        for col in money_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')

        qty_cols = ['News', 'Upgrades', 'SMT GA', 'SMB GA', 'SMT QTY',
                    'VZ VHI GA', 'VZ FIOS GA', 'VZPH', 'Verizon Visa']
        for col in qty_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                df[col] = 0

        df.fillna(0, inplace=True)

        # --- DEBUG: Force numeric again for safety ---
        df['News'] = pd.to_numeric(df['News'], errors='coerce')
        df['Upgrades'] = pd.to_numeric(df['Upgrades'], errors='coerce')

        df_grouped = df.groupby('Employee', as_index=False).sum()

        # --- DEBUG Check types ---
        st.write("✅ Data types before summing News + Upgrades:")
        st.write("News type:", df_grouped['News'].dtype)
        st.write("Upgrades type:", df_grouped['Upgrades'].dtype)
        st.write("News sample:", df_grouped['News'].head())
        st.write("Upgrades sample:", df_grouped['Upgrades'].head())

        df_grouped['Total Boxes'] = df_grouped['News'] + df_grouped['Upgrades']
        df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0,
                                       df_grouped['News'] / df_grouped['Upgrades'], 0).round(2)
        df_grouped['GP Per Smart'] = np.where(df_grouped['SMT QTY'] != 0,
                                              df_grouped['GP'] / df_grouped['SMT QTY'], 0).round(2)
        df_grouped['VHI/FIOS'] = pd.to_numeric(df_grouped.get('VZ VHI GA', 0), errors='coerce').fillna(0) + \
                                 pd.to_numeric(df_grouped.get('VZ FIOS GA', 0), errors='coerce').fillna(0)

        final_cols = [
            'Employee', 'News', 'Upgrades', 'Total Boxes', 'Ratio',
            'SMT GA', 'Perks', 'VMP', 'GP Per Smart', 'GP', 'SMB GA',
            'Premium Unlimited', 'VHI/FIOS', 'VZPH', 'Verizon Visa'
        ]
        df_display = df_grouped[final_cols].copy()

        # --- Totals ---
        total_gp_value = df_grouped['GP'].sum()
        totals = {
            'Employee': 'TOTALS / AVG',
            'News': float(df_grouped['News'].sum()),
            'Upgrades': float(df_grouped['Upgrades'].sum()),
            'Total Boxes': float(df_grouped['Total Boxes'].sum()),
            'Ratio': round(df_grouped['Ratio'].mean(), 2),
            'SMT GA': float(df_grouped['SMT GA'].sum()),
            'Perks': f"{df_grouped['Perks'].mean():.2f}%",
            'VMP': f"{df_grouped['VMP'].mean():.2f}%",
            'GP Per Smart': f"${(total_gp_value / df_grouped['SMT QTY'].sum()):,.2f}" if df_grouped['SMT QTY'].sum() > 0 else "$0.00",
            'GP': f"${total_gp_value:,.2f}",
            'SMB GA': float(df_grouped['SMB GA'].sum()),
            'Premium Unlimited': f"{df_grouped['Premium Unlimited'].mean():.2f}%",
            'VHI/FIOS': float(df_grouped['VHI/FIOS'].sum()),
            'VZPH': float(df_grouped['VZPH'].sum()),
            'Verizon Visa': float(df_grouped['Verizon Visa'].sum())
        }
        df_display = pd.concat([df_display, pd.DataFrame([totals])], ignore_index=True)

        # --- Formatting ---
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

        # --- Goals Row ---
        goals_row = pd.DataFrame([{
            'Employee': 'GOALS',
            'News': '',
            'Upgrades': '',
            'Total Boxes': '',
            'Ratio': 0.5,
            'SMT GA': '',
            'Perks': '56%',
            'VMP': '55%',
            'GP Per Smart': '$460.00',
            'GP': '',
            'SMB GA': 3,
            'Premium Unlimited': '65%',
            'VHI/FIOS': 7,
            'VZPH': 2,
            'Verizon Visa': 1
        }])
        df_display = pd.concat([goals_row[final_cols], df_display], ignore_index=True)

        # --- Shade Goals Row ---
        def highlight_goals_row(row):
            return ['background-color: lightgrey' if row.name == 0 else '' for _ in row]

        styled_df = df_display.style.apply(highlight_goals_row, axis=1)

        st.success("✅ File processed successfully!")
        st.subheader("📄 Performance Table with Goals & Totals")
        st.dataframe(styled_df, use_container_width=True)

        st.subheader("📊 Current Month Trend")
        st.markdown(f"💡 **Trend so far:** `${total_gp_value:,.2f}` in Gross Profit this month.")

    except Exception as e:
        st.error(f"❌ Error while processing file:\n\n{e}")

import streamlit as st
import pandas as pd
import numpy as np

# --- Page Configuration ---
st.set_page_config(page_title="Sales Performance Extractor", layout="wide")
st.title("📊 Sales Performance Commissions/Results")
st.markdown("Upload your sales CSV and extract a clean, styled summary with point-based commission insights.")

# --- File Upload ---
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Normalize column names
        df.columns = [col.strip() for col in df.columns]
        df.rename(columns={'SMT Qty': 'SMT QTY'}, inplace=True)

        required_cols = [
            'Employee Full Name', 'GA', 'Upgrades', 'SMT GA', 'SMB GA',
            'VZ Perks Rate', '(RQ) Consumer SMT Prem Unlim %', 'VZ VHI GA',
            'VZ FIOS GA', 'VMP Take Rate', 'GP', 'SMT QTY'
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
        else:
            df.rename(columns={
                'Employee Full Name': 'Employee',
                'GA': 'News',
                'SMT GA': 'SMT GA',
                'SMB GA': 'SMB GA',
                'VZ Perks Rate': 'VZ Perks Rate (%)',
                '(RQ) Consumer SMT Prem Unlim %': 'Premium Unlim (%)',
                'VMP Take Rate': 'VMP'
            }, inplace=True)

            df = df[df['Employee'].astype(str).str.split().str.len() >= 2]
            df = df[~df['Employee'].str.lower().isin(['rep enc', 'unknown'])]

            for col in ['Premium Unlim (%)', 'VMP', 'VZ Perks Rate (%)']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
            df['GP'] = pd.to_numeric(df['GP'].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')
            df['SMT QTY'] = pd.to_numeric(df['SMT QTY'], errors='coerce')

            numeric_cols = [
                'News', 'Upgrades', 'SMT GA', 'SMB GA', 'VZ Perks Rate (%)',
                'Premium Unlim (%)', 'VZ VHI GA', 'VZ FIOS GA', 'VMP', 'GP', 'SMT QTY'
            ]
            df[numeric_cols] = df[numeric_cols].fillna(0)

            df = df.groupby('Employee', as_index=False)[numeric_cols].sum()

            df['Total GA'] = df['News'] + df['Upgrades']
            df['Ratio'] = np.where(df['Upgrades'] != 0, df['News'] / df['Upgrades'], 0).round(2)
            df['GP Per Smart'] = np.where(df['SMT QTY'] != 0, df['GP'] / df['SMT QTY'], 0).round(2)

            df['GP'] = df['GP'].apply(lambda x: f"${x:,.2f}")
            df['GP Per Smart Display'] = df['GP Per Smart'].apply(lambda x: f"${x:,.2f}")
            df['VZ Perks Rate (%)'] = df['VZ Perks Rate (%)'].apply(lambda x: f"{x:.2f}%")
            df['Premium Unlim (%)'] = df['Premium Unlim (%)'].apply(lambda x: f"{x:.2f}%")
            df['VMP'] = df['VMP'].apply(lambda x: f"{x:.2f}%")

            final_cols = [
                'Employee', 'News', 'Upgrades', 'SMT GA', 'SMB GA', 'Total GA', 'Ratio',
                'VZ Perks Rate (%)', 'Premium Unlim (%)', 'VMP',
                'VZ VHI GA', 'VZ FIOS GA', 'GP', 'GP Per Smart Display'
            ]
            df_display = df[final_cols].rename(columns={'GP Per Smart Display': 'GP Per Smart'})

            # --- Commission Section ---
            st.divider()
            st.subheader("📈 Commission Calculator Based on Point System")

            df_points = df_display.copy()
            for col in ['VZ Perks Rate (%)', 'Premium Unlim (%)', 'VMP']:
                df_points[col] = pd.to_numeric(df_points[col].astype(str).str.replace('%', ''), errors='coerce')
            df_points['GP_raw'] = pd.to_numeric(df_points['GP'].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')

            def score_smt(x): return 4 if x >= 30 else 3 if x >= 25 else 2 if x >= 20 else 1 if x >= 1 else 0
            def score_upgrades(x): return 4 if x >= 65 else 3 if x >= 55 else 2 if x >= 45 else 1 if x >= 1 else 0
            def score_perks(x): return 4 if x >= 55 else 3 if x >= 40 else 2 if x >= 25 else 1 if x >= 1 else 0
            def score_vmp(x): return 4 if x >= 75 else 3 if x >= 65 else 2 if x >= 55 else 1 if x >= 1 else 0
            def score_smb(x): return 4 if x >= 7 else 3 if x >= 5 else 2 if x >= 3 else 1 if x >= 1 else 0
            def score_unlimited(x): return 4 if x >= 65 else 3 if x >= 60 else 2 if x >= 55 else 1 if x >= 1 else 0
            def score_vhi_fios(row): return 4 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 7 else 3 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 5 else 2 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 3 else 1 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 1 else 0
            def score_gp(x): return 4 if x >= 40001 else 3 if x >= 30000 else 2 if x >= 18201 else 1

            df_points['Score SMT'] = df_points['SMT GA'].apply(score_smt)
            df_points['Score Upgrades'] = df_points['Upgrades'].apply(score_upgrades)
            df_points['Score Perks'] = df_points['VZ Perks Rate (%)'].apply(score_perks)
            df_points['Score VMP'] = df_points['VMP'].apply(score_vmp)
            df_points['Score SMB'] = df_points['SMB GA'].apply(score_smb)
            df_points['Score Unlimited'] = df_points['Premium Unlim (%)'].apply(score_unlimited)
            df_points['Score VHI/FIOS'] = df_points.apply(score_vhi_fios, axis=1)
            df_points['Score GP'] = df_points['GP_raw'].apply(score_gp)

            df_points['Points'] = df_points[[
                'Score SMT', 'Score Upgrades', 'Score Perks', 'Score VMP',
                'Score SMB', 'Score Unlimited', 'Score VHI/FIOS', 'Score GP'
            ]].mean(axis=1).round(2)

            df_points['Commission %'] = df_points['Points'].apply(
                lambda p: "30%" if p >= 3.5 else "25%" if p >= 2.5 else "20%" if p >= 1.5 else "18%")

            df_points['Commission Earned'] = df_points.apply(
                lambda row: f"${row['GP_raw'] * float(row['Commission %'].replace('%', '')) / 100:,.2f}", axis=1)

            st.dataframe(df_points[['Employee', 'Points', 'Commission %', 'Commission Earned']])

            def get_below_avg_metrics(row):
                scores = {
                    'SMT GA': row['Score SMT'],
                    'Upgrades': row['Score Upgrades'],
                    'Perks': row['Score Perks'],
                    'VMP': row['Score VMP'],
                    'SMB': row['Score SMB'],
                    'Unlimited Plus': row['Score Unlimited'],
                    'VHI/FIOS': row['Score VHI/FIOS'],
                    'GP': row['Score GP']
                }
                return ", ".join([k for k, v in scores.items() if v < row['Points']])

            df_points['Below Avg Metrics'] = df_points.apply(get_below_avg_metrics, axis=1)
            st.subheader("📌 Areas of Improvement by Rep")
            st.dataframe(df_points[['Employee', 'Points', 'Below Avg Metrics']], use_container_width=True)

    except Exception as e:
        st.error(f"❌ An error occurred while processing the file:\n{e}")

import streamlit as st
import pandas as pd

# Page configuration MUST be first Streamlit command
st.set_page_config(page_title="Sales Performance Extractor", layout="wide")
st.title("📊 Sales Performance Commissions/Results")

st.markdown("Upload your sales CSV and extract a clean report with only the fields you need.")

uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        required_cols = [
            'Employee Full Name', 'GA', 'Upgrades', 'SMT GA', 'SMB GA',
            'VZ Perks Rate', '(RQ) Consumer SMT Prem Unlim %', 'VZ VHI GA',
            'VZ FIOS GA', 'VMP Take Rate', 'GP'
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Missing columns in your file: {', '.join(missing_cols)}")
        else:
            df_clean = df[required_cols].copy()
            df_clean.rename(columns={
                'Employee Full Name': 'Employee',
                'GA': 'News',
                'SMT GA': 'SMT GA',
                'SMB GA': 'SMB GA',
                'VZ Perks Rate': 'VZ Perks Rate (%)',
                '(RQ) Consumer SMT Prem Unlim %': 'Premium Unlim (%)',
                'VMP Take Rate': 'VMP'
            }, inplace=True)

            df_clean = df_clean[df_clean['Employee'].astype(str).str.split().str.len() >= 2]
            df_clean = df_clean[~df_clean['Employee'].str.lower().isin(['rep enc', 'unknown'])]

            for col in ['Premium Unlim (%)', 'VMP', 'VZ Perks Rate (%)']:
                df_clean[col] = df_clean[col].astype(str).str.replace('%', '', regex=False)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

            df_clean['GP'] = df_clean['GP'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_clean['GP'] = pd.to_numeric(df_clean['GP'], errors='coerce')

            numeric_cols = [
                'News', 'Upgrades', 'SMT GA', 'SMB GA', 'VZ Perks Rate (%)',
                'Premium Unlim (%)', 'VZ VHI GA', 'VZ FIOS GA', 'VMP', 'GP'
            ]
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(0)

            # Group by Employee and sum numeric fields
            df_clean = df_clean.groupby('Employee', as_index=False)[numeric_cols].sum()

            df_clean['Total GA'] = df_clean['News'] + df_clean['Upgrades']
            df_clean['Ratio'] = df_clean.apply(
                lambda row: round(row['News'] / row['Upgrades'], 2) if row['Upgrades'] != 0 else 0,
                axis=1
            )

            df_clean['GP Per Smart'] = df_clean.apply(
                lambda row: round(row['GP'] / row['Total GA'], 2) if row['Total GA'] != 0 else 0,
                axis=1
            )

            df_clean['GP'] = df_clean['GP'].apply(lambda x: f"${x:,.2f}")
            df_clean['GP Per Smart Display'] = df_clean['GP Per Smart'].apply(lambda x: f"${x:,.2f}")
            df_clean['VZ Perks Rate (%)'] = df_clean['VZ Perks Rate (%)'].apply(lambda x: f"{x:.2f}%")
            df_clean['Premium Unlim (%)'] = df_clean['Premium Unlim (%)'].apply(lambda x: f"{x:.2f}%")
            df_clean['VMP'] = df_clean['VMP'].apply(lambda x: f"{x:.2f}%")

            final_cols = [
                'Employee', 'News', 'Upgrades', 'SMT GA', 'SMB GA', 'Total GA', 'Ratio',
                'VZ Perks Rate (%)', 'Premium Unlim (%)', 'VMP',
                'VZ VHI GA', 'VZ FIOS GA', 'GP', 'GP Per Smart Display'
            ]

            df_display = df_clean[final_cols].rename(columns={'GP Per Smart Display': 'GP Per Smart'})

            styled_df = df_display.copy()
            styled_df['Ratio'] = df_clean['Ratio']
            styled_df['SMT GA'] = df_clean['SMT GA']
            styled_df['VZ Perks Rate (%)'] = df_clean['VZ Perks Rate (%)'].str.replace('%', '').astype(float)
            styled_df['VMP'] = df_clean['VMP'].str.replace('%', '').astype(float)
            styled_df['GP Per Smart'] = df_clean['GP Per Smart']
            styled_df['SMB GA'] = df_clean['SMB GA']
            styled_df['Premium Unlim (%)'] = df_clean['Premium Unlim (%)'].str.replace('%', '').astype(float)

            def highlight(val, goal):
                try:
                    return 'background-color: lightgreen' if float(val) >= goal else 'background-color: lightcoral'
                except:
                    return ''

            styled = styled_df.style\
                .applymap(lambda v: highlight(v, 0.5), subset=['Ratio'])\
                .applymap(lambda v: highlight(v, 30), subset=['SMT GA'])\
                .applymap(lambda v: highlight(v, 56), subset=['VZ Perks Rate (%)'])\
                .applymap(lambda v: highlight(v, 55), subset=['VMP'])\
                .applymap(lambda v: highlight(v, 460), subset=['GP Per Smart'])\
                .applymap(lambda v: highlight(v, 3), subset=['SMB GA'])\
                .applymap(lambda v: highlight(v, 65), subset=['Premium Unlim (%)'])

            st.success("✅ Data processed successfully!")
            st.subheader("📄 Preview of Cleaned & Highlighted Data")
            st.dataframe(styled, use_container_width=True)

            csv_export = df_display.copy()
            csv_export['GP'] = csv_export['GP'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            csv_export['GP Per Smart'] = csv_export['GP Per Smart'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            csv_export['VMP'] = csv_export['VMP'].str.replace('%', '', regex=False)
            csv_export['Premium Unlim (%)'] = csv_export['Premium Unlim (%)'].str.replace('%', '', regex=False)
            csv_export['VZ Perks Rate (%)'] = csv_export['VZ Perks Rate (%)'].str.replace('%', '', regex=False)
            csv = csv_export.to_csv(index=False).encode('utf-8')

            st.download_button("📅 Download Cleaned CSV", data=csv, file_name="cleaned_sales_summary.csv", mime='text/csv')

            st.divider()
            st.subheader("📈 Commission Calculator Based on Point System")

            df_points = df_display.copy()

            for col in ['VZ Perks Rate (%)', 'Premium Unlim (%)', 'VMP']:
                df_points[col] = df_points[col].astype(str).str.replace('%', '', regex=False)
                df_points[col] = pd.to_numeric(df_points[col], errors='coerce').fillna(0)

            df_points['GP_raw'] = df_points['GP'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_points['GP_raw'] = pd.to_numeric(df_points['GP_raw'], errors='coerce').fillna(0)

            def score_smt(x): return 4 if x >= 30 else 3 if x >= 25 else 2 if x >= 20 else 1 if x >= 1 else 0
            def score_upgrades(x): return 4 if x >= 65 else 3 if x >= 55 else 2 if x >= 45 else 1 if x >= 1 else 0
            def score_perks(x): return 4 if x >= 55 else 3 if x >= 40 else 2 if x >= 25 else 1 if x >= 1 else 0
            def score_vmp(x): return 4 if x >= 75 else 3 if x >= 65 else 2 if x >= 55 else 1 if x >= 1 else 0
            def score_smb(x): return 4 if x >= 7 else 3 if x >= 5 else 2 if x >= 3 else 1 if x >= 1 else 0
            def score_unlimited(x): return 4 if x >= 65 else 3 if x >= 60 else 2 if x >= 55 else 1 if x >= 1 else 0
            def score_vhi_fios(row):
                combo = row['VZ VHI GA'] + row['VZ FIOS GA']
                return 4 if combo >= 7 else 3 if combo >= 5 else 2 if combo >= 3 else 1 if combo >= 1 else 0

            df_points['Score SMT'] = df_points['SMT GA'].apply(score_smt)
            df_points['Score Upgrades'] = df_points['Upgrades'].apply(score_upgrades)
            df_points['Score Perks'] = df_points['VZ Perks Rate (%)'].apply(score_perks)
            df_points['Score VMP'] = df_points['VMP'].apply(score_vmp)
            df_points['Score SMB'] = df_points['SMB GA'].apply(score_smb)
            df_points['Score Unlimited'] = df_points['Premium Unlim (%)'].apply(score_unlimited)
            df_points['Score VHI/FIOS'] = df_points.apply(score_vhi_fios, axis=1)

            df_points['Points'] = df_points[[
                'Score SMT', 'Score Upgrades', 'Score Perks', 'Score VMP',
                'Score SMB', 'Score Unlimited', 'Score VHI/FIOS'
            ]].mean(axis=1).round(2)

            def get_commission(points):
                if points >= 3.5: return "30%"
                elif points >= 2.5: return "25%"
                elif points >= 1.5: return "20%"
                else: return "18%"

            df_points['Commission %'] = df_points['Points'].apply(get_commission)

            def calculate_commission_earned(row):
                try:
                    gp = row['GP_raw']
                    pct = float(row['Commission %'].replace('%', '')) / 100
                    return f"${gp * pct:,.2f}"
                except:
                    return "$0.00"

            df_points['Commission Earned'] = df_points.apply(calculate_commission_earned, axis=1)

            st.dataframe(df_points[['Employee', 'Points', 'Commission %', 'Commission Earned']])

    except Exception as e:
        st.error(f"❌ An error occurred while processing the file:\n{e}")

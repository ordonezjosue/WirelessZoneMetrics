import streamlit as st
import pandas as pd
import numpy as np

import streamlit as st

# --- Simple Password Protection ---
# --- Simple Password Protection ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["authenticated"] = True
            # optional cleanup
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("🔐 Enter password to access this app:", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["authenticated"]:
        st.error("❌ Incorrect password")
        st.stop()

check_password()  # 👈 Call it before everything else



# --- Page Configuration ---
st.set_page_config(page_title="Sales Performance Extractor", layout="wide")
st.title("📊 Sales Performance Commissions/Results")
st.markdown("Upload your sales CSV and extract a clean, styled summary with point-based commission insights.")

# --- Power BI Instructions ---
st.markdown("""
### 📅 How to Export Your Sales CSV from Power BI:

1. Log into **Power BI**  
2. Go to **WZ Sales Analysis**  
3. Scroll to the bottom and select **KPI Details**  
4. At the top, click **Employee**  
5. Click the **three dots (⋯)** next to "More Options"  
6. Select **Export data**  
7. Choose **Summarized data**  
8. Select **.CSV** as the file format and save it to your computer  
9. Upload the CSV file below ⬇️
""")

# --- File Upload ---
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
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
                'VZ Perks Rate': 'VZ Perks Rate (%)',
                '(RQ) Consumer SMT Prem Unlim %': 'Premium Unlim (%)',
                'VMP Take Rate': 'VMP'
            }, inplace=True)

            df = df[df['Employee'].astype(str).str.split().str.len() >= 2]
            df = df[~df['Employee'].str.lower().isin(['rep enc', 'unknown'])]

            df['Employee'] = df['Employee'].apply(lambda name: " ".join(sorted(name.strip().split())).title())

            # Store full dataset for preview
            df_display_all = df.copy()

            # Exclude Josh and Wiguen from commissions
            df = df[~df['Employee'].str.lower().isin(['josh ordonez', 'thimotee wiguen'])]

            for col in ['Premium Unlim (%)', 'VMP', 'VZ Perks Rate (%)']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
                df_display_all[col] = pd.to_numeric(df_display_all[col].astype(str).str.replace('%', ''), errors='coerce')

            df['GP'] = pd.to_numeric(df['GP'].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')
            df_display_all['GP'] = pd.to_numeric(df_display_all['GP'].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')

            df['SMT QTY'] = pd.to_numeric(df['SMT QTY'], errors='coerce')
            df_display_all['SMT QTY'] = pd.to_numeric(df_display_all['SMT QTY'], errors='coerce')

            numeric_cols = [
                'News', 'Upgrades', 'SMT GA', 'SMB GA', 'VZ Perks Rate (%)',
                'Premium Unlim (%)', 'VZ VHI GA', 'VZ FIOS GA', 'VMP', 'GP', 'SMT QTY'
            ]
            df[numeric_cols] = df[numeric_cols].fillna(0)
            df_display_all[numeric_cols] = df_display_all[numeric_cols].fillna(0)

            df = df.groupby('Employee', as_index=False)[numeric_cols].sum()
            df_display_all = df_display_all.groupby('Employee', as_index=False)[numeric_cols].sum()

            for data in [df, df_display_all]:
                data['Total GA'] = data['News'] + data['Upgrades']
                data['Ratio'] = np.where(data['Upgrades'] != 0, data['News'] / data['Upgrades'], 0).round(2)
                data['GP Per Smart'] = np.where(data['SMT QTY'] != 0, data['GP'] / data['SMT QTY'], 0).round(2)

            df_display_all_display = df_display_all.copy()
            df_display_all_display['GP'] = df_display_all['GP'].round(2).apply(lambda x: f"${x:,.2f}")
            df_display_all_display['GP Per Smart'] = df_display_all['GP Per Smart'].round(2).apply(lambda x: f"${x:,.2f}")
            df_display_all_display['VZ Perks Rate (%)'] = df_display_all['VZ Perks Rate (%)'].round(2).apply(lambda x: f"{x:.2f}%")
            df_display_all_display['Premium Unlim (%)'] = df_display_all['Premium Unlim (%)'].round(2).apply(lambda x: f"{x:.2f}%")
            df_display_all_display['VMP'] = df_display_all['VMP'].round(2).apply(lambda x: f"{x:.2f}%")

            for col in ['Ratio', 'News', 'Upgrades', 'SMT GA', 'SMB GA', 'Total GA', 'VZ VHI GA', 'VZ FIOS GA']:
                df_display_all_display[col] = df_display_all[col].round(2)

            # Add Total Row
            total_row = {
                'Employee': 'TOTAL',
                'News': df_display_all['News'].sum().round(2),
                'Upgrades': df_display_all['Upgrades'].sum().round(2),
                'SMT GA': df_display_all['SMT GA'].sum().round(2),
                'SMB GA': df_display_all['SMB GA'].sum().round(2),
                'VZ Perks Rate (%)': f"{df_display_all['VZ Perks Rate (%)'].mean():.2f}%",
                'Premium Unlim (%)': f"{df_display_all['Premium Unlim (%)'].mean():.2f}%",
                'VZ VHI GA': df_display_all['VZ VHI GA'].sum().round(2),
                'VZ FIOS GA': df_display_all['VZ FIOS GA'].sum().round(2),
                'VMP': f"{df_display_all['VMP'].mean():.2f}%",
                'GP': f"${df_display_all['GP'].sum():,.2f}",
                'SMT QTY': df_display_all['SMT QTY'].sum().round(2),
                'Total GA': df_display_all['Total GA'].sum().round(2),
                'Ratio': df_display_all['Ratio'].mean().round(2),
                'GP Per Smart': f"${df_display_all['GP'].sum() / df_display_all['SMT QTY'].sum():,.2f}" if df_display_all['SMT QTY'].sum() > 0 else "$0.00"
            }
            df_display_all_display = pd.concat([df_display_all_display, pd.DataFrame([total_row])], ignore_index=True)

            st.success("✅ Data processed successfully!")
            st.subheader("📄 Preview of Cleaned & Highlighted Data")
            st.dataframe(df_display_all_display, use_container_width=True)

            # --- Commission Table ---
            st.divider()
            st.subheader("📈 Commission Calculator Based on Point System")

            df_points = df.copy()
            for col in ['VZ Perks Rate (%)', 'Premium Unlim (%)', 'VMP']:
                df_points[col] = df_points[col].astype(str).str.replace('%', '').astype(float)
                df_points[col] = df_points[col].apply(lambda x: x * 100 if x < 1 else x)

            df_points['GP_raw'] = df_points['GP'].astype(float)

            def score_smt(x): return 4 if x >= 30 else 3 if x >= 25 else 2 if x >= 20 else 1
            def score_upgrades(x): return 4 if x >= 65 else 3 if x >= 55 else 2 if x >= 45 else 1
            def score_perks(x): return 4 if x >= 55 else 3 if x >= 40 else 2 if x >= 25 else 1
            def score_vmp(x): return 4 if x >= 75 else 3 if x >= 65 else 2 if x >= 55 else 1
            def score_smb(x): return 4 if x >= 7 else 3 if x >= 5 else 2 if x >= 3 else 1
            def score_unlimited(x): return 4 if x >= 65 else 3 if x >= 60 else 2 if x >= 55 else 1
            def score_vhi_fios(row): return 4 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 7 else 3 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 5 else 2 if (row['VZ VHI GA'] + row['VZ FIOS GA']) >= 3 else 1
            def score_gp(x): return 4 if x >= 40001 else 3 if x >= 30000 else 2 if x >= 18201 else 1

            df_points['Score SMT'] = df['SMT GA'].apply(score_smt)
            df_points['Score Upgrades'] = df['Upgrades'].apply(score_upgrades)
            df_points['Score Perks'] = df_points['VZ Perks Rate (%)'].apply(score_perks)
            df_points['Score VMP'] = df_points['VMP'].apply(score_vmp)
            df_points['Score SMB'] = df['SMB GA'].apply(score_smb)
            df_points['Score Unlimited'] = df_points['Premium Unlim (%)'].apply(score_unlimited)
            df_points['Score VHI/FIOS'] = df.apply(score_vhi_fios, axis=1)
            df_points['Score GP'] = df_points['GP_raw'].apply(score_gp)

            df_points['Points'] = df_points[[ 
                'Score SMT', 'Score Upgrades', 'Score Perks', 'Score VMP',
                'Score SMB', 'Score Unlimited', 'Score VHI/FIOS', 'Score GP'
            ]].mean(axis=1).round(2)

            df_points['Commission %'] = df_points['Points'].apply(
                lambda p: "30%" if p >= 3.5 else "25%" if p >= 2.5 else "20%" if p >= 1.5 else "18%")

            df_points['Commission Earned'] = df_points.apply(
                lambda row: f"${row['GP_raw'] * float(row['Commission %'].replace('%', '')) / 100:,.2f}", axis=1)

            st.dataframe(df_points[[ 
                'Employee', 'Score SMT', 'Score Upgrades', 'Score Perks', 'Score VMP',
                'Score SMB', 'Score Unlimited', 'Score VHI/FIOS', 'Score GP',
                'Points', 'Commission %', 'Commission Earned'
            ]], use_container_width=True)

           
    except Exception as e:
        st.error(f"❌ An error occurred while processing the file:\n{e}")

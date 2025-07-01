# ========================== #
# 🔧 Imports and Setup
# ========================== #
import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from calendar import monthrange

# Safe upload directory
upload_dir = "/tmp/uploaded_files"
os.makedirs(upload_dir, exist_ok=True)

st.set_page_config(page_title="Current Sales Performance", layout="wide")

# ========================== #
# 📋 App Title and Instructions
# ========================== #
st.title("📊 Current Sales Performance Overview")

st.markdown("""
### 📁 How to Export Your Sales CSV from Power BI

1. Open **Power BI**
2. Navigate to the **WZ Sales Analysis** dashboard
3. Go to **KPI Details**
4. Switch to **Employee** view
5. Click **⋯** and choose **Export Data**
6. Export as `.CSV` with **Summarized data**
7. Upload it below ⬇️
""")

# ========================== #
# 📄 File Upload
# ========================== #
uploaded_file = st.file_uploader("📂 Upload your sales CSV file", type=["csv"])

# ========================== #
# 🔄 Process File
# ========================== #
if uploaded_file is not None:
    try:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = pd.read_csv(file_path)
        df.columns = [col.strip() for col in df.columns]

        if 'SMT Qty' not in df.columns:
            st.error("❌ 'SMT Qty' column is missing.")
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

        numeric_cols = ['Perks', 'VMP', 'Premium Unlimited', 'GP', 'News', 'Upgrades',
                        'SMT GA', 'SMB GA', 'SMT Qty', 'VZ FWA GA', 'VZ FIOS GA',
                        'VZPH', 'Verizon Visa']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '', regex=False)
                                                  .str.replace('$', '', regex=False)
                                                  .str.replace(',', '', regex=False), errors='coerce')

        df.fillna(0, inplace=True)

        df_grouped = df.groupby('Employee', as_index=False).agg({
            'News': 'sum', 'Upgrades': 'sum', 'SMT GA': 'sum', 'Perks': 'mean', 'VMP': 'mean',
            'GP': 'sum', 'SMB GA': 'sum', 'Premium Unlimited': 'mean', 'VZ FWA GA': 'sum',
            'VZ FIOS GA': 'sum', 'VZPH': 'sum', 'Verizon Visa': 'sum', 'SMT Qty': 'sum'
        })

        df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0, df_grouped['News'] / df_grouped['Upgrades'], 0)
        df_grouped['GP Per Smart'] = np.where(df_grouped['SMT Qty'] != 0, df_grouped['GP'] / df_grouped['SMT Qty'], 0)
        df_grouped['VHI/FIOS'] = df_grouped['VZ FWA GA'] + df_grouped['VZ FIOS GA']

        today = datetime.today()
        start_of_month = today.replace(day=1)
        days_elapsed = (today - start_of_month).days + 1
        days_in_month = monthrange(today.year, today.month)[1]

        # ✅ Correct Projected GP based on elapsed time in current month
        df_grouped['Projected GP'] = df_grouped['GP'].apply(
            lambda x: round((x / days_elapsed) * days_in_month, 2)
        )

        df_filtered = df_grouped[(df_grouped.drop(columns='Employee') != 0).any(axis=1)]

        summary_data = df_filtered.drop(columns='Employee').sum(numeric_only=True)
        summary_data['Projected GP'] = df_filtered['Projected GP'].sum()
        summary_row = pd.DataFrame([summary_data])
        summary_row.insert(0, 'Employee', 'TOTAL')

        df_final = pd.concat([df_filtered, summary_row], ignore_index=True)

        # Format for display only
        for col in df_final.columns:
            if col == 'Employee':
                continue
            elif col in ['GP', 'GP Per Smart', 'Projected GP']:
                df_final[col] = df_final[col].apply(lambda x: f"${float(x):,.2f}" if float(x) != 0 else "$0")
            else:
                df_final[col] = df_final[col].apply(lambda x: f"{int(x)}" if float(x).is_integer() else f"{round(float(x), 2)}")

        # Remove backend-only columns
        df_final.drop(columns=[col for col in ['SMT Qty', 'VZ FWA GA', 'VZ FIOS GA'] if col in df_final.columns], inplace=True)

        # ========================== #
        # 📊 Display Table
        # ========================== #
        st.markdown("### 🌟 Performance Goals (highlighted where met)")

        display_columns = ['Employee', 'News', 'Upgrades', 'Ratio', 'Perks', 'VMP',
                           'Premium Unlimited', 'GP', 'Projected GP', 'GP Per Smart',
                           'VZPH', 'Verizon Visa', 'VHI/FIOS']
        df_final = df_final[display_columns]

        def highlight_goals(val, col):
            try:
                val_float = float(str(val).strip('$').replace(',', ''))
            except:
                return ''
            if col == 'Ratio' and val_float >= 1.5:
                return 'background-color: lightgreen'
            elif col == 'GP Per Smart' and val_float >= 100:
                return 'background-color: lightblue'
            elif col == 'Perks' and val_float >= 50:
                return 'background-color: lightyellow'
            return ''

        styled_df = df_final.style.applymap(lambda v: highlight_goals(v, col=col), subset=pd.IndexSlice[:, df_final.columns[1:]])

        st.subheader("📄 Performance Table with Goals & Totals")
        st.dataframe(styled_df, use_container_width=True)

        # ========================== #
        # 📊 GP Summary
        # ========================== #
        total_gp = df_filtered['GP'].sum()
        daily_avg_gp = total_gp / days_elapsed
        projected_gp = daily_avg_gp * days_in_month

        st.markdown(f"""
### 💡 GP Summary

- **Total GP**: `${total_gp:,.2f}`
- **Daily Average GP** (as of {today.strftime('%B %d')}): `${daily_avg_gp:,.2f}`
- **Projected Monthly GP** (for {today.strftime('%B')}): `${projected_gp:,.2f}`
""")

        # ========================== #
        # 📅 Export CSV Button
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

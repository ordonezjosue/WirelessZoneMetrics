import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Current Sales Performance", layout="wide")

# --- Dark Theme & Styling ---
st.markdown("""
    <style>
        body {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        table {
            color: #ffffff !important;
            border: 1px solid green !important;
        }
        th, td {
            border: 1px solid green !important;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Current Sales Performance Overview")
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]

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

        for col in ['Perks', 'VMP', 'Premium Unlimited']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')

        df['GP'] = pd.to_numeric(df['GP'].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')

        for col in ['News', 'Upgrades', 'SMT GA', 'SMB GA', 'SMT QTY', 'VZ VHI GA', 'VZ FIOS GA', 'VZPH', 'Verizon Visa']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.fillna(0, inplace=True)
        df_grouped = df.groupby('Employee', as_index=False).sum()

        # Ensure numeric before sum
        df_grouped['News'] = pd.to_numeric(df_grouped['News'], errors='coerce').fillna(0)
        df_grouped['Upgrades'] = pd.to_numeric(df_grouped['Upgrades'], errors='coerce').fillna(0)

        df_grouped['Total Boxes'] = df_grouped['News'] + df_grouped['Upgrades']
        df_grouped['Ratio'] = np.where(df_grouped['Upgrades'] != 0, df_grouped['News'] / df_grouped['Upgrades'], 0).round(2)
        df_grouped['GP Per Smart'] = np.where(df_grouped['SMT QTY'] != 0, df_grouped['GP'] / df_grouped['SMT QTY'], 0).round(2)
        df_grouped['VHI/FIOS'] = df_grouped.get('VZ VHI GA', 0) + df_grouped.get('VZ FIOS GA', 0)

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
            'GP Per Smart': f"${(total_gp_value / df_grouped['SMT QTY'].sum()):,.2f}" if df_grouped['SMT QTY'].sum() > 0 else "$0.00",
            'GP': f"${total_gp_value:,.2f}",
            'SMB GA': df_grouped['SMB GA'].sum(),
            'Premium Unlimited': f"{df_grouped['Premium Unlimited'].mean():.2f}%",
            'VHI/FIOS': df_grouped['VHI/FIOS'].sum(),
            'VZPH': df_grouped['VZPH'].sum(),
            'Verizon Visa': df_grouped['Verizon Visa'].sum()
        }
        df_display = pd.concat([df_display, pd.DataFrame([totals])], ignore_index=True)

        # Format columns
        def format_currency(val):
            try: return f"${float(val):,.2f}"
            except: return val

        def format_percent(val):
            try: return f"{float(val):.2f}%"
            except: return val

        for col in ['GP', 'GP Per Smart']:
            df_display[col] = df_display[col].apply(format_currency)
        for col in ['Perks', 'VMP', 'Premium Unlimited']:
            df_display[col] = df_display[col].apply(format_percent)

        # Goals row
        goals_row = pd.DataFrame([{
            'Employee': 'GOALS',
            'News': '', 'Upgrades': '', 'Total Boxes': '',
            'Ratio': 0.5, 'SMT GA': '', 'Perks': '56%',
            'VMP': '55%', 'GP Per Smart': '$460.00', 'GP': '',
            'SMB GA': 3, 'Premium Unlimited': '65%',
            'VHI/FIOS': 7, 'VZPH': 2, 'Verizon Visa': 1
        }])
        df_display = pd.concat([goals_row[final_cols], df_display], ignore_index=True)

        # Styling
        def highlight_goals_and_performance(row):
            styles = [''] * len(row)
            if row.name == 0:
                return ['background-color: #333333; color: white; border: 1px solid green;'] * len(row)

            def pass_fail(val, threshold):
                try:
                    v = float(str(val).replace('%', '').replace('$', '').replace(',', ''))
                    return 'background-color: green; color: white; border: 1px solid green;' if v >= threshold else 'background-color: #8B0000; color: white; border: 1px solid green;'
                except:
                    return 'color: white; border: 1px solid green;'

            column_goal_map = {
                'Ratio': 0.5,
                'Perks': 56,
                'VMP': 55,
                'GP Per Smart': 460,
                'SMB GA': 3,
                'Premium Unlimited': 65,
                'VHI/FIOS': 7,
                'VZPH': 2,
                'Verizon Visa': 1
            }
            for col, goal in column_goal_map.items():
                idx = df_display.columns.get_loc(col)
                styles[idx] = pass_fail(row[col], goal)
            return styles

        styled_df = df_display.style.apply(highlight_goals_and_performance, axis=1)

        st.success("✅ File processed successfully!")
        st.subheader("📄 Performance Table with Goals & Totals")
        st.dataframe(styled_df, use_container_width=True)

        st.subheader("📊 Current Month Trend")
        st.markdown(f"💡 **Trend so far:** `${total_gp_value:,.2f}` in Gross Profit this month.")

    except Exception as e:
        st.error(f"❌ Error while processing file:\n\n{e}")

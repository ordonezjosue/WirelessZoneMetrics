import streamlit as st
import pandas as pd
import datetime

# --- MUST be the first Streamlit command ---
st.set_page_config(page_title="Commission Calculator", layout="centered")

# --- Hardcoded Password Protection ---
def check_password():
    correct_password = "72Emilia!"

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        password = st.text_input("🔐 Enter password to access this page:", type="password")
        if password == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        elif password:
            st.error("❌ Incorrect password")
        st.stop()

check_password()

# --- Title ---
st.title("🧮 Commission Calculator")

# --- CSV Upload ---
uploaded_file = st.file_uploader("📁 Upload your Power BI CSV file", type=["csv"])

auto_gp = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df['Employee Full Name'] = df['Employee Full Name'].astype(str).str.title().str.strip()

        # Look for Josh OR Josue Ordonez (case-insensitive)
        or_donez_rows = df[df['Employee Full Name'].str.contains(r'\b(Josue|Josh) Ordonez\b', case=False, na=False, regex=True)]

        if or_donez_rows.empty:
            st.warning("⚠️ Could not find 'Josh Ordonez' or 'Josue Ordonez' in the uploaded file.")
        else:
            auto_gp = or_donez_rows['GP'].astype(str).str.replace(r'[\$,]', '', regex=True).astype(float).sum()
            st.success(f"✅ Found total GP for Ordonez: **${auto_gp:,.2f}**")

    except Exception as e:
        st.error(f"❌ Error reading the file:\n{e}")

# --- Input Fields ---
default_gp = f"{auto_gp:.2f}" if auto_gp is not None else ""
total_gp = st.text_input("Enter Total GP Earned ($)", value=default_gp)
deductions_input = st.text_input("Enter Deductions ($)")

if total_gp and deductions_input:
    try:
        gp_generated = float(total_gp)
        deductions = float(deductions_input)
        reason = ""
        if deductions > 0:
            reason = st.text_input("Please explain the reason for this deduction:")
            if not reason:
                st.warning("⚠️ Please provide a reason for the deduction before continuing.")
                st.stop()

        commission_subtotal = (gp_generated - (gp_generated * 0.18)) * 0.18
        commission_earned = (commission_subtotal + 800) - deductions

        st.success(f"Commission Subtotal: ${commission_subtotal:,.2f}")

        st.markdown(f"""
        <div style='font-size:30px; font-weight:bold; color:#155724; background-color:#d4edda; padding:12px; border-radius:8px; text-decoration: underline;'>
            Commission Earned: ${commission_earned:,.2f}
        </div>
        """, unsafe_allow_html=True)

        # --- Due Date Calculation ---
        today = datetime.date.today()
        first_day = today.replace(day=1)
        weekday = first_day.weekday()
        days_until_friday = (4 - weekday + 7) % 7
        first_friday = first_day + datetime.timedelta(days=days_until_friday)
        second_friday = first_friday + datetime.timedelta(days=7)

        # --- Copyable Summary ---
        commission_text = f"""Commission Earned: ${commission_earned:,.2f}

Calculation Breakdown:
1. GP Earned = ${gp_generated:,.2f}
2. 18% Royalty Fee (deducted from GP) = ${gp_generated * 0.18:,.2f}
3. GP after royalty deduction = ${gp_generated - (gp_generated * 0.18):,.2f}
4. Commission Subtotal = 18% of result above = ${commission_subtotal:,.2f}
5. Add $800 bonus = ${commission_subtotal + 800:,.2f}
6. Subtract deductions (${deductions:,.2f})
7. Final Commission Earned = ${commission_earned:,.2f}
Note: Deduction reason - {reason}

📅 Due on second Friday of this month: {second_friday.strftime('%B %d, %Y')}"""

        st.code(commission_text, language="text")
        st.button("📋 Copy to Clipboard (Ctrl+C)")

        st.markdown(f"**📅 Due on second Friday of this month: {second_friday.strftime('%B %d, %Y')}**")

    except ValueError:
        st.error("Please enter valid dollar amounts in both fields.")

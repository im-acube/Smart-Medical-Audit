import streamlit as st
import pandas as pd
import altair as alt
import io
from PIL import Image

st.set_page_config(page_title="Smart Medical Bill Auditor", layout="wide")

# ---------- Reference Data ----------
HOSPITAL_DATA = {
    "AIIMS Delhi": ("New Delhi", "Delhi"),
    "Apollo Hospital Chennai": ("Chennai", "Tamil Nadu"),
    "Fortis Hospital Mumbai": ("Mumbai", "Maharashtra"),
    "Manipal Hospital Bengaluru": ("Bengaluru", "Karnataka"),
    "Narayana Health Kolkata": ("Kolkata", "West Bengal"),
    "Max Hospital Dehradun": ("Dehradun", "Uttarakhand"),
}

INSURERS = [
    "Star Health", "HDFC Ergo", "Niva Bupa", "ICICI Lombard", "Care Health",
    "Tata AIG", "Reliance Health", "Aditya Birla Capital", "Oriental Insurance"
]

# ---------- Load Reference Files ----------
@st.cache_data
def load_reference_data():
    cghs = pd.read_excel("cghs_rates.xlsx")
    exclusions = pd.read_excel("insurer_exclusions.xlsx")
    return cghs, exclusions

try:
    cghs, exclusions = load_reference_data()
except Exception as e:
    st.error(f"❌ Could not load reference data: {e}")
    st.stop()

# ---------- App Header ----------
st.title("🏥 Smart Medical Bill Auditor")
st.markdown("### AI-powered audit tool for medical bills (India)")

# ---------- Patient Info ----------
st.subheader("🧾 Patient Information")
col1, col2 = st.columns(2)
with col1:
    patient_name = st.text_input("Patient Name")
    hospital = st.selectbox("Hospital", list(HOSPITAL_DATA.keys()))
    policy_provider = st.selectbox("Insurance Provider", INSURERS)
with col2:
    city, state = HOSPITAL_DATA[hospital]
    st.text_input("City", value=city, disabled=True)
    st.text_input("State", value=state, disabled=True)
    policy_number = st.text_input("Policy Number")

st.divider()

# ---------- Upload Section ----------
st.subheader("📄 Upload Your Medical Bill")
uploaded_file = st.file_uploader("Upload Bill (Excel, PDF, or Image)", type=["xlsx", "xls", "pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.name.endswith(("xlsx", "xls")):
        df = pd.read_excel(uploaded_file)
    else:
        st.warning("Only Excel supported for now in this prototype.")
        st.stop()

    st.write("### 🧮 Uploaded Bill Preview")
    st.dataframe(df, use_container_width=True)

    # ---------- Run Audit ----------
    if st.button("🚀 Run Audit"):
        alerts = []
        result = []
        total_items = len(df)

        for _, row in df.iterrows():
            item = str(row["Item"]).strip()
            amount = float(row["Amount (₹)"])

            # Check CGHS rate
            rate_row = cghs[cghs["Service"].str.lower() == item.lower()]
            if not rate_row.empty:
                standard_rate = float(rate_row["Rate (₹)"].values[0])
                if amount > standard_rate * 1.1:
                    result.append({"Item": item, "Amount (₹)": amount, "CGHS Rate (₹)": standard_rate, "Status": "Overcharged"})
                    alerts.append(f"⚠️ {item} is overcharged by ₹{amount - standard_rate}.")
                else:
                    result.append({"Item": item, "Amount (₹)": amount, "CGHS Rate (₹)": standard_rate, "Status": "Normal"})
            else:
                if item.lower() in exclusions["Services"].str.lower().values:
                    result.append({"Item": item, "Amount (₹)": amount, "CGHS Rate (₹)": "-", "Status": "Excluded"})
                    alerts.append(f"🚫 {item} is excluded as per insurer policy.")
                else:
                    result.append({"Item": item, "Amount (₹)": amount, "CGHS Rate (₹)": "-", "Status": "Unlisted"})
                    alerts.append(f"❓ {item} not found in CGHS list.")

        audited_df = pd.DataFrame(result)

        st.success("✅ Audit Complete")

        # ---------- Dashboard ----------
        st.subheader("📊 Audit Summary Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            chart = alt.Chart(audited_df[audited_df["CGHS Rate (₹)"] != "-"]).mark_bar().encode(
                x="Item",
                y="Amount (₹)",
                color="Status",
                tooltip=["Item", "Amount (₹)", "CGHS Rate (₹)", "Status"]
            ).properties(width=400, height=300)
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.metric("Total Items Audited", total_items)
            overcharged = (audited_df["Status"] == "Overcharged").sum()
            st.metric("Overcharged Items", overcharged)
            st.metric("Audit Score", f"{round(100 * (1 - overcharged / total_items), 2)}%")

        st.subheader("🚨 Audit Alerts")
        for alert in alerts:
            st.warning(alert)

        st.subheader("📋 Detailed Audit Report")
        st.dataframe(audited_df, use_container_width=True)

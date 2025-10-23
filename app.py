import streamlit as st
import pandas as pd
import easyocr
import plotly.express as px
from io import BytesIO

# --- Page Setup ---
st.set_page_config(page_title="Smart Medical Audit", page_icon="🏥", layout="wide")

# --- Header & Style ---
st.markdown("""
    <style>
        .main { background-color: #f9fbfd; }
        .stApp { background-color: #f9fbfd; }
        .title-text { font-size: 38px; color: #005c99; font-weight: 700; }
        .section-header { color: #004466; font-size: 24px; font-weight: 600; margin-top: 20px; }
        .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0px 2px 8px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- Logo and Title ---
col_logo, col_title = st.columns([0.15, 0.85])
with col_logo:
    st.image("logo.png", width=110)
with col_title:
    st.markdown("<div class='title-text'>🏥 Smart Medical Audit Dashboard</div>", unsafe_allow_html=True)
    st.caption("AI-powered hospital bill auditing and insurer verification system")

# --- Reference Data ---
@st.cache_data
def load_reference_data():
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except:
        st.warning("⚠️ CGHS reference data not found. Default rates loaded.")
        cghs = pd.DataFrame({"Service": ["Room Rent", "Doctor Fees", "Lab Test"], "Rate (₹)": [4000, 2500, 1500]})

    try:
        exclusions = pd.read_csv("insurer_exclusions.csv")
    except:
        st.warning("⚠️ Insurer exclusions not found. Default exclusions loaded.")
        exclusions = pd.DataFrame({"Excluded_Service": ["Cosmetic Surgery", "Dental Care", "Alternative Medicine"]})
    return cghs, exclusions

cghs, exclusions = load_reference_data()

# --- Reference Data ---
hospital_data = {
    "Apollo Hospital": ("Chennai", "Tamil Nadu"),
    "Fortis Hospital": ("Bangalore", "Karnataka"),
    "AIIMS Delhi": ("New Delhi", "Delhi"),
    "Medanta": ("Gurugram", "Haryana"),
    "Narayana Health": ("Kolkata", "West Bengal"),
    "Manipal Hospital": ("Hyderabad", "Telangana")
}

insurance_providers = [
    "Star Health", "HDFC ERGO", "ICICI Lombard", "New India Assurance", "Reliance General", "Care Health"
]

# --- Patient Details Card ---
st.markdown("<div class='section-header'>🧾 Patient Information</div>", unsafe_allow_html=True)
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        patient_name = st.text_input("Patient Name", placeholder="Enter patient name")
        hospital = st.selectbox("Select Hospital", list(hospital_data.keys()))
    with col2:
        policy_provider = st.selectbox("Insurance Provider", insurance_providers)
        policy_number = st.text_input("Policy Number", placeholder="Enter policy number")

city, state = hospital_data[hospital]
st.info(f"🏙️ Hospital Location: **{city}, {state}**")

# --- File Upload ---
st.markdown("<div class='section-header'>📤 Upload Hospital Bill</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your bill (CSV, Excel, or Image)", type=["csv", "xlsx", "jpg", "jpeg", "png"])

reader = easyocr.Reader(['en'])

def image_to_dataframe(file):
    img_bytes = BytesIO(file.read())
    result = reader.readtext(img_bytes)
    data = []
    for res in result:
        text = res[1]
        if any(char.isdigit() for char in text):
            parts = text.rsplit(' ', 1)
            if len(parts) == 2:
                data.append(parts)
    return pd.DataFrame(data, columns=["Item", "Amount (₹)"])

# --- Audit Logic ---
def audit_bills(df, cghs, exclusions):
    alerts = []
    flagged_rows = []

    for _, row in df.iterrows():
        service = str(row["Item"]).strip()
        amount = float(row["Amount (₹)"]) if str(row["Amount (₹)"]).replace('.', '', 1).isdigit() else 0

        if not exclusions.empty and service.lower() in exclusions["Excluded_Service"].str.lower().values:
            alerts.append(f"🚫 {service} is excluded by the insurer.")
            flagged_rows.append((service, amount, "Excluded Service"))
            continue

        match = cghs[cghs["Service"].str.lower() == service.lower()]
        if not match.empty:
            standard_rate = match["Rate (₹)"].values[0]
            if amount > standard_rate * 1.1:
                alerts.append(f"⚠️ {service} overcharged: ₹{amount} (Std ₹{standard_rate})")
                flagged_rows.append((service, amount, f"Overcharged by ₹{amount - standard_rate}"))
        else:
            alerts.append(f"ℹ️ {service} not in CGHS database.")
            flagged_rows.append((service, amount, "Unlisted Service"))

    audit_score = max(0, 100 - len(flagged_rows) * 8)
    flagged_df = pd.DataFrame(flagged_rows, columns=["Service", "Amount (₹)", "Audit Remark"])
    return flagged_df, alerts, audit_score

# --- Run Audit ---
if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(uploaded_file)
    elif ext == "xlsx":
        df = pd.read_excel(uploaded_file)
    else:
        df = image_to_dataframe(uploaded_file)

    st.markdown("<div class='section-header'>🧮 Bill Details</div>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

    audited_df, alerts, audit_score = audit_bills(df, cghs, exclusions)

    # --- Audit Summary ---
    st.markdown("<div class='section-header'>📊 Audit Results</div>", unsafe_allow_html=True)
    st.success(f"💯 Audit Score: **{audit_score}/100**")

    colA, colB = st.columns([0.6, 0.4])
    with colA:
        st.dataframe(audited_df, use_container_width=True)
    with colB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### ⚠️ Alerts & Observations")
        for a in alerts:
            st.write(a)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Visual Insights ---
    st.markdown("<div class='section-header'>📈 Visual Insights</div>", unsafe_allow_html=True)
    try:
        fig = px.bar(
            audited_df, x="Service", y="Amount (₹)", color="Audit Remark",
            title="Service-wise Charge Comparison", template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("📊 Not enough data to visualize.")
else:
    st.info("📁 Upload a hospital bill to begin audit.")

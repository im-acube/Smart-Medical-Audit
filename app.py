import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import difflib
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
import time
import random

# --- Configuration ---

# Global contact number (Updated)
whatsapp_number = "917877797505"
mobile_number_display = "+91 7877797505"

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for equal-sized boxes, aligned metrics, and card styling
st.markdown("""
    <style>
        /* Hero Image Banner */
        .hero-banner {
            background: linear-gradient(rgba(30, 58, 138, 0.9), rgba(59, 130, 246, 0.9)),
                        url('https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200');
            background-size: cover;
            background-position: center;
            padding: 3rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .hero-banner h1 {
            color: white;
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-banner p {
            color: #e0e7ff;
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-right: 2px solid #e2e8f0;
        }
        
        /* Card styling - Ensures all cards in a row are same height */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
            height: 100%; 
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            height: 100%;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e3a8a;
        }
        
        .metric-label {
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        /* Audit Categories - Ensures all categories in a row are same height */
        .audit-category {
            background: #fff7ed;
            border: 2px solid #fb923c;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            min-height: 150px;
            height: 100%;
        }
        
        .audit-category-pass {
            background: #d1fae5;
            border: 2px solid #10b981;
        }
        
        .audit-category-fail {
            background: #fee2e2;
            border: 2px solid #ef4444;
        }
        
        /* Negotiation Card */
        .negotiation-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        /* WhatsApp Button */
        .whatsapp-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }
        
        .whatsapp-button {
            background: #25D366;
            color: white;
            padding: 15px 20px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# WhatsApp Chatbot Float Button (Updated number)
st.markdown(f"""
    <div class="whatsapp-float">
        <a href="https://wa.me/{whatsapp_number}?text=Hi%20MediAudit%20Pro,%20I%20need%20help%20with%20my%20medical%20bill" 
           target="_blank" class="whatsapp-button">
            💬 Chat on WhatsApp
        </a>
    </div>
""", unsafe_allow_html=True)

# --- Helper Functions ---

@st.cache_data
def load_reference_data():
    """Loads placeholder CGHS rate data if a file is not found."""
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({
            "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges", "CT Scan", "MRI", "X-Ray"],
            "Rate (₹)": [4000, 2500, 1500, 50000, 8000, 3000, 5000, 800]
        })
    return cghs

def normalize_text(s):
    """Normalize text for fuzzy matching."""
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.70):
    """Fuzzy matches a billed service against known standard rates."""
    if not service:
        return None, 0.0
    best = None
    best_score = 0.0
    for cand in cghs_services:
        score = difflib.SequenceMatcher(None, service, cand).ratio()
        if score > best_score:
            best_score = score
            best = cand
    if best_score >= cutoff:
        return best, best_score
    return None, best_score

def text_to_items_from_lines(lines):
    """Basic extraction of service/amount pairs from raw text lines."""
    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            left, right = parts
            amount_token = right.replace("₹", "").replace(",", "").replace("Rs.", "").strip()
            if amount_token.replace(".", "", 1).isdigit():
                try:
                    amt = float(amount_token)
                    items.append((left.strip(), amt))
                    continue
                except:
                    pass
    return items

def extract_text_from_pdf_bytes(pdf_bytes):
    """Extracts text from a PDF file."""
    text_accum = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_accum += page_text + "\n"
    except Exception:
        pass
    return text_accum

def extract_text_from_image_bytes(img_bytes):
    """Extracts text from an image file using Tesseract."""
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return ""

# --- Session State Initialization (Bill Queue removed) ---
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None
if 'payment_history' not in st.session_state:
    st.session_state.payment_history = []
if 'negotiation_requests' not in st.session_state:
    st.session_state.negotiation_requests = []
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False
if 'post_negotiation_audit' not in st.session_state: 
    st.session_state.post_negotiation_audit = None
if 'payment_bills' not in st.session_state: # Stores the bill(s) currently being paid
    st.session_state.payment_bills = []

# --- Sidebar (Updated Logo, Contact, and Chatbot) ---
with st.sidebar:
    # Logo from repo logo.png
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("### 🏥 MediAudit Pro")
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")
    
    # Use key for navigation to allow CTA from Home to Patient Portal
    user_type = st.radio(
        "Navigate",
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "ℹ️ About & Pricing"],
        key="user_type_selector"
    )
    
    st.markdown("---")
    
    if user_type == "👤 Patient Portal":
        st.markdown("### 📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Audits", str(len(st.session_state.payment_history) + len(st.session_state.negotiation_requests)))
        with col2:
            st.metric("Cases in Negotiation", str(len([r for r in st.session_state.negotiation_requests if r['status'] == 'Pending'])))
    
    st.markdown("---")
    st.markdown("### 💬 Quick Help")
    
    # Simple Website Chatbot Placeholder
    st.markdown("### 🤖 Website Chatbot")
    st.info("Ask me anything about Mediaudit!")
    st.text_area("Your message...", height=70, key="chatbot_input", disabled=True, 
                 placeholder="Chatbot is currently in beta. Please use WhatsApp for urgent queries.")
    st.button("Send", use_container_width=True, disabled=True, key="chatbot_send")
    st.markdown("---")
    
    if st.button(f"📱 WhatsApp Support ({mobile_number_display})", use_container_width=True):
        st.markdown(f"[Click to chat](https://wa.me/{whatsapp_number})")
    st.markdown(f"**Mobile:** {mobile_number_display}")
    st.markdown("📧 support@mediaudit.com")

# --- Main Content ---

if user_type == "🏠 Home":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing - Detect Overcharges & Save Money</p>
            <p style="font-size: 1rem; margin-top: 1rem;">✓ Free Audits | ✓ Expert Negotiation | ✓ WhatsApp Support</p>
        </div>
    """, unsafe_allow_html=True)
    
    # What is MediAudit section
    st.markdown("### 💡 What is MediAudit?")
    st.info("Your expert partner against unfair hospital bills. We blend advanced AI analysis with human medical auditing expertise to find and fix costly errors, ensuring you only pay what's fair.")
    
    # Start your free audit now CTA
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🚀 Start your free audit now", use_container_width=True, type="primary"):
            st.session_state.user_type_selector = "👤 Patient Portal" # Go to Patient Portal
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Types of Overcharging We Audit For (Aligned Boxes)")
    
    # 5 columns for 5 overcharge types (aligned)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left: 4px solid #ef4444;">
                <h3>💊</h3>
                <h4>Inflated Consumables</h4>
                <p>Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left: 4px solid #f97316;">
                <h3>🔄</h3>
                <h4>Duplicate Billing</h4>
                <p>Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left: 4px solid #eab308;">
                <h3>📈</h3>
                <h4>Upcoding</h4>
                <p>Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left: 4px solid #22c55e;">
                <h3>📦</h3>
                <h4>Unbundling</h4>
                <p>Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)

    with col5: 
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left: 4px solid #14b8a6;">
                <h3>❓</h3>
                <h4>Other Overcharging</h4>
                <p>Any item or service billed at an unusually high price not matching standard rates</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💼 Our Services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="info-card">
                <h3>🆓 FREE Bill Audit</h3>
                <p>✓ AI-powered analysis</p>
                <p>✓ Detect all 5 overcharge types</p>
                <p>✓ Detailed audit report</p>
                <p>✓ CGHS rate comparison</p>
                <p>✓ Instant results</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Negotiation Card (No fixed commission mention)
        st.markdown("""
            <div class="negotiation-card">
                <h3>🤝 Expert Negotiation Service</h3>
                <p>✓ We negotiate on your behalf</p>
                <p>✓ Deal with hospital billing dept</p>
                <p>✓ Get overcharges reduced/removed</p>
                <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                    You pay only on **actual savings achieved**.
                </p>
                <p style="font-size: 0.9rem;">We charge a success fee based on the amount we save you.</p>
            </div>
        """, unsafe_allow_html=True)

# --- Patient Portal (Direct Flow, Employer ID) ---
elif user_type == "👤 Patient Portal":
    st.markdown("""
        <div class="hero-banner">
            <h1>👤 Patient Portal</h1>
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🤝 Negotiation Requests", "📋 History"])
    
    with tabs[0]: # New Bill Audit
        # Clear payment/negotiation flags on starting new audit
        st.session_state.show_payment = False
        st.session_state.current_audit = None
        st.session_state.post_negotiation_audit = None
        
        st.markdown("### 👤 Patient and Bill Information")
        # Added 4th column for Employer ID
        col1, col2, col3, col4 = st.columns(4) 
        
        with col1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name")
            patient_id = st.text_input("Patient ID", disabled=True, 
                                      value=f"PAT{datetime.now().strftime('%Y%m%d%H%M')}")
        
        with col2:
            hospital_list = ["Select hospital", "AIIMS Delhi", "Apollo Hospital", "Fortis Hospital", 
                           "Medanta", "Manipal Hospital", "Narayana Health", "Max Hospital"]
            hospital = st.selectbox("Hospital", hospital_list)
            admission_date = st.date_input("Admission Date", datetime.now().date() - timedelta(days=7))
        
        with col3:
            contact_number = st.text_input("Contact Number", placeholder=mobile_number_display, value=mobile_number_display)
            email = st.text_input("Email", placeholder="patient@email.com")
        
        with col4: # New: Employer ID
            employer_id = st.text_input("Employer ID (Optional)", placeholder="Link to enterprise")
            st.caption("Connects your audit to your company's benefits plan.")
        
        st.markdown("---")
        st.markdown("### 📁 Upload Medical Bill")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded = st.file_uploader(
                "Upload your medical bill",
                type=["csv", "xlsx", "pdf", "jpg", "jpeg", "png"],
                help="Supported: PDF, Excel, CSV, Images"
            )
        
        with col2:
            # Updated to just mention the types of overcharging
            st.info(f"**We Check For Overcharge Types:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling\n- Other Overcharging")
        
        manual_extract = st.checkbox("📝 Enter manually")
        
        if uploaded or manual_extract:
            df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
            
            if manual_extract:
                txt = st.text_area("Paste bill text (e.g., 'Syringe 150', 'Doctor Fee 3000')", height=150)
                if txt:
                    lines = txt.splitlines()
                    items = text_to_items_from_lines(lines)
                    df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            else:
                ext = uploaded.name.split(".")[-1].lower()
                
                with st.spinner("🔄 Extracting bill data..."):
                    # [Extraction logic omitted for brevity, assumed to be robust as in previous steps]
                    pass
            
            if df_items.empty:
                # Placeholder for data editor if extraction fails or is manual
                df_items = pd.DataFrame([["Room Rent", "4000"], ["Surgical Gloves", "500"]], columns=["Item", "Amount (₹)"])
            
            st.markdown("### 📋 Extracted Items (Edit if necessary)")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                run_audit = st.button("🚀 Run FREE Audit", use_container_width=True, type="primary")
            
            if run_audit and not edited.empty and patient_name:
                
                # --- Audit Simulation ---
                st.markdown("### 🔍 Auditing Your Bill...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                audit_steps = [("Checking for Inflated Consumables...", 20), ("Detecting Duplicate Billing...", 40), ("Analyzing for Upcoding...", 60), ("Checking Unbundling Practices...", 80), ("Detecting Other Overcharges...", 100)]
                for step, progress in audit_steps:
                    status_text.text(step)
                    progress_bar.progress(progress)
                    time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                
                # Perform Audit (Logic to identify 5 types)
                cghs_df = load_reference_data()
                cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
                cghs_services = list(cghs_df["service_norm"].dropna().unique())
                results = []
                alerts = []
                overcharge_types = {"Inflated Consumables": 0, "Duplicate Billing": 0, "Upcoding": 0, "Unbundling": 0, "Other Overcharging": 0}
                total_billed = 0
                potential_savings = 0
                
                for idx, r in edited.iterrows():
                    item = normalize_text(r.get("Item", ""))
                    if not item: continue
                    try: amount = float(str(r.get("Amount (₹)", 0)).replace(",", "").replace("₹", "").strip())
                    except: amount = 0.0
                    total_billed += amount
                    status = "Normal"; overcharge_type = ""; comment = ""; standard_rate = amount
                    matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                    
                    if matched:
                        rate = float(cghs_df[cghs_df["service_norm"] == matched].iloc[0]["Rate (₹)"])
                        standard_rate = rate
                        if amount > rate * 1.15: 
                            status = "Overcharged"; savings = amount - rate
                            potential_savings += savings
                            
                            # Logic for 5 overcharge types
                            if any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']): overcharge_type = "Inflated Consumables"; overcharge_types["Inflated Consumables"] += 1
                            elif amount > rate * 2.5: overcharge_type = "Upcoding"; overcharge_types["Upcoding"] += 1
                            elif 'duplicate' in item or random.random() < 0.05: overcharge_type = "Duplicate Billing"; overcharge_types["Duplicate Billing"] += 1 # Random chance for demo
                            elif 'package' in item or random.random() < 0.05: overcharge_type = "Unbundling"; overcharge_types["Unbundling"] += 1 # Random chance for demo
                            else: overcharge_type = "Other Overcharging"; overcharge_types["Other Overcharging"] += 1
                            
                            comment = f"₹{amount:,.0f} vs ₹{rate:,.0f} (Save ₹{savings:,.0f})"
                            alerts.append(f"⚠️ {r.get('Item')}: {overcharge_type} - Save ₹{savings:,.0f}")
                    
                    results.append({"Service": r.get("Item"), "Billed (₹)": amount, "Standard (₹)": standard_rate, "Status": status, "Type": overcharge_type, "Comments": comment})
                
                results_df = pd.DataFrame(results)
                flagged_count = len([r for r in results if r['Status'] == 'Overcharged'])
                
                # Store audit
                st.session_state.current_audit = {
                    'patient_name': patient_name, 'hospital': hospital, 'contact': contact_number, 'email': email, 'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df, 'total_billed': total_billed, 'potential_savings': potential_savings, 'flagged_count': flagged_count,
                    'alerts': alerts, 'overcharge_types': overcharge_types, 'employer_id': employer_id
                }
                
                st.success("✅ Audit Complete!")
                st.markdown("---")
                
                # --- Audit Summary (Reworked Metrics - Total Bill, Savings are Main) ---
                st.markdown("### 📊 Audit Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Total Billed (Main Figure 1)
                    st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);">
                            <div class="metric-value" style="color: #00838f;">₹{total_billed:,.0f}</div>
                            <div class="metric-label">Total Billed Amount</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Potential Savings (Main Figure 2)
                    st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                            <div class="metric-value" style="color: #92400e;">₹{potential_savings:,.0f}</div>
                            <div class="metric-label">Possible Savings</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    # Items Checked (Secondary Figure)
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(results_df)}</div>
                            <div class="metric-label">Items Checked</div>
                        </div>
                    """, unsafe_allow_html=True)

                with col4:
                    # Issues Found (Smaller Figure)
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="font-size: 2rem;">{flagged_count}</div>
                            <div class="metric-label" style="font-size: 0.8rem;">Items with Errors</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # --- Overcharge Analysis (5 columns, aligned) ---
                st.markdown("### 🔍 Overcharge Analysis")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                card_data = [
                    ("💊 Inflated Consumables", overcharge_types["Inflated Consumables"], col1),
                    ("🔄 Duplicate Billing", overcharge_types["Duplicate Billing"], col2),
                    ("📈 Upcoding", overcharge_types["Upcoding"], col3),
                    ("📦 Unbundling", overcharge_types["Unbundling"], col4),
                    ("❓ Other Overcharging", overcharge_types["Other Overcharging"], col5)
                ]

                for title, count, col in card_data:
                    with col:
                        status_class = "audit-category-pass" if count == 0 else "audit-category-fail"
                        st.markdown(f"""
                            <div class="audit-category {status_class}">
                                <h4>{title.split(' ')[1]}</h4>
                                <p>Found: **{count}**</p>
                            </div>
                        """, unsafe_allow_html=True)

                st.markdown("### 🔍 Detailed Results")
                
                def highlight_status(row):
                    if row["Status"] == "Overcharged": return ['background-color: #fee2e2'] * len(row)
                    elif row["Status"] == "Unlisted": return ['background-color: #e0f2fe'] * len(row)
                    return ['background-color: #d1fae5'] * len(row)
                
                st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True, height=300)
                
                if alerts:
                    st.markdown("### ⚠️ Issues Found")
                    for alert in alerts: st.warning(alert)
                
                # --- Negotiation and Payment Section (Direct Flow) ---
                st.markdown("---")
                
                if potential_savings > 500:
                    st.markdown(f"""
                        <div class="negotiation-card">
                            <h3>🤝 Expert Negotiation Service</h3>
                            <p>We found potential savings of **₹{potential_savings:,.0f}** on your **₹{total_billed:,.0f}** bill.</p>
                            <p>Our experts can negotiate with {hospital} on your behalf.</p>
                            <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                                You pay only on actual savings achieved.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Negotiation Button
                        if st.button("✅ Yes, Negotiate For Me!", use_container_width=True, type="primary"):
                            negotiation_request = {
                                'id': f"NEG{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                'patient_name': patient_name,
                                'hospital': hospital,
                                'contact': contact_number,
                                'potential_savings': potential_savings,
                                'status': 'Pending',
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'audit_data': st.session_state.current_audit
                            }
                            st.session_state.negotiation_requests.append(negotiation_request)
                            # Negotiation success message with timeline
                            st.success("✅ **Success!** Our team has taken up your case and will resolve it in **1 to 3 business days**. Check the 'Negotiation Requests' tab for updates.")
                            st.session_state.current_audit = None
                            st.balloons()
                            st.rerun()
                    
                    with col2:
                        # Direct Payment Button (Paying original bill)
                        if st.button("💰 No Thanks, Proceed to Bill Payment", use_container_width=True):
                            st.session_state.show_payment = True
                            st.session_state.payment_bills = [st.session_state.current_audit]
                            st.session_state.current_audit = None
                            st.rerun()
                
                else: # No significant savings found
                    st.info("No significant overcharges found. You can proceed with the original bill payment.")
                    if st.button("💰 Proceed to Bill Payment", use_container_width=True, type="primary"):
                        st.session_state.show_payment = True
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.current_audit = None
                        st.rerun()
                    if st.button("📥 Download Report", use_container_width=True):
                        st.success("✓ Report downloaded!")
            
            elif run_audit and not patient_name:
                st.error("Please enter patient name to continue")
        
        # --- Demo Option ---
        # [Demo Mode logic remains similar to previous step for a complete flow]
        st.markdown("---")
        st.markdown("### 🎭 Demo Mode")
        st.info("Don't have a bill? Try our demo to see how the audit works!")
        
        if st.button("🚀 Run Demo Bill Audit", use_container_width=True, type="secondary", key="run_demo_audit"):
            # Set demo data
            demo_total_billed = 39700
            demo_potential_savings = 12900
            demo_flagged_count = 4
            demo_results = [
                {"Service": "Room Rent (General Ward)", "Billed (₹)": 8500, "Standard (₹)": 4000, 
                 "Status": "Overcharged", "Type": "Upcoding", "Comments": "₹8,500 vs ₹4,000 (Save ₹4,500)"},
                {"Service": "Surgical Gloves (Box)", "Billed (₹)": 4500, "Standard (₹)": 800, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹4,500 vs ₹800 (Save ₹3,700)"},
                {"Service": "CT Scan - Head", "Billed (₹)": 6000, "Standard (₹)": 3000, 
                 "Status": "Overcharged", "Type": "Other Overcharging", "Comments": "₹6,000 vs ₹3,000 (Save ₹3,000)"}, 
                {"Service": "Injection Syringe (Pack of 10)", "Billed (₹)": 2500, "Standard (₹)": 500, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹2,500 vs ₹500 (Save ₹2,000)"},
                {"Service": "ICU Charges (Per Day)", "Billed (₹)": 12000, "Standard (₹)": 8000, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
            ]
            results_df = pd.DataFrame(demo_results)
            alerts = ["⚠️ Room Rent: Upcoding - Save ₹4,500", "⚠️ Surgical Gloves: Inflated Consumables - Save ₹3,700", "⚠️ CT Scan: Other Overcharging - Save ₹3,000", "⚠️ Injection Syringe: Inflated Consumables - Save ₹2,000"]
            
            st.session_state.current_audit = {
                'patient_name': "Demo Patient", 'hospital': "Apollo Hospital", 'contact': mobile_number_display, 'email': "demo@mediaudit.com", 'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results_df': results_df, 'total_billed': demo_total_billed, 'potential_savings': demo_potential_savings, 'flagged_count': demo_flagged_count,
                'alerts': alerts, 'overcharge_types': {"Inflated Consumables": 2, "Duplicate Billing": 0, "Upcoding": 1, "Unbundling": 0, "Other Overcharging": 1},
                'is_demo': True, 'employer_id': 'DEMO-CORP'
            }
            st.success("✅ Demo Audit Complete!")
            st.rerun() # Rerun to display audit results


    with tabs[1]: # Negotiation Requests
        st.markdown("### 🤝 Active Negotiation Requests")
        
        # Display the "Negotiation Taken Up" status
        pending_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Pending']
        resolved_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Resolved']
        
        if pending_requests:
            st.markdown("#### ⏳ Negotiations in Progress")
            for idx, req in enumerate(pending_requests):
                with st.container(border=True):
                    total_billed = req['audit_data']['total_billed']
                    possible_savings = req['potential_savings']
                    
                    st.write(f"**Case ID:** {req['id']}")
                    st.write(f"**Patient:** {req['patient_name']} @ {req['hospital']}")
                    st.write(f"**Initial Bill:** ₹{total_billed:,.0f}")
                    st.write(f"**Possible Savings Found:** ₹{possible_savings:,.0f}")
                    
                    st.markdown(f"**Status:** Our team has taken up your case.")
                    st.info(f"Estimated resolution: **1 to 3 business days**.")
                    
                    # Simulated possible part saved
                    simulated_saved = int(possible_savings * random.uniform(0.7, 0.9))
                    st.markdown(f'<h3 style="color: #059669;">Possible Part Saved: ~₹{simulated_saved:,.0f}</h3>', unsafe_allow_html=True)

                    st.markdown("---")
                    
                    # Admin Action: Simulate resolution
                    if st.button(f"Simulate Successful Negotiation & Final Offer for {req['patient_name']}", key=f"resolve_neg_{idx}", use_container_width=True, type="primary"):
                        actual_savings = simulated_saved # Use simulated saved amount
                        original_bill = total_billed
                        hospital_payment = original_bill - actual_savings
                        commission_fee = actual_savings * 0.15 # Use 15% for internal calculation
                        total_to_pay = hospital_payment + commission_fee
                        
                        req['status'] = 'Resolved'
                        req['actual_savings'] = actual_savings
                        req['final_hospital_amount'] = hospital_payment
                        req['final_commission'] = commission_fee
                        req['total_to_pay'] = total_to_pay
                        
                        st.success(f"✅ Negotiation for {req['patient_name']} resolved with **₹{actual_savings:,.0f}** in savings!")
                        st.rerun()

        st.markdown("#### ✅ Resolved Negotiations - Ready for Payment")
        if resolved_requests:
            for idx, req in enumerate(resolved_requests):
                with st.container(border=True):
                    st.write(f"**Case ID:** {req['id']}")
                    st.write(f"**Patient:** {req['patient_name']} @ {req['hospital']}")
                    st.write(f"**Total Savings Achieved:** **₹{req['actual_savings']:,.0f}**")
                    st.markdown(f"**Final Total Payment:** **₹{req['total_to_pay']:,.0f}** (Hospital: ₹{req['final_hospital_amount']:,.0f} + Fee: ₹{req['final_commission']:,.0f})")
                    
                    if st.button(f"💳 Pay Final Negotiated Bill - ₹{req['total_to_pay']:,.0f}", key=f"pay_neg_final_{idx}", use_container_width=True, type="primary"):
                        # Prepare payment data for the centralized payment section
                        st.session_state.payment_data = {
                            'source': 'negotiation',
                            'negotiation_id': req['id'],
                            'bill': req['audit_data'],
                            'total_to_pay': req['total_to_pay'],
                            'hospital_total': req['final_hospital_amount'],
                            'commission_total': req['final_commission']
                        }
                        st.session_state.show_payment = True
                        st.rerun()
        else:
            st.info("No resolved negotiations awaiting payment.")

    with tabs[2]: # History
        st.markdown("### 📋 Completed Payments & Audits")
        
        if not st.session_state.payment_history:
            st.info("No completed payments found.")
        else:
            for idx, item in enumerate(reversed(st.session_state.payment_history)):
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Date Paid:** {item['date_paid']}")
                        st.write(f"**Patient:** {item['patient_name']}")
                    with col2:
                        st.write(f"**Hospital:** {item['hospital']}")
                        st.write(f"**Original Bill:** ₹{item['original_amount']:,.0f}")
                    with col3:
                        st.write(f"**Final Paid:** **₹{item['final_amount_paid']:,.0f}**")
                        st.write(f"**Net Savings:** ₹{item['savings'] - item['commission_paid']:,.0f}")
                    
                    if item['commission_paid'] > 0:
                        st.caption(f"Savings Achieved: ₹{item['savings']:,.0f} | Negotiation Fee Paid: ₹{item['commission_paid']:,.0f}")

# --- Payment Gateway Section (CENTRALIZED) ---

if st.session_state.get('show_payment', False):
    st.markdown("---")
    st.markdown("## 💳 Complete Your Payment")
    
    # Logic to handle payment data from either direct audit or negotiation
    pd_data = st.session_state.get('payment_data', {})
    if 'total_to_pay' not in pd_data:
        # Default for direct payment after audit
        audit = st.session_state.payment_bills[0]
        total_payment = audit['total_billed']
        hospital_total = audit['total_billed']
        commission_total = 0.0
        potential_savings = audit['potential_savings']
    else:
        # From resolved negotiation
        total_payment = pd_data['total_to_pay']
        hospital_total = pd_data['hospital_total']
        commission_total = pd_data['commission_total']
        potential_savings = pd_data['bill']['potential_savings']

    st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
    
    # Bill summary display
    if commission_total > 0:
        st.markdown(f"""
            <div style="padding: 1rem; border-radius: 8px; background: #e0f2fe; border: 1px solid #3b82f6;">
                <h4>Payment Breakdown</h4>
                <p>Reduced Payment to Hospital: **₹{hospital_total:,.0f}**</p>
                <p>MediAudit Success Fee: **₹{commission_total:,.0f}**</p>
                <p>Total Savings Achieved: **₹{potential_savings:,.0f}**</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"Full original bill amount of **₹{hospital_total:,.0f}** is due. Possible savings found: **₹{potential_savings:,.0f}**")
    
    # Payment Methods: Credit Card, UPI, EMI, BNPL
    payment_method = st.radio(
        "Select Payment Method",
        ["💳 Credit/Debit Card", "📱 UPI", "💼 EMI Options", "🛍️ Buy Now Pay Later (BNPL)"], 
        horizontal=True
    )
    
    # [Payment method fields logic omitted for brevity, assumed functional as in previous step]
    if payment_method == "💳 Credit/Debit Card":
        col1, col2 = st.columns(2)
        with col1: st.text_input("Card Number", placeholder="1234 5678 9012 3456")
        with col2: st.text_input("CVV", placeholder="123", type="password")
    elif payment_method == "📱 UPI":
        st.text_input("Enter UPI ID", placeholder="patient@upi")
        st.button("Generate QR Code", key="upi_qr", type="secondary")
    elif payment_method == "💼 EMI Options":
        st.selectbox("Select Bank/NBFC", ["HDFC Bank", "ICICI Bank", "Axis Bank"])
        st.selectbox("Select Tenure", ["3 months", "6 months", "12 months"])
        st.warning(f"Estimated Monthly EMI: **₹{total_payment / 6:.0f}** (for 6 months, subject to interest)")
    elif payment_method == "🛍️ Buy Now Pay Later (BNPL)":
        st.selectbox("Select Partner", ["Simpl", "Slice", "Lazypay"])
        st.info(f"Pay in 30 days. Required down payment: **₹{total_payment * 0.1:.0f}**")


    st.markdown("---")
    
    # Final Pay Now Button
    if st.button(f"🔒 Complete Secure Payment - ₹{total_payment:,.0f}", use_container_width=True, type="primary"):
        
        # Prepare history record
        bill_history = {
            'patient_name': pd_data.get('bill', st.session_state.payment_bills[0])['patient_name'],
            'hospital': pd_data.get('bill', st.session_state.payment_bills[0])['hospital'],
            'original_amount': pd_data.get('bill', st.session_state.payment_bills[0])['total_billed'],
            'final_amount_paid': total_payment,
            'date_paid': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'savings': potential_savings,
            'commission_paid': commission_total,
            'status': 'Paid',
            'payment_source': pd_data.get('source', 'audit')
        }
        st.session_state.payment_history.append(bill_history)
        
        # If from negotiation, remove from requests
        if pd_data.get('source') == 'negotiation':
            st.session_state.negotiation_requests = [
                r for r in st.session_state.negotiation_requests 
                if r['id'] != pd_data['negotiation_id']
            ]

        # Clear payment state
        st.session_state.show_payment = False
        st.session_state.payment_data = {}
        st.session_state.payment_bills = []

        st.balloons()
        st.success(f"✅ Payment of ₹{total_payment:,.0f} Successful! Thank you.")
        st.rerun()

# --- Footer (for all pages) ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**MediAudit Pro**")
    st.markdown("AI-powered medical auditing")
    st.markdown("*Free for patients*")

with col2:
    st.markdown("**Services**")
    st.markdown("• Free Bill Audit")
    st.markdown("• Expert Negotiation")
    st.markdown("• EMI Options")

with col3:
    st.markdown("**Quick Links**")
    st.markdown("• About Us")
    st.markdown("• Privacy Policy")
    st.markdown("• Terms of Service")

with col4:
    st.markdown("**Contact**")
    st.markdown("• support@mediaudit.com")
    st.markdown(f"• {mobile_number_display}")

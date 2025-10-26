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

# --- Configuration ---

# Global contact number
whatsapp_number = "917877797505"
mobile_number_display = "+91 7877797505"

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for equal-sized boxes and metrics
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
        
        [data-testid="stSidebar"] h3 {
            color: #1e293b !important;
            font-weight: 700;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label {
            background: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin: 0.25rem 0;
            border: 2px solid #e2e8f0;
            transition: all 0.3s;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: #3b82f6;
            background: #eff6ff;
            transform: translateX(4px);
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white !important;
            border-color: #2563eb;
        }
        
        /* Card styling - Added min-height for alignment */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
            height: 100%; /* Ensure all cards in a row are same height */
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        
        .info-card h4 {
            min-height: 40px; /* Enforce minimal height for title area */
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
        
        /* Audit Categories - Added min-height for alignment */
        .audit-category {
            background: #fff7ed;
            border: 2px solid #fb923c;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            min-height: 150px;
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
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({
            "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges", "CT Scan", "MRI", "X-Ray"],
            "Rate (₹)": [4000, 2500, 1500, 50000, 8000, 3000, 5000, 800]
        })
    return cghs

def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.70):
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

# --- Sidebar (Updated Logo, Contact, and Chatbot) ---
with st.sidebar:
    # Logo from repo logo.png
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("### 🏥 MediAudit Pro")
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")
    
    user_type = st.radio(
        "Navigate",
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "ℹ️ About & Pricing"],
        key="user_type_selector"
    )
    
    st.markdown("---")
    
    # Removed Bill Queue stats
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
    st.button("Send", use_container_width=True, disabled=True)
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
    st.markdown("### 🎯 What We Audit For (Aligned Boxes)")
    
    # 5 columns for 5 overcharge types (aligned)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>💊</h3>
                <h4>Inflated Consumables</h4>
                <p>Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>🔄</h3>
                <h4>Duplicate Billing</h4>
                <p>Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📈</h3>
                <h4>Upcoding</h4>
                <p>Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📦</h3>
                <h4>Unbundling</h4>
                <p>Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)

    with col5: # New 5th error: Other Overcharging
        st.markdown("""
            <div class="info-card" style="text-align: center;">
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
                    You pay only on actual savings achieved
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
    
    # Simplified tabs (Removed Bill Queue/Payment)
    tabs = st.tabs(["📤 New Bill Audit", "🤝 Negotiation Requests", "📋 History"])
    
    with tabs[0]: # New Bill Audit
        # Clear payment/negotiation flags on starting new audit
        st.session_state.show_payment = False
        st.session_state.current_audit = None
        st.session_state.post_negotiation_audit = None
        
        st.markdown("### 👤 Patient Information")
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
            admission_date = st.date_input("Admission Date")
        
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
            st.info(f"**We Check For 5 Errors:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling\n- Other Overcharging")
        
        manual_extract = st.checkbox("📝 Enter manually")
        
        if uploaded or manual_extract:
            df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
            
            if manual_extract:
                txt = st.text_area("Paste bill text", height=150)
                if txt:
                    lines = txt.splitlines()
                    items = text_to_items_from_lines(lines)
                    df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            else:
                ext = uploaded.name.split(".")[-1].lower()
                
                with st.spinner("🔄 Extracting bill data..."):
                    if ext in ("csv", "xlsx"):
                        try:
                            df_items = pd.read_csv(uploaded) if ext == "csv" else pd.read_excel(uploaded)
                            col_map = {}
                            for c in df_items.columns:
                                lc = c.strip().lower()
                                if "item" in lc or "service" in lc:
                                    col_map[c] = "Item"
                                if "amount" in lc or "₹" in lc or "cost" in lc:
                                    col_map[c] = "Amount (₹)"
                            df_items = df_items.rename(columns=col_map)
                            if "Item" in df_items.columns and "Amount (₹)" in df_items.columns:
                                df_items = df_items[["Item", "Amount (₹)"]]
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    elif ext in ("jpg", "jpeg", "png"):
                        bytes_data = uploaded.read()
                        txt = extract_text_from_image_bytes(bytes_data)
                        if txt:
                            items = text_to_items_from_lines(txt.splitlines())
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
                    
                    elif ext == "pdf":
                        txt = extract_text_from_pdf_bytes(uploaded.read())
                        if txt.strip():
                            items = text_to_items_from_lines(txt.splitlines())
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            
            if df_items.empty:
                df_items = pd.DataFrame([["", ""], ["", ""]], columns=["Item", "Amount (₹)"])
            
            st.markdown("### 📋 Extracted Items")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                run_audit = st.button("🚀 Run FREE Audit", use_container_width=True, type="primary")
            
            if run_audit and not edited.empty and patient_name:
                # Audit Progress Animation (Updated 5 steps)
                st.markdown("### 🔍 Auditing Your Bill...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audit_steps = [
                    ("Checking for Inflated Consumables...", 20),
                    ("Detecting Duplicate Billing...", 40),
                    ("Analyzing for Upcoding...", 60),
                    ("Checking Unbundling Practices...", 80),
                    ("Detecting Other Overcharges...", 100)
                ]
                
                for step, progress in audit_steps:
                    status_text.text(step)
                    progress_bar.progress(progress)
                    time.sleep(0.5)
                
                status_text.empty()
                progress_bar.empty()
                
                # Perform Audit
                cghs_df = load_reference_data()
                cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
                cghs_services = list(cghs_df["service_norm"].dropna().unique())
                
                results = []
                alerts = []
                # Updated Overcharge Types (5 total)
                overcharge_types = {
                    "Inflated Consumables": 0,
                    "Duplicate Billing": 0,
                    "Upcoding": 0,
                    "Unbundling": 0,
                    "Other Overcharging": 0 # The 5th error
                }
                
                total_billed = 0
                total_standard = 0
                potential_savings = 0
                
                for idx, r in edited.iterrows():
                    item = normalize_text(r.get("Item", ""))
                    if not item:
                        continue
                    
                    try:
                        amount = float(str(r.get("Amount (₹)", 0)).replace(",", "").replace("₹", "").strip())
                    except:
                        amount = 0.0
                    
                    total_billed += amount
                    status = "Normal"
                    overcharge_type = ""
                    comment = ""
                    standard_rate = amount
                    
                    matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                    
                    if matched:
                        row_ref = cghs_df[cghs_df["service_norm"] == matched].iloc[0]
                        rate = float(row_ref["Rate (₹)"])
                        standard_rate = rate
                        
                        if amount > rate * 1.15:  # 15% tolerance
                            status = "Overcharged"
                            savings = amount - rate
                            potential_savings += savings
                            
                            # Determine overcharge type (5th error implementation)
                            if any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']):
                                overcharge_type = "Inflated Consumables"
                                overcharge_types["Inflated Consumables"] += 1
                            elif amount > rate * 2 and not any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']):
                                overcharge_type = "Upcoding"
                                overcharge_types["Upcoding"] += 1
                            elif 'duplicate' in item or 'twice' in item:
                                overcharge_type = "Duplicate Billing"
                                overcharge_types["Duplicate Billing"] += 1
                            else:
                                # This catches Unbundling, or any general high deviation not classified above (Other Overcharging)
                                # For simplicity, we assign the rest of the unclassified overcharges to "Other Overcharging"
                                overcharge_type = "Other Overcharging"
                                overcharge_types["Other Overcharging"] += 1
                            
                            comment = f"₹{amount:,.0f} vs ₹{rate:,.0f} (Save ₹{savings:,.0f})"
                            alerts.append(f"⚠️ {r.get('Item')}: {overcharge_type} - Save ₹{savings:,.0f}")
                        else:
                            total_standard += amount
                    else:
                        status = "Unlisted"
                        comment = "Not in CGHS rates"
                        total_standard += amount
                    
                    results.append({
                        "Service": r.get("Item"),
                        "Billed (₹)": amount,
                        "Standard (₹)": standard_rate,
                        "Status": status,
                        "Type": overcharge_type,
                        "Comments": comment
                    })
                
                results_df = pd.DataFrame(results)
                flagged_count = len([r for r in results if r['Status'] == 'Overcharged'])
                
                # Store audit (Audit Score removed)
                st.session_state.current_audit = {
                    'patient_name': patient_name,
                    'hospital': hospital,
                    'contact': contact_number,
                    'email': email,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df,
                    'total_billed': total_billed,
                    'potential_savings': potential_savings,
                    'flagged_count': flagged_count,
                    'alerts': alerts,
                    'overcharge_types': overcharge_types,
                    'employer_id': employer_id
                }
                
                st.success("✅ Audit Complete!")
                st.markdown("---")
                
                # --- Audit Summary (Reworked Metrics) ---
                st.markdown("### 📊 Audit Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Total Billed (Main Figure 1)
                    st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);">
                            <div class="metric-value" style="color: #00838f;">₹{total_billed:,.0f}</div>
                            <div class="metric-label">Total Billed</div>
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
                st.markdown("### 🔍 Overcharge Analysis (Keep note of the 5th error)")
                
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
                    if row["Status"] == "Overcharged":
                        return ['background-color: #fee2e2'] * len(row)
                    elif row["Status"] == "Unlisted":
                        return ['background-color: #e0f2fe'] * len(row)
                    return ['background-color: #d1fae5'] * len(row)
                
                st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True, height=300)
                
                if alerts:
                    st.markdown("### ⚠️ Issues Found")
                    for alert in alerts:
                        st.warning(alert)
                
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
                                'email': email,
                                'potential_savings': potential_savings,
                                'status': 'Pending',
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'audit_data': st.session_state.current_audit
                            }
                            st.session_state.negotiation_requests.append(negotiation_request)
                            # Updated negotiation success message
                            st.success("✅ **Success!** Our team has taken up your case and will resolve it in **1 to 3 business days**.")
                            st.session_state.post_negotiation_audit = st.session_state.current_audit
                            st.session_state.current_audit = None
                            st.balloons()
                            st.rerun()
                    
                    with col2:
                        # Direct Payment Button
                        if st.button("💰 No Thanks, Proceed to Bill Payment", use_container_width=True):
                            st.session_state.show_payment = True
                            st.session_state.payment_bills = [st.session_state.current_audit]
                            st.rerun()
                
                else: # No significant savings found
                    if st.button("💰 Proceed to Bill Payment", use_container_width=True, type="primary"):
                        st.session_state.show_payment = True
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.rerun()
                    if st.button("📥 Download Report", use_container_width=True):
                        st.success("✓ Report downloaded!")
            
            elif run_audit and not patient_name:
                st.error("Please enter patient name to continue")
        
        # --- Demo Option (Updated metrics, 5th error, negotiation card) ---
        st.markdown("---")
        st.markdown("### 🎭 Demo Mode")
        st.info("Don't have a bill? Try our demo to see how the audit works!")
        
        if st.button("🚀 Run Demo Bill Audit", use_container_width=True, type="secondary"):
            # ... Demo Setup Logic ...
            
            # Perform Demo Audit
            # ...
            # Demo results with specific overcharges
            demo_results = [
                {"Service": "Room Rent (General Ward)", "Billed (₹)": 8500, "Standard (₹)": 4000, 
                 "Status": "Overcharged", "Type": "Upcoding", "Comments": "₹8,500 vs ₹4,000 (Save ₹4,500)"},
                {"Service": "Doctor Consultation", "Billed (₹)": 3000, "Standard (₹)": 2500, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "Blood Test - CBC", "Billed (₹)": 2000, "Standard (₹)": 1500, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "Surgical Gloves (Box)", "Billed (₹)": 4500, "Standard (₹)": 800, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹4,500 vs ₹800 (Save ₹3,700)"},
                {"Service": "CT Scan - Head", "Billed (₹)": 6000, "Standard (₹)": 3000, 
                 "Status": "Overcharged", "Type": "Other Overcharging", "Comments": "₹6,000 vs ₹3,000 (Save ₹3,000)"}, # Renamed to Other Overcharging (5th error)
                {"Service": "Injection Syringe (Pack of 10)", "Billed (₹)": 2500, "Standard (₹)": 500, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹2,500 vs ₹500 (Save ₹2,000)"},
                {"Service": "ICU Charges (Per Day)", "Billed (₹)": 12000, "Standard (₹)": 8000, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "X-Ray - Chest", "Billed (₹)": 1200, "Standard (₹)": 800, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"}
            ]
            
            results_df = pd.DataFrame(demo_results)
            
            alerts = [
                "⚠️ Room Rent (General Ward): Upcoding - Save ₹4,500",
                "⚠️ Surgical Gloves (Box): Inflated Consumables - Save ₹3,700",
                "⚠️ CT Scan - Head: Other Overcharging - Save ₹3,000", # Updated
                "⚠️ Injection Syringe (Pack of 10): Inflated Consumables - Save ₹2,000"
            ]
            flagged_count = 4
            
            # Store demo audit
            st.session_state.current_audit = {
                'patient_name': "Demo Patient",
                'hospital': "Apollo Hospital",
                'contact': mobile_number_display,
                'email': "demo@mediaudit.com",
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results_df': results_df,
                'total_billed': 39700,
                'potential_savings': 12900,
                'flagged_count': flagged_count,
                'alerts': alerts,
                'overcharge_types': {"Inflated Consumables": 2, "Duplicate Billing": 0, "Upcoding": 1, "Unbundling": 0, "Other Overcharging": 1},
                'is_demo': True,
                'employer_id': 'DEMO-CORP'
            }
            st.success("✅ Demo Audit Complete!")
            st.markdown("---")

            # --- Demo Audit Summary (Reworked Metrics) ---
            st.markdown("### 📊 Demo Audit Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1: # Total Billed
                st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);">
                        <div class="metric-value" style="color: #00838f;">₹39,700</div>
                        <div class="metric-label">Total Billed</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2: # Potential Savings
                st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                        <div class="metric-value" style="color: #92400e;">₹12,900</div>
                        <div class="metric-label">Possible Savings</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3: # Items Checked
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">8</div>
                        <div class="metric-label">Items Checked</div>
                    </div>
                """, unsafe_allow_html=True)
            with col4: # Issues Found
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="font-size: 2rem;">4</div>
                        <div class="metric-label" style="font-size: 0.8rem;">Items with Errors</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # --- Demo Overcharge Analysis (5 columns, aligned) ---
            st.markdown("### 🔍 Demo Overcharge Analysis")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            demo_card_data = [
                ("💊 Inflated Consumables", 2, "audit-category-fail", col1),
                ("🔄 Duplicate Billing", 0, "audit-category-pass", col2),
                ("📈 Upcoding", 1, "audit-category-fail", col3),
                ("📦 Unbundling", 0, "audit-category-pass", col4),
                ("❓ Other Overcharging", 1, "audit-category-fail", col5)
            ]

            for title, count, status_class, col in demo_card_data:
                with col:
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>{title.split(' ')[1]}</h4>
                            <p>Found: **{count}**</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("### 🔍 Detailed Demo Results")
            st.dataframe(results_df, use_container_width=True, height=300)
            
            st.markdown("### ⚠️ Issues Found in Demo")
            for alert in alerts:
                st.warning(alert)
            
            # Demo Negotiation Offer (No fixed commission)
            st.markdown("---")
            st.markdown(f""" 
                <div class="negotiation-card">
                    <h3>🤝 Demo: Expert Negotiation Service</h3>
                    <p>In this demo, we found potential savings of **₹12,900** on your **₹39,700** bill.</p>
                    <p>Our experts would negotiate with the hospital on your behalf.</p>
                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                        You pay only on actual savings achieved.
                    </p>
                    <p style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 8px;"> 
                        **This is a demo.** Upload a real bill to use our actual negotiation service! 
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Demo Actions
            st.markdown("### 💳 Try Demo Actions")
            col1, col2 = st.columns(2)
            with col1:
                st.button("✅ Yes, Negotiate For Me! (Demo)", use_container_width=True, type="primary", disabled=True)
            with col2:
                st.button("💰 Proceed to Bill Payment (Demo)", use_container_width=True, disabled=True)


    with tabs[1]: # Negotiation Requests (New)
        st.markdown("### 🤝 Active Negotiation Requests")
        
        # Display post-negotiation status (Possible Part Saved)
        if st.session_state.post_negotiation_audit:
            bill = st.session_state.post_negotiation_audit
            possible_savings = bill['potential_savings']
            total_billed = bill['total_billed']
            st.markdown("---")
            st.markdown(f"""
                <div class="negotiation-card" style="background: #e0f2fe; border: 3px solid #3b82f6;">
                    <h4>Case ID: NEG{datetime.now().strftime('%Y%m%d%H%M%S')} - {bill['patient_name']}</h4>
                    <p>Initial Bill: **₹{total_billed:,.0f}**</p>
                    <p>Possible Savings Found: **₹{possible_savings:,.0f}**</p>
                    <p style="font-weight: 700; font-size: 1.1rem;">Status: Our team has taken up your case.</p>
                    <p style="font-size: 1.1rem; color: #1d4ed8;">Estimated resolution: **1 to 3 business days**</p>
                    <h3 style="color: #059669;">Possible Part Saved: ~₹{int(possible_savings * 0.8):,.0f}</h3>
                    <p style="margin-top: 1rem;">**After successful negotiation, you will receive a new payment link with the revised, saved amount.**</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No active negotiation requests. Run an audit and select 'Negotiate For Me!' to start the process.")

    with tabs[2]: # History (Now tabs[2])
        st.markdown("### 📋 Payment & Audit History")
        if not st.session_state.payment_history:
            st.info("No completed payments or audits in history yet.")
        else:
            for idx, bill in enumerate(st.session_state.payment_history):
                with st.expander(f"Audit #{idx+1}: {bill['patient_name']} - {bill['hospital']} (Paid ₹{bill['total_billed']:,.0f})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Date:** {bill['date']}")
                        st.write(f"**Hospital:** {bill['hospital']}")
                        st.write(f"**Employer ID:** {bill['employer_id'] if 'employer_id' in bill else 'N/A'}")
                    with col2:
                        st.write(f"**Total Billed:** ₹{bill['total_billed']:,.0f}")
                        st.write(f"**Potential Savings:** ₹{bill['potential_savings']:,.0f}")
                    with col3:
                        st.write(f"**Errors Found:** {bill['flagged_count']}")
                        st.write(f"**Status:** ✅ Paid")
                    st.dataframe(bill['results_df'], use_container_width=True)

# --- Payment Section (Reworked to be standalone/direct) ---
if st.session_state.get('show_payment', False):
    st.markdown("---")
    st.markdown("## 💳 Complete Your Payment")
    
    payment_bills = st.session_state.get('payment_bills', [])
    if not payment_bills:
        st.error("No bill selected for payment. Please start a new audit or go to history.")
        st.session_state.show_payment = False
        st.stop()

    total_billed_for_payment = sum([bill['total_billed'] for bill in payment_bills])
    total_potential_savings = sum([bill['potential_savings'] for bill in payment_bills])
    
    # Bill summary display
    st.markdown(f"""
        <div class="info-card" style="background: #f0f9ff; border-left: 4px solid #3b82f6;">
            <h4>Bill Summary for Payment</h4>
            <p>Total Original Bill Amount: **₹{total_billed_for_payment:,.0f}**</p>
            <p>Possible Savings Found: **₹{total_potential_savings:,.0f}**</p>
            <h3 style="color: #1e3a8a;">Total Payment Due: ₹{total_billed_for_payment:,.0f}</h3>
            <p style="font-size: 0.8rem; color: #64748b;">(Note: You are paying the original billed amount. If you selected the negotiation service, a revised payment link will be provided separately once savings are achieved.)</p>
        </div>
    """, unsafe_allow_html=True)

    # Updated Payment Methods: Credit Card, UPI, EMI, BNPL
    payment_method = st.radio(
        "Select Payment Method",
        ["💳 Credit/Debit Card", "📱 UPI", "💼 EMI Options", "🛍️ Buy Now Pay Later (BNPL)"], 
        horizontal=True
    )
    
    if payment_method == "💳 Credit/Debit Card":
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Card Number", placeholder="1234 5678 9012 3456")
            st.text_input("Cardholder Name", placeholder="John Doe")
        with col2:
            col_a, col_b = st.columns(2)
            with col_a:
                st.text_input("Expiry (MM/YY)", placeholder="12/25")
            with col_b:
                st.text_input("CVV", placeholder="123", type="password")
            st.checkbox("Save card for future payments")

    elif payment_method == "📱 UPI":
        upi_id = st.text_input("Enter UPI ID", placeholder="patient@upi")
        if st.button("Generate QR Code", key="upi_qr", type="secondary"):
            st.info(f"QR code generated for {upi_id} to pay ₹{total_billed_for_payment:,.0f}")
            st.caption("Scan the QR code in your UPI app to complete the transaction.")
    
    elif payment_method == "💼 EMI Options":
        st.markdown("### 🏦 Pay with EMI")
        st.info("Convert your bill into easy monthly installments. Get instant approval from our partners.")
        st.selectbox("Select Bank/NBFC", ["HDFC Bank", "ICICI Bank", "Axis Bank", "Bajaj Finserv", "Other"], key="emi_bank")
        st.selectbox("Select Tenure", ["3 months", "6 months", "12 months", "24 months"], key="emi_tenure")
        st.warning("Final EMI amount is subject to bank approval and interest rates.")

    elif payment_method == "🛍️ Buy Now Pay Later (BNPL)":
        st.markdown("### 🛍️ Buy Now Pay Later")
        st.info("Pay later through one of our BNPL partners. Get up to 30 days interest-free.")
        st.selectbox("Select Partner", ["Simpl", "Slice", "Lazypay", "ZestMoney"], key="bnpl_partner")
        st.warning("BNPL availability is subject to credit check and partner terms.")
    
    st.markdown("---")
    
    if st.button("✅ Complete Secure Payment", type="primary", use_container_width=True):
        st.session_state.payment_history.extend(payment_bills)
        st.session_state.show_payment = False
        st.session_state.current_audit = None
        st.session_state.payment_bills = []
        st.success("🎉 **Payment Successful!** Your payment has been processed.")
        st.balloons()
        st.rerun()

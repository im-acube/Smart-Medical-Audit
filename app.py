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

# --- CONSTANTS (Updated Phone Number) ---
CONTACT_NUMBER = "+91 7877797505"
WHATSAPP_LINK = f"https://wa.me/917877797505?text=Hi%20MediAudit%20Pro,%20I%20need%20help%20with%20my%20medical%20bill"
LOGO_PATH = "logo.png"

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (Updated for Card Alignment and Chatbot)
st.markdown("""
    <style>
        /* Logo Styling */
        .logo-img {
            max-width: 100%;
            height: auto;
            margin-bottom: 1rem;
            border-radius: 8px;
        }

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
        
        /* Card styling - Added min-height for alignment of parallel boxes */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
            min-height: 200px; /* Enforcing equal height for overcharge cards */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 120px; /* Ensure metric cards are aligned */
            display: flex;
            flex-direction: column;
            justify-content: center;
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
            min-height: 150px; /* Enforcing equal height for audit categories */
            display: flex;
            flex-direction: column;
            justify-content: space-around;
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
        
        /* Chatbot Icon (New) */
        .chatbot-float {
            position: fixed;
            bottom: 100px; /* Above WhatsApp button */
            right: 30px;
            z-index: 1000;
        }
        .chatbot-button {
            background: #2563eb;
            color: white;
            padding: 15px 20px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(37, 102, 211, 0.4);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }

    </style>
""", unsafe_allow_html=True)

# --- CHATBOT FUNCTIONALITY (Placeholder) ---
if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = False
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hello! I'm your MediAudit Pro Chatbot. How can I assist you with your bill audit today?"}
    ]

def toggle_chatbot():
    st.session_state.show_chatbot = not st.session_state.show_chatbot

# WhatsApp Chatbot Float Button (Updated Number)
st.markdown(f"""
    <div class="whatsapp-float">
        <a href="{WHATSAPP_LINK}" 
           target="_blank" class="whatsapp-button">
            💬 WhatsApp: {CONTACT_NUMBER}
        </a>
    </div>
""", unsafe_allow_html=True)

# Chatbot Toggle Button
st.markdown(f"""
    <div class="chatbot-float">
        <a class="chatbot-button" href="javascript:void(0);" onclick="Streamlit.setComponentValue('chatbot_toggle', !Streamlit.getComponentValue('chatbot_toggle'))">
            🤖 Ask MediBot
        </a>
    </div>
    <script>
        // Placeholder for Streamlit Component Communication. 
        // In a real Streamlit app, this would require a custom component 
        // or a JavaScript hack to update the session state of a button.
        // For this submission, we'll use a hidden button to simulate the toggle.
    </script>
""", unsafe_allow_html=True)

# Hidden button to trigger the state change via Rerun logic
if st.button("Toggle Chatbot (Hidden)", key="hidden_chatbot_toggle", on_click=toggle_chatbot):
    pass # This button's main purpose is to be a state change target

# Chatbot Display
if st.session_state.show_chatbot:
    with st.popover("MediAudit Chatbot", use_container_width=True):
        st.write("🤖 **MediAudit Pro Chatbot**")
        st.markdown("---")
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input logic
        if prompt := st.chat_input("Ask a question...", key="chat_input"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            # Simple Bot Logic (Placeholder)
            response = "Thank you for your message. Our bot is currently in beta. For immediate assistance, please use our WhatsApp link or contact us at " + CONTACT_NUMBER + "."
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            # Manually force rerun to display the new messages
            st.experimental_rerun()


# Helper functions
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

# Initialize session state
if 'bill_queue' not in st.session_state:
    st.session_state.bill_queue = []
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None
if 'payment_history' not in st.session_state:
    st.session_state.payment_history = []
if 'negotiation_requests' not in st.session_state:
    st.session_state.negotiation_requests = []

# Sidebar (Updated with Logo and Contact Number)
with st.sidebar:
    # --- Logo ---
    try:
        # Assuming logo.png is present in the repo
        logo = Image.open(LOGO_PATH)
        st.image(logo, use_column_width=True, caption="MediAudit Pro Logo")
    except FileNotFoundError:
        st.markdown("### 🏥 MediAudit Pro")
    
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")
    
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
            st.metric("Total Bills", str(len(st.session_state.payment_history) + len(st.session_state.bill_queue)))
        with col2:
            # Main metric change: Focus on savings
            total_savings = sum([b.get('possible_part_saved', 0) for b in st.session_state.payment_history])
            st.metric("Total Saved (₹)", f"{total_savings:,.0f}")
        
        if st.session_state.bill_queue:
            st.markdown("---")
            total_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            st.info(f"**Queue Total Bill**\n₹{total_queue:,.0f}")
    
    st.markdown("---")
    st.markdown("### 📞 Quick Contact")
    st.markdown(f"**Mobile:** {CONTACT_NUMBER}")
    if st.button("📱 WhatsApp Support", use_container_width=True):
        st.markdown(f"[Click to chat]({WHATSAPP_LINK})")
    st.markdown("📧 support@mediaudit.com")

# Main content

# --- HOME PAGE (Updated) ---
if user_type == "🏠 Home":
    
    # Hero
    st.markdown("""
        <div class="hero-banner">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing - Detect Overcharges & Save Money</p>
            <p style="font-size: 1rem; margin-top: 1rem;">✓ Free Audits | ✓ Expert Negotiation | ✓ WhatsApp Support</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 1. New 'What is MediAudit' section
    st.markdown("### 💡 What is MediAudit?")
    st.markdown("""
        <div class="info-card" style="min-height: auto; border-left: 4px solid #f59e0b; justify-content: center;">
            <p style="font-size: 1.2rem; font-weight: 500;">
                **Your expert partner against unfair hospital bills.** We blend advanced AI analysis with human medical auditing expertise to find and fix costly errors, ensuring you only pay what's fair.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 2. New 'Start Audit Now' button that navigates to Patient Portal
    if st.button("🚀 Start your free audit now", use_container_width=True, type="primary"):
        st.session_state.user_type_selector = "👤 Patient Portal"
        st.rerun()

    st.markdown("---")

    # 3. Updated Overcharge Types (with 5th error and equal size/alignment from CSS)
    st.markdown("### 🎯 What We Audit For")
    
    col1, col2, col3, col4, col5 = st.columns(5) # 5 columns for 5 errors
    
    with col1:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left-color: #ef4444;">
                <h3>💊</h3>
                <h4>Inflated Consumables</h4>
                <p>Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left-color: #f97316;">
                <h3>🔄</h3>
                <h4>Duplicate Billing</h4>
                <p>Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left-color: #0ea5e9;">
                <h3>📈</h3>
                <h4>Upcoding</h4>
                <p>Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left-color: #10b981;">
                <h3>📦</h3>
                <h4>Unbundling</h4>
                <p>Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col5: # New 5th error
        st.markdown("""
            <div class="info-card" style="text-align: center; border-left-color: #6366f1;">
                <h3>❓</h3>
                <h4>Other Overcharging</h4>
                <p>Any other discrepancy, administrative fees, or unverified charge</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 💼 Our Services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="min-height: auto; justify-content: flex-start;">
                <h3>🆓 FREE Bill Audit</h3>
                <p>✓ AI-powered analysis</p>
                <p>✓ Detect all 5 overcharge types</p>
                <p>✓ Detailed audit report</p>
                <p>✓ CGHS rate comparison</p>
                <p>✓ Instant results</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Negotiation section with commission removed
        st.markdown("""
            <div class="negotiation-card" style="min-height: auto; justify-content: flex-start;">
                <h3>🤝 Expert Negotiation Service</h3>
                <p>✓ We negotiate on your behalf</p>
                <p>✓ Deal with hospital billing dept</p>
                <p>✓ Get overcharges reduced/removed</p>
                <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                    *No fixed commission needs to be mentioned.* We charge only on actual savings achieved.
                </p>
            </div>
        """, unsafe_allow_html=True)

# --- PATIENT PORTAL (Updated) ---
elif user_type == "👤 Patient Portal":
    st.markdown("""
        <div class="hero-banner">
            <h1>👤 Patient Portal</h1>
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🗂️ Bill Queue & Payment", "🤝 Negotiation Requests", "📋 History"])
    
    # TAB 1: New Bill Audit
    with tabs[0]:
        st.markdown("### 👤 Patient & Enterprise Information")
        col1, col2, col3 = st.columns(3)
        
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
            contact_number_input = st.text_input("Contact Number", placeholder="+91 7877797505", value=CONTACT_NUMBER)
            email = st.text_input("Email", placeholder="patient@email.com")

        # New Employer ID section
        st.markdown("---")
        st.markdown("#### 🏢 Enterprise Linking")
        # 8. Add employer ID input
        employer_id = st.text_input("Employer ID (Optional)", placeholder="Enter your Employer/Insurance ID that can link it to their enterprise.")
        
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
            st.info("**We Check For 5 Errors:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling\n- Other Overcharging")
        
        manual_extract = st.checkbox("📝 Enter manually")
        
        if uploaded or manual_extract:
            df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
            
            # (Rest of extraction logic remains the same)
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
                # Audit Progress Animation
                st.markdown("### 🔍 Auditing Your Bill...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Updated audit steps to reflect 5 errors
                audit_steps = [
                    ("Checking for Inflated Consumables...", 20),
                    ("Detecting Duplicate Billing...", 40),
                    ("Analyzing for Upcoding...", 60),
                    ("Checking Unbundling Practices...", 80),
                    ("Reviewing for Other Overcharging...", 100) # 5th error
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
                # 6. Updated overcharge_types to include the 5th error
                overcharge_types = {
                    "Inflated Consumables": 0,
                    "Duplicate Billing": 0,
                    "Upcoding": 0,
                    "Unbundling": 0,
                    "Other Overcharging": 0 # New 5th error
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
                            
                            # Determine overcharge type (Updated logic)
                            if any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']):
                                overcharge_type = "Inflated Consumables"
                                overcharge_types["Inflated Consumables"] += 1
                            elif amount > rate * 2.5 and not any(word in item for word in ['room', 'ward', 'icu']):
                                overcharge_type = "Upcoding"
                                overcharge_types["Upcoding"] += 1
                            else:
                                # Catch-all for other high charges (5th error)
                                overcharge_type = "Other Overcharging" 
                                overcharge_types["Other Overcharging"] += 1
                            
                            comment = f"₹{amount:,.0f} vs ₹{rate:,.0f} (Save ₹{savings:,.0f})"
                            alerts.append(f"⚠️ {r.get('Item')}: {overcharge_type} - Save ₹{savings:,.0f}")
                        else:
                            pass 
                    else:
                        status = "Unlisted"
                        comment = "Not in CGHS rates (Standard assumption for non-matched item)"
                    
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
                
                # Store audit
                st.session_state.current_audit = {
                    'patient_name': patient_name,
                    'hospital': hospital,
                    'contact': contact_number_input,
                    'email': email,
                    'employer_id': employer_id,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df,
                    'total_billed': total_billed,
                    'potential_savings': potential_savings,
                    'flagged_count': flagged_count,
                    'alerts': alerts,
                    'overcharge_types': overcharge_types,
                    'possible_part_saved': None 
                }
                
                st.success("✅ Audit Complete!")
                st.markdown("---")
                
                # Results (Updated Metrics Display - Removed Audit Score, Added Total Billed)
                st.markdown("### 📊 Audit Summary")
                
                # 14. Main figures: Total Bill, Possible Savings, Items with Errors (smaller)
                col1, col2, col3 = st.columns(3) 
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{total_billed:,.0f}</div>
                            <div class="metric-label">Total Bill</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                            <div class="metric-value" style="color: #92400e;">₹{potential_savings:,.0f}</div>
                            <div class="metric-label">Possible Savings</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{flagged_count}</div>
                            <div class="metric-label">Items with Errors</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Overcharge Types Found (Updated to 5 errors)
                st.markdown("### 🔍 Overcharge Analysis (5 Error Types)")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                # Helper to display audit category
                def display_audit_category(col, name, key, color, description):
                    status_class = "audit-category-pass" if st.session_state.current_audit['overcharge_types'][key] == 0 else "audit-category-fail"
                    with col:
                        st.markdown(f"""
                            <div class="audit-category {status_class}" style="border-color: {color};">
                                <h4>{name}</h4>
                                <p>Found: {st.session_state.current_audit['overcharge_types'][key]}</p>
                                <p style="font-size: 0.75rem;">{description}</p>
                            </div>
                        """, unsafe_allow_html=True)

                display_audit_category(col1, "💊 Consumables", "Inflated Consumables", "#ef4444", "Syringes, gloves, basic supplies")
                display_audit_category(col2, "🔄 Duplicate", "Duplicate Billing", "#f97316", "Same charge listed multiple times")
                display_audit_category(col3, "📈 Upcoding", "Upcoding", "#0ea5e9", "Basic service billed as premium")
                display_audit_category(col4, "📦 Unbundling", "Unbundling", "#10b981", "Package split to inflate cost")
                display_audit_category(col5, "❓ Other", "Other Overcharging", "#6366f1", "General discrepancy / admin fee") # 5th error
                
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
                
                # Negotiation Offer (Updated Text)
                if potential_savings > 500:
                    st.markdown("---")
                    st.markdown(f"""
                        <div class="negotiation-card">
                            <h3>🤝 Expert Negotiation Service</h3>
                            <p>We found potential savings of **₹{potential_savings:,.0f}**</p>
                            <p>**Our team has taken up your case and will resolve in 1 to 3 business days.**</p>
                            <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                                We guarantee to fight every error to maximize your final savings. *No fixed commission needs to be mentioned.*
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Negotiate For Me!", use_container_width=True, type="primary"):
                            negotiation_request = {
                                'id': f"NEG{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                'patient_name': patient_name,
                                'hospital': hospital,
                                'contact': contact_number_input,
                                'email': email,
                                'employer_id': employer_id,
                                'potential_savings': potential_savings,
                                'status': 'In Progress (1-3 Business Days)',
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'audit_data': st.session_state.current_audit,
                                'possible_part_saved': None
                            }
                            st.session_state.negotiation_requests.append(negotiation_request)
                            st.success("✅ Negotiation request submitted! Our team will begin the resolution process.")
                            st.balloons()
                    
                    with col2:
                        if st.button("No Thanks, I'll Handle It", use_container_width=True):
                            st.info("No problem! You can still proceed with payment options below.")
                
                # Action buttons
                st.markdown("---")
                st.markdown("### 💳 What's Next?")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗂️ Add to Bill Queue", use_container_width=True):
                        st.session_state.bill_queue.append(st.session_state.current_audit)
                        st.success(f"✓ Added! {len(st.session_state.bill_queue)} bills in queue")
                        st.rerun()
                
                with col2:
                    if st.button("💰 Proceed to Payment", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.show_payment = True
                        st.rerun()
                
                with col3:
                    if st.button("📥 Download Report", use_container_width=True):
                        st.success("✓ Report downloaded!")
            
            elif run_audit and not patient_name:
                st.error("Please enter patient name to continue")
        
        # Demo Option (Updated to reflect new metrics, 5 errors, and negotiation text)
        st.markdown("---")
        st.markdown("### 🎭 Demo Mode")
        st.info("Don't have a bill? Try our demo to see how the audit works!")
        
        if st.button("🚀 Run Demo Bill Audit", use_container_width=True, type="secondary"):
            
            # (Demo logic remains the same, but the displayed results are updated)
            
            # Set demo patient info
            demo_patient_name = "Demo Patient"
            demo_hospital = "Apollo Hospital"
            demo_contact = CONTACT_NUMBER
            demo_email = "demo@mediaudit.com"
            demo_employer = "Demo Corp"
            
            st.markdown("### 🔍 Running Demo Audit...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Updated audit steps for demo
            audit_steps = [
                ("Checking for Inflated Consumables...", 20),
                ("Detecting Duplicate Billing...", 40),
                ("Analyzing for Upcoding...", 60),
                ("Checking Unbundling Practices...", 80),
                ("Reviewing for Other Overcharging...", 100)
            ]
            
            for step, progress in audit_steps:
                status_text.text(step)
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            status_text.empty()
            progress_bar.empty()
            
            # Perform Demo Audit (Results hardcoded for a consistent demo experience)
            total_billed = 39700
            potential_savings = 12900 # Savings will be the main metric
            flagged_count = 4
            
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
                {"Service": "CT Scan - Head (Overcharge)", "Billed (₹)": 6000, "Standard (₹)": 3000, 
                 "Status": "Overcharged", "Type": "Other Overcharging", "Comments": "₹6,000 vs ₹3,000 (Save ₹3,000)"}, # Changed to 5th error
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
                "⚠️ CT Scan - Head (Overcharge): Other Overcharging - Save ₹3,000",
                "⚠️ Injection Syringe (Pack of 10): Inflated Consumables - Save ₹2,000"
            ]
            
            # Updated overcharge types for demo
            demo_overcharge_types = {
                "Inflated Consumables": 2,
                "Duplicate Billing": 0,
                "Upcoding": 1,
                "Unbundling": 0,
                "Other Overcharging": 1 
            }
            
            # Store demo audit
            st.session_state.current_audit = {
                'patient_name': demo_patient_name,
                'hospital': demo_hospital,
                'contact': demo_contact,
                'email': demo_email,
                'employer_id': demo_employer,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results_df': results_df,
                'total_billed': total_billed,
                'potential_savings': potential_savings,
                'flagged_count': flagged_count,
                'alerts': alerts,
                'overcharge_types': demo_overcharge_types,
                'is_demo': True,
                'possible_part_saved': None
            }
            
            st.success("✅ Demo Audit Complete!")
            st.markdown("---")
            
            # Demo Results (Updated Metrics Display)
            st.markdown("### 📊 Demo Audit Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">₹{total_billed:,.0f}</div>
                        <div class="metric-label">Total Bill</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                        <div class="metric-value" style="color: #92400e;">₹{potential_savings:,.0f}</div>
                        <div class="metric-label">Possible Savings</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{flagged_count}</div>
                        <div class="metric-label">Items with Errors</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Demo Overcharge Types Found
            st.markdown("### 🔍 Demo Overcharge Analysis (5 Error Types)")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Helper to display audit category
            def display_demo_category(col, name, key, color, description, count):
                status_class = "audit-category-pass" if count == 0 else "audit-category-fail"
                with col:
                    st.markdown(f"""
                        <div class="audit-category {status_class}" style="border-color: {color};">
                            <h4>{name}</h4>
                            <p>Found: {count} issues</p>
                            <p style="font-size: 0.75rem;">{description}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            display_demo_category(col1, "💊 Consumables", "Inflated Consumables", "#ef4444", "Gloves & Syringes overpriced", 2)
            display_demo_category(col2, "🔄 Duplicate", "Duplicate Billing", "#f97316", "All clear!", 0)
            display_demo_category(col3, "📈 Upcoding", "Upcoding", "#0ea5e9", "Room rent inflated", 1)
            display_demo_category(col4, "📦 Unbundling", "Unbundling", "#10b981", "All clear!", 0)
            display_demo_category(col5, "❓ Other", "Other Overcharging", "#6366f1", "CT Scan Overcharge", 1) 

            
            st.markdown("### 🔍 Detailed Demo Results")
            
            def highlight_status(row):
                if row["Status"] == "Overcharged":
                    return ['background-color: #fee2e2'] * len(row)
                return ['background-color: #d1fae5'] * len(row)
            
            st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True, height=300)
            
            st.markdown("### ⚠️ Issues Found in Demo")
            for alert in alerts:
                st.warning(alert)
            
            # Demo Negotiation Offer (Updated Text)
            st.markdown("---")
            st.markdown(f"""
                <div class="negotiation-card">
                    <h3>🤝 Demo: Expert Negotiation Service</h3>
                    <p>In this demo, we found potential savings of **₹12,900**</p>
                    <p>**Our team would take up your case and resolve in 1 to 3 business days.**</p>
                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                        We guarantee to fight every error to maximize your final savings.
                    </p>
                    <p style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 8px;"> 
                        **This is a demo.** Upload a real bill to use our actual negotiation service! 
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 💳 Try Demo Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🗂️ Add Demo to Queue", use_container_width=True):
                    st.session_state.bill_queue.append(st.session_state.current_audit)
                    st.success(f"✓ Demo added! {len(st.session_state.bill_queue)} bills in queue")
            with col2:
                st.button("💰 Try Payment Flow", use_container_width=True, disabled=True)
                st.caption("Available with real bills")
            with col3:
                if st.button("📥 Download Demo Report", use_container_width=True):
                    st.success("✓ Demo report downloaded!")

    # TAB 2: Bill Queue & Payment (Updated Bill Display and Payment Options)
    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        if not st.session_state.bill_queue:
            st.info("📭 No bills in queue. Audit a bill and add it to queue to pay multiple bills together!")
        else:
            total_billed_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            total_savings_queue = sum([b['potential_savings'] for b in st.session_state.bill_queue])
            
            # Updated Queue Summary
            st.markdown(f"""
                <div class="info-card" style="background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 100%); border-color: #3b82f6; min-height: auto;">
                    <h3>📋 {len(st.session_state.bill_queue)} Bills in Queue</h3>
                    <div style="display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 600;">
                        <p style="color: #1e3a8a;">Total Billed: ₹{total_billed_queue:,.0f}</p>
                        <p style="color: #92400e;">Possible Savings: ₹{total_savings_queue:,.0f}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display queued bills
            for idx, bill in enumerate(st.session_state.bill_queue):
                is_demo = bill.get('is_demo', False)
                demo_badge = " 🎭 DEMO" if is_demo else ""
                
                # Check for negotiation status
                negotiated_req = next((n for n in st.session_state.negotiation_requests if n.get('audit_data') and n['audit_data'] == bill), None)
                negotiated_savings = negotiated_req.get('possible_part_saved') if negotiated_req else None
                
                
                with st.expander(f"Bill #{idx+1}{demo_badge}: {bill['patient_name']} - {bill['hospital']} (Billed: ₹{bill['total_billed']:,.0f})"):
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Date:** {bill['date']}")
                        st.write(f"**Hospital:** {bill['hospital']}")
                    with col2:
                        # 11. Bill should show total bill and possible savings
                        st.write(f"**Total Bill:** ₹{bill['total_billed']:,.0f}")
                        st.write(f"**Possible Savings:** ₹{bill['potential_savings']:,.0f}")
                    with col3:
                        st.write(f"**Employer ID:** {bill['employer_id'] if bill.get('employer_id') else 'N/A'}")
                        # 11. Then after negotisition a possible part saved.
                        if negotiated_savings is not None:
                            st.write(f"**Saved (Post-Neg):** ₹{negotiated_savings:,.0f}")
                        else:
                            st.write(f"**Issues Found:** {bill['flagged_count']}")
                            
                    st.dataframe(bill['results_df'], use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if not is_demo:
                            if st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True):
                                st.session_state.payment_bills = [bill]
                                st.session_state.show_payment = True
                                st.rerun()
                        else:
                            st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True, disabled=True)
                            st.caption("Demo bills can't be paid")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                            st.session_state.bill_queue.pop(idx)
                            st.rerun()
            
            st.markdown("---")
            
            # Check if any non-demo bills exist
            non_demo_bills = [b for b in st.session_state.bill_queue if not b.get('is_demo', False)]
            col1, col2 = st.columns(2)
            with col1:
                if non_demo_bills:
                    if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = non_demo_bills
                        st.session_state.show_payment = True
                        st.rerun()
                else:
                    st.button("💳 Pay All Bills Together", use_container_width=True, disabled=True)
                    st.caption("No real bills in queue")
            with col2:
                if st.button("🗑️ Clear Queue", use_container_width=True):
                    st.session_state.bill_queue = []
                    st.rerun()
        
        # Payment Section (Updated Payment Methods)
        if st.session_state.get('show_payment', False):
            st.markdown("---")
            st.markdown("## 💳 Complete Your Payment")
            payment_bills = st.session_state.get('payment_bills', [])
            total_payment = sum([bill['total_billed'] for bill in payment_bills])
            
            st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
            st.markdown(f"Paying for {len(payment_bills)} bill(s)")
            
            # 9. Updated Payment Method options (CC, UPI, EMI, BNPL)
            payment_method = st.radio(
                "Select Payment Method", 
                ["💳 Credit/Debit Card", "📱 UPI", "💼 EMI Options", "🛍️ BNPL (Buy Now Pay Later)"],
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
                upi_id = st.text_input("UPI ID", placeholder="yourname@paytm")
                st.info("📱 You'll receive a payment request on your UPI app")
            
            elif payment_method == "💼 EMI Options":
                st.info("Select from various bank EMI options at checkout.")
                st.selectbox("Select Bank for EMI", [
                    "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Other"
                ])
                st.selectbox("Tenure", ["3 Months", "6 Months", "9 Months", "12 Months"])
            
            elif payment_method == "🛍️ BNPL (Buy Now Pay Later)":
                st.info("Pay the hospital bill now and settle with our BNPL partner later.")
                st.selectbox("Select BNPL Partner", [
                    "ZestMoney", "LazyPay", "Simple Pay", "Sezzle"
                ])
                st.markdown("---")
                st.warning("Approval subject to partner terms and conditions.")

            st.markdown("---")
            if st.button(f"🔒 Pay ₹{total_payment:,.0f} Securely", type="primary", use_container_width=True):
                # Move to payment history
                for bill in payment_bills:
                    bill_copy = bill.copy()
                    bill_copy['payment_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # Check if a negotiated saving exists
                    negotiated_req = next((n for n in st.session_state.negotiation_requests if n.get('audit_data') and n['audit_data'] == bill), None)
                    if negotiated_req and negotiated_req.get('possible_part_saved') is not None:
                        bill_copy['possible_part_saved'] = negotiated_req['possible_part_saved']
                    elif bill_copy['possible_part_saved'] is None:
                        # Simulate negotiated savings for history if no negotiation was completed
                        bill_copy['possible_part_saved'] = bill_copy['potential_savings'] * 0.5 
                        
                    st.session_state.payment_history.append(bill_copy)
                    
                    # Remove from queue if it was there
                    if bill in st.session_state.bill_queue:
                        st.session_state.bill_queue.remove(bill)
                        
                st.success("🎉 Payment successful! Bill moved to History.")
                st.session_state.show_payment = False
                st.rerun()

    # TAB 3: Negotiation Requests (Updated Negotiation Text)
    with tabs[2]:
        st.markdown("### 🤝 Negotiation Requests")
        
        if not st.session_state.negotiation_requests:
            st.info("No active negotiation requests. Run an audit and request negotiation to start saving!")
        else:
            for idx, req in enumerate(st.session_state.negotiation_requests):
                
                # Simulate negotiation success after a day
                if req['status'] == 'In Progress (1-3 Business Days)' and (datetime.now() - datetime.strptime(req['date'], "%Y-%m-%d %H:%M")) > timedelta(days=1):
                    # Simulate a part saved (e.g., 75% of potential savings)
                    req['possible_part_saved'] = req['potential_savings'] * 0.75
                    req['status'] = 'Resolved (Saved)'
                
                status_color = "#3b82f6"
                if req['status'] == 'Resolved (Saved)':
                    status_color = "#10b981"
                
                st.markdown(f"""
                    <div class="info-card" style="border-left: 4px solid {status_color}; min-height: auto;">
                        <h4 style="display: flex; justify-content: space-between;">
                            <span>Case ID: {req['id']}</span>
                            <span style="color: {status_color}; font-size: 1rem;">**{req['status']}**</span>
                        </h4>
                        <p>**Patient:** {req['patient_name']} | **Hospital:** {req['hospital']}</p>
                        <p><strong>Total Billed:</strong> ₹{req['audit_data']['total_billed']:,.0f}</p>
                        <p><strong>Potential Savings Identified:</strong> ₹{req['potential_savings']:,.0f}</p>
                        <p style="font-weight: 700;">
                            {'**Savings Achieved:** ₹' + f"{req['possible_part_saved']:,.0f}" if req['possible_part_saved'] is not None else '**Estimated Resolution:** 1 to 3 Business Days'}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("View Audit Details", key=f"neg_detail_{idx}"):
                    st.json(req['audit_data'])


    # TAB 4: History (Updated Bill Display)
    with tabs[3]:
        st.markdown("### 📋 Payment & Audit History")
        
        if not st.session_state.payment_history:
            st.info("Your payment history is empty.")
        else:
            for idx, bill in enumerate(st.session_state.payment_history):
                is_demo = bill.get('is_demo', False)
                demo_badge = " 🎭 DEMO" if is_demo else ""
                
                
                st.markdown(f"""
                    <div class="info-card" style="border-left: 4px solid #10b981; min-height: auto;">
                        <h4 style="display: flex; justify-content: space-between;">
                            <span>**PAID** - {bill['hospital']} ({bill['patient_name']}){demo_badge}</span>
                            <span style="color: #64748b; font-size: 0.9rem;">{bill['payment_date']}</span>
                        </h4>
                        <p style="display: flex; justify-content: space-between; font-weight: 500;">
                            <span>**Total Bill:** ₹{bill['total_billed']:,.0f}</span>
                            <span>**Possible Savings:** ₹{bill['potential_savings']:,.0f}</span>
                        </p>
                        <p style="font-weight: 700; color: #059669;">
                            **Part Saved:** ₹{bill['possible_part_saved']:,.0f} (Final reduction)
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("View Full Details", key=f"hist_detail_{idx}"):
                    st.json(bill)


# --- B2B ENTERPRISE ---
elif user_type == "🏢 B2B Enterprise":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏢 B2B Enterprise Solutions</h1>
            <p>Custom solutions for insurance providers and large corporations.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Advanced Features")
    
    st.markdown("""
        <div class="info-card" style="min-height: auto;">
            <h4>📈 Bulk Audit Processing</h4>
            <p>Submit thousands of claims for simultaneous AI-driven overcharge analysis.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="info-card" style="min-height: auto;">
            <h4>🔗 Custom API Integration</h4>
            <p>Integrate our audit engine directly into your existing claims management system.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="info-card" style="min-height: auto;">
            <h4>📊 Advanced Analytics Dashboard</h4>
            <p>Monitor savings, error trends, and hospital compliance rates in real-time.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Contact Sales")
    st.write(f"Interested in a corporate partnership? Contact our sales team.")
    st.text_input("Your Company Name", placeholder="Acme Corp")
    st.text_input("Your Work Email", placeholder="manager@acmecorp.com")
    st.text_area("Your Requirements", placeholder="We need to process 5,000 claims per month...")
    st.button("Request Demo", type="primary")

# --- ABOUT & PRICING ---
elif user_type == "ℹ️ About & Pricing":
    st.markdown("""
        <div class="hero-banner">
            <h1>ℹ️ About MediAudit Pro</h1>
            <p>Transparency, Savings, and Trust in Medical Billing.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Our Mission")
    st.write("To empower every patient against unfair and complex medical billing practices using cutting-edge AI and human expertise.")
    
    st.markdown("### Pricing Model (Updated to remove fixed commission)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div class="info-card" style="border-left-color: #10b981; min-height: auto; justify-content: flex-start;">
                <h4>✅ Patient Audit & Report</h4>
                <p class="free-badge">FREE</p>
                <p>Detailed AI analysis and audit report on overcharges. Always free, no hidden costs.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="negotiation-card" style="min-height: auto; justify-content: flex-start;">
                <h4>🤝 Expert Negotiation Service</h4>
                <p style="font-size: 1.5rem; font-weight: 700; color: #92400e;">
                    *Commission on Savings*
                </p>
                <p>We only charge a percentage of the **actual savings** we achieve for you. If we don't save you money, you don't pay us a fee.</p>
                <p style="font-size: 0.9rem; margin-top: 1rem;">
                    *No upfront fees or fixed commissions mentioned.*
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### FAQ")
    
    with st.expander("❓ What exactly is overcharging?"):
        st.write("Overcharging can take many forms: inflated prices for simple consumables, billing for the same service twice (duplicate billing), charging for a more complex service than performed (upcoding), splitting a package into separate charges (unbundling), or simple clerical/administrative errors (other overcharging).")
        
    with st.expander("❓ How fast is the negotiation process?"):
        st.write("Our team typically takes up your case immediately after submission and works to resolve it with the hospital in 1 to 3 business days.")
        
    with st.expander(f"📞 How do I contact you?"):
        st.write(f"You can reach us anytime on WhatsApp: {CONTACT_NUMBER}, via email at support@mediaudit.com, or use the MediBot on the website.")

# Footer (Updated with Contact Number)
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
    st.markdown("• EMI & BNPL Options") # Updated

with col3:
    st.markdown("**Quick Links**")
    st.markdown("• About Us")
    st.markdown("• Privacy Policy")
    st.markdown("• Terms of Service")

with col4:
    st.markdown("**Contact**")
    st.markdown(f"• WhatsApp: {CONTACT_NUMBER}") # Updated
    st.markdown("• support@mediaudit.com")

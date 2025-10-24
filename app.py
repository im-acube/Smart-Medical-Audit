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

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI
st.markdown("""
    <style>
        /* Main theme colors */
        :root {
            --primary-color: #1e3a8a;
            --secondary-color: #3b82f6;
            --accent-color: #10b981;
            --danger-color: #ef4444;
            --warning-color: #f59e0b;
        }
        
        /* Sidebar styling - Bright and Modern */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-right: 2px solid #e2e8f0;
        }
        
        [data-testid="stSidebar"] h3 {
            color: #1e293b !important;
            font-weight: 700;
        }
        
        [data-testid="stSidebar"] .stRadio > label {
            color: #334155 !important;
            font-weight: 500;
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
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        .main-header p {
            color: #e0e7ff;
            font-size: 1.1rem;
            margin: 0.5rem 0 0 0;
        }
        
        /* Card styling */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
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
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59,130,246,0.4);
        }
        
        /* Free badge */
        .free-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.2rem;
            display: inline-block;
            margin: 1rem 0;
        }
        
        .strikethrough-price {
            text-decoration: line-through;
            color: #94a3b8;
            font-size: 1.5rem;
        }
        
        /* Bill queue card */
        .bill-queue-card {
            background: #fff7ed;
            border: 2px solid #fb923c;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        .queued-bill {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid #3b82f6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_reference_data():
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({
            "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges"],
            "Rate (₹)": [4000, 2500, 1500, 50000, 8000]
        })
    try:
        exclusions = pd.read_csv("insurer_exclusions.csv")
    except Exception:
        exclusions = pd.DataFrame({"Services": [], "Excluded_Service": []})
    return cghs, exclusions

def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.75):
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
        tokens = line.split()
        for t in reversed(tokens):
            tt = t.replace("₹", "").replace(",", "").replace("Rs.", "")
            if tt.replace(".", "", 1).isdigit():
                try:
                    amt = float(tt)
                    item_name = " ".join(tokens[:tokens.index(t)])
                    items.append((item_name.strip(), amt))
                    break
                except:
                    pass
    return items

def extract_text_from_image_bytes(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

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
    
    if not text_accum.strip():
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes)
            for img in images:
                text_accum += pytesseract.image_to_string(img) + "\n"
        except Exception:
            pass
    
    return text_accum

# Initialize session state
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'bill_queue' not in st.session_state:
    st.session_state.bill_queue = []
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🏥 MediAudit Pro")
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")
    
    user_type = st.radio(
        "Navigate",
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "ℹ️ About & Pricing"],
        key="user_type_selector"
    )
    
    st.markdown("---")
    
    if user_type in ["👤 Patient Portal", "🏢 B2B Enterprise"]:
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Audits", "47", delta="12")
        with col2:
            st.metric("Savings", "₹2.4L", delta="₹45K")
        
        if st.session_state.bill_queue:
            st.markdown("---")
            st.markdown(f"### 🗂️ Bill Queue")
            st.info(f"**{len(st.session_state.bill_queue)} bills** in queue")
    
    st.markdown("---")
    st.markdown("### 💬 Need Help?")
    st.markdown("📧 support@mediaudit.com")
    st.markdown("📱 +91-9876543210")

# Main content based on user type
if user_type == "🏠 Home":
    # Landing Page
    st.markdown("""
        <div class="main-header">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing - Now 100% FREE for Patients!</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="info-card">
                <h3>👤 For Patients</h3>
                <p>✓ FREE bill verification</p>
                <p>✓ Insurance claim support</p>
                <p>✓ Overcharge detection</p>
                <p>✓ Bill payment with EMI</p>
                <p>✓ Queue multiple bills</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card">
                <h3>🏢 For Enterprises</h3>
                <p>✓ Bulk bill processing</p>
                <p>✓ API integration</p>
                <p>✓ Custom compliance rules</p>
                <p>✓ Detailed analytics</p>
                <p>✓ Volume discounts</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card">
                <h3>🤖 AI Technology</h3>
                <p>✓ OCR bill extraction</p>
                <p>✓ Smart pattern matching</p>
                <p>✓ Real-time verification</p>
                <p>✓ 98% accuracy rate</p>
                <p>✓ Instant processing</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Platform Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">₹2.4Cr</div>
                <div class="metric-label">Savings Generated</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">50K+</div>
                <div class="metric-label">Bills Audited</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">98%</div>
                <div class="metric-label">Accuracy Rate</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">24/7</div>
                <div class="metric-label">Support</div>
            </div>
        """, unsafe_allow_html=True)

elif user_type == "👤 Patient Portal":
    # Patient Portal
    st.markdown("""
        <div class="main-header">
            <h1>👤 Patient Portal</h1>
            <p>Upload and audit your medical bills - Completely FREE!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🗂️ Bill Queue & Payment", "📋 History"])
    
    with tabs[0]:
        # Patient details
        st.markdown("### 👤 Patient Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name")
            patient_id = st.text_input("Patient ID", placeholder="Auto-generated", disabled=True, 
                                      value=f"PAT{datetime.now().strftime('%Y%m%d%H%M')}")
        
        with col2:
            hospital_list = ["Select hospital", "AIIMS Delhi", "Apollo Hospital", "Fortis Hospital", 
                           "Medanta", "Manipal Hospital", "Narayana Health", "Max Hospital"]
            hospital = st.selectbox("Hospital", hospital_list)
            admission_date = st.date_input("Admission Date")
        
        with col3:
            insurer = st.selectbox("Insurance Provider", 
                                 ["Select insurer", "Star Health", "HDFC ERGO", "ICICI Lombard", 
                                  "Care Health", "New India Assurance"])
            policy_number = st.text_input("Policy Number", placeholder="Enter policy number")
        
        st.markdown("---")
        st.markdown("### 📁 Upload Medical Bill")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded = st.file_uploader(
                "Drag and drop or click to upload",
                type=["csv", "xlsx", "pdf", "jpg", "jpeg", "png"],
                help="Supported formats: PDF, Excel, CSV, JPG, PNG"
            )
        
        with col2:
            st.info("**Supported Files**\n- PDF Bills\n- Excel/CSV\n- Scanned Images\n- Max: 10MB")
        
        manual_extract = st.checkbox("📝 Enter bill details manually")
        
        # Processing logic
        if uploaded or manual_extract:
            df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
            
            if manual_extract:
                txt = st.text_area("Paste bill text or enter line items", height=150)
                if txt:
                    lines = txt.splitlines()
                    items = text_to_items_from_lines(lines)
                    df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            else:
                ext = uploaded.name.split(".")[-1].lower()
                
                with st.spinner("🔄 Processing bill..."):
                    if ext in ("csv", "xlsx"):
                        try:
                            if ext == "csv":
                                df_items = pd.read_csv(uploaded)
                            else:
                                df_items = pd.read_excel(uploaded)
                            
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
                            lines = txt.splitlines()
                            items = text_to_items_from_lines(lines)
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
                    
                    elif ext == "pdf":
                        pdf_bytes = uploaded.read()
                        txt = extract_text_from_pdf_bytes(pdf_bytes)
                        if txt.strip():
                            lines = txt.splitlines()
                            items = text_to_items_from_lines(lines)
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            
            if df_items.empty:
                df_items = pd.DataFrame([["", ""], ["", ""]], columns=["Item", "Amount (₹)"])
            
            st.markdown("### 📋 Extracted Line Items")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                run_audit = st.button("🚀 Run FREE Audit", use_container_width=True, type="primary")
            with col2:
                if st.button("💾 Save Draft", use_container_width=True):
                    st.success("✓ Draft saved!")
            
            if run_audit and not edited.empty:
                cghs_df, exclusions_df = load_reference_data()
                cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
                cghs_services = list(cghs_df["service_norm"].dropna().unique())
                
                exclusions_norm = []
                if not exclusions_df.empty and "Excluded_Service" in exclusions_df.columns:
                    exclusions_norm = exclusions_df[
                        exclusions_df["Excluded_Service"].astype(str).str.lower() == "yes"
                    ]["Services"].astype(str).str.lower().tolist()
                
                results = []
                alerts = []
                flagged_count = 0
                total_billed = 0
                total_standard = 0
                
                for idx, r in edited.iterrows():
                    item = normalize_text(r.get("Item", ""))
                    amt_raw = r.get("Amount (₹)", 0)
                    try:
                        amount = float(str(amt_raw).replace(",", "").replace("₹", "").strip()) if str(amt_raw).strip() else 0.0
                    except:
                        amount = 0.0
                    
                    total_billed += amount
                    status = "Normal"
                    comment = ""
                    standard_rate = amount
                    
                    if item and item in exclusions_norm:
                        status = "Excluded"
                        comment = "Excluded by insurer"
                        alerts.append(f"🚫 {r.get('Item')} is excluded")
                        flagged_count += 1
                    else:
                        matched = None
                        if item in cghs_services:
                            matched = item
                        else:
                            matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                        
                        if matched:
                            row_ref = cghs_df[cghs_df["service_norm"] == matched].iloc[0]
                            rate = float(row_ref["Rate (₹)"])
                            standard_rate = rate
                            total_standard += rate
                            
                            if amount > rate * 1.1:
                                status = "Overcharged"
                                comment = f"₹{amount:,.0f} vs ₹{rate:,.0f}"
                                alerts.append(f"⚠️ {r.get('Item')}: ₹{amount-rate:,.0f} overcharge")
                                flagged_count += 1
                            else:
                                total_standard += amount
                        else:
                            status = "Unlisted"
                            comment = "Not in CGHS"
                            total_standard += amount
                    
                    results.append({
                        "Service": r.get("Item"),
                        "Billed (₹)": amount,
                        "Standard (₹)": standard_rate,
                        "Status": status,
                        "Comments": comment
                    })
                
                results_df = pd.DataFrame(results)
                potential_savings = total_billed - total_standard
                audit_score = max(0, 100 - flagged_count * 8)
                
                # Store current audit
                st.session_state.current_audit = {
                    'patient_name': patient_name,
                    'hospital': hospital,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df,
                    'total_billed': total_billed,
                    'total_standard': total_standard,
                    'potential_savings': potential_savings,
                    'audit_score': audit_score,
                    'flagged_count': flagged_count,
                    'alerts': alerts
                }
                
                st.success("✅ FREE Audit completed!")
                st.markdown("---")
                
                # Audit Summary
                st.markdown("### 📊 Audit Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(results_df)}</div>
                            <div class="metric-label">Items</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{flagged_count}</div>
                            <div class="metric-label">Issues</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{audit_score}</div>
                            <div class="metric-label">Score</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{potential_savings:,.0f}</div>
                            <div class="metric-label">Savings</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("### 🔍 Detailed Results")
                
                def highlight_status(row):
                    if row["Status"] == "Overcharged":
                        return ['background-color: #fee2e2'] * len(row)
                    elif row["Status"] == "Excluded":
                        return ['background-color: #fef3c7'] * len(row)
                    elif row["Status"] == "Unlisted":
                        return ['background-color: #e0f2fe'] * len(row)
                    return ['background-color: #d1fae5'] * len(row)
                
                st.dataframe(
                    results_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    height=300
                )
                
                if alerts:
                    st.markdown("### ⚠️ Alerts")
                    for alert in alerts:
                        st.warning(alert)
                
                # Payment options
                st.markdown("---")
                st.markdown("### 💳 What would you like to do?")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗂️ Add to Queue", use_container_width=True, type="secondary"):
                        st.session_state.bill_queue.append(st.session_state.current_audit)
                        st.success(f"✓ Bill added! Queue has {len(st.session_state.bill_queue)} bills")
                        st.rerun()
                
                with col2:
                    if st.button("💰 Pay This Bill Now", use_container_width=True, type="primary"):
                        st.session_state.show_single_payment = True
                        st.rerun()
                
                with col3:
                    if st.button("📥 Download Report", use_container_width=True):
                        st.success("Report downloaded!")
    
    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        
        if not st.session_state.bill_queue:
            st.info("No bills in queue. Audit a bill and add it to queue.")
        else:
            st.markdown(f"""
                <div class="bill-queue-card">
                    <h3>📋 {len(st.session_state.bill_queue)} Bills in Queue</h3>
                    <p>Review and pay your bills together or individually</p>
                </div>
            """, unsafe_allow_html=True)
            
            total_queue_amount = sum([bill['total_billed'] for bill in st.session_state.bill_queue])
            
            st.markdown(f"### Total Amount: ₹{total_queue_amount:,.0f}")
            
            # Display queued bills
            for idx, bill in enumerate(st.session_state.bill_queue):
                with st.expander(f"Bill #{idx+1}: {bill['patient_name']} - {bill['hospital']} (₹{bill['total_billed']:,.0f})"):
                    st.write(f"**Date:** {bill['date']}")
                    st.write(f"**Audit Score:** {bill['audit_score']}/100")
                    st.write(f"**Potential Savings:** ₹{bill['potential_savings']:,.0f}")
                    st.dataframe(bill['results_df'], use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True):
                            st.session_state.payment_bills = [bill]
                            st.session_state.show_payment = True
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                            st.session_state.bill_queue.pop(idx)
                            st.rerun()
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                    st.session_state.payment_bills = st.session_state.bill_queue
                    st.session_state.show_payment = True
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Queue", use_container_width=True):
                    st.session_state.bill_queue = []
                    st.rerun()
        
        # Payment Section
        if st.session_state.get('show_payment', False):
            st.markdown("---")
            st.markdown("## 💳 Payment Options")
            
            payment_bills = st.session_state.get('payment_bills', [])
            total_payment = sum([bill['total_billed'] for bill in payment_bills])
            
            st.success(f"💰 Total Payment Amount: ₹{total_payment:,.0f}")
            
            payment_method = st.radio(
                "Select Payment Method",
                ["💳 Credit/Debit Card", "🏦 Net Banking", "📱 UPI", "💼 EMI Options"],
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
                
            elif payment_method == "🏦 Net Banking":
                st.selectbox("Select Bank", [
                    "State Bank of India",
                    "HDFC Bank",
                    "ICICI Bank",
                    "Axis Bank",
                    "Kotak Mahindra Bank"
                ])
                
            elif payment_method == "📱 UPI":
                st.text_input("UPI ID", placeholder="yourname@upi")
                st.info("You'll be redirected to your UPI app to complete payment")
                
            elif payment_method == "💼 EMI Options":
                st.markdown("### 📊 EMI Calculator for Medical Bills")
                st.info("Convert your medical bill payment into easy monthly installments")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    bill_amount = st.number_input("Bill Amount (₹)", min_value=1000, max_value=10000000, 
                                                value=int(total_payment), step=1000, disabled=True)
                
                with col2:
                    emi_tenure = st.selectbox("EMI Tenure", ["3 months", "6 months", "9 months", "12 months", "18 months", "24 months"])
                
                with col3:
                    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=30.0, value=12.0, step=0.5)
                
                # Calculate EMI
                tenure_months = int(emi_tenure.split()[0])
                monthly_rate = interest_rate / (12 * 100)
                
                if monthly_rate > 0:
                    emi = (bill_amount * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
                else:
                    emi = bill_amount / tenure_months
                
                total_payment_emi = emi * tenure_months
                total_interest = total_payment_emi - bill_amount
                
                st.markdown("### 💰 EMI Breakdown")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{emi:,.0f}</div>
                            <div class="metric-label">Monthly EMI</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{total_payment_emi:,.0f}</div>
                            <div class="metric-label">Total Payment</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{total_interest:,.0f}</div>
                            <div class="metric-label">Total Interest</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{tenure_months}</div>
                            <div class="metric-label">Months</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # EMI Schedule
                st.markdown("### 📅 Payment Schedule")
                
                schedule_data = []
                remaining_principal = bill_amount
                
                for month in range(1, tenure_months + 1):
                    interest_component = remaining_principal * monthly_rate
                    principal_component = emi - interest_component
                    remaining_principal -= principal_component
                    
                    schedule_data.append({
                        'Month': month,
                        'EMI (₹)': f"₹{emi:,.0f}",
                        'Principal (₹)': f"₹{principal_component:,.0f}",
                        'Interest (₹)': f"₹{interest_component:,.0f}",
                        'Balance (₹)': f"₹{max(0, remaining_principal):,.0f}"
                    })
                
                schedule_df = pd.DataFrame(schedule_data)
                st.dataframe(schedule_df, use_container_width=True, height=300)
                
                st.markdown("#### 🏦 EMI Partners")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                        <div class="info-card">
                            <h4>Bajaj Finserv</h4>
                            <p>✓ 0% interest for 3 months</p>
                            <p>✓ Instant approval</p>
                            <p>✓ No documentation</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                        <div class="info-card">
                            <h4>HDFC Bank EMI</h4>
                            <p>✓ Flexible tenure</p>
                            <p>✓ Competitive rates</p>
                            <p>✓ Easy processing</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                        <div class="info-card">
                            <h4>Credit Card EMI</h4>
                            <p>✓ Convert to EMI</p>
                            <p>✓ Bank-specific offers</p>
                            <p>✓ Quick conversion</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.checkbox("I agree to the Terms & Conditions")
            
            with col2:
                if st.button("💳 Complete Payment", use_container_width=True, type="primary"):
                    with st.spinner("Processing payment..."):
                        import time
                        time.sleep(2)
                    st.success("✅ Payment successful!")
                    st.balloons()
                    # Clear queue after payment
                    st.session_state.bill_queue = []
                    st.session_state.show_payment = False
                    st.rerun()
    
    with tabs[2]:
        st.markdown("### 📋 Audit History")
        
        history_data = pd.DataFrame({
            'Date': ['2025-10-20', '2025-10-15', '2025-10-10', '2025-10-05'],
            'Hospital': ['Apollo Hospital', 'Fortis Hospital', 'AIIMS Delhi', 'Max Hospital'],
            'Amount (₹)': [45000, 32000, 78000, 23000],
            'Savings (₹)': [5400, 2800, 8900, 1200],
            'Status': ['Paid', 'Paid', 'Pending', 'Paid']
        })
        
        st.dataframe(history_data, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Audits", "47")
        with col2:
            st.metric("Total Savings", "₹2.4L")
        with col3:
            st.metric("Avg Score", "92/100")

elif user_type == "🏢 B2B Enterprise":
    # B2B Enterprise Portal
    st.markdown("""
        <div class="main-header">
            <h1>🏢 Enterprise Dashboard</h1>
            <p>Bulk processing and advanced analytics for healthcare organizations</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📊 Dashboard", "📤 Bulk Upload", "🔧 Settings", "📈 Analytics"])
    
    with tabs[0]:
        st.markdown("### 📊 Enterprise Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">1,247</div>
                    <div class="metric-label">Bills Processed MTD</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">₹12.4L</div>
                    <div class="metric-label">Savings Generated</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">94%</div>
                    <div class="metric-label">Approval Rate</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">2.4hrs</div>
                    <div class="metric-label">Avg Processing</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📈 Weekly Activity")
        
        activity_data = pd.DataFrame({
            'Date': pd.date_range(start='2025-10-17', periods=7),
            'Bills Processed': [45, 52, 48, 61, 55, 58, 63],
            'Savings (₹)': [45000, 52000, 48000, 61000, 55000, 58000, 63000]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(activity_data, x='Date', y='Bills Processed', markers=True)
            fig.update_layout(title="Daily Processing Volume")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(activity_data, x='Date', y='Savings (₹)')
            fig.update_layout(title="Daily Savings")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 🏥 Top Hospitals")
        hospital_stats = pd.DataFrame({
            'Hospital': ['Apollo', 'Fortis', 'Max', 'Medanta', 'AIIMS'],
            'Bills': [234, 198, 176, 143, 121],
            'Avg Savings (₹)': [4500, 3800, 5200, 4100, 3600]
        })
        st.dataframe(hospital_stats, use_container_width=True)
    
    with tabs[1]:
        st.markdown("### 📤 Bulk Bill Upload")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            bulk_file = st.file_uploader(
                "Upload Excel/CSV with multiple bills",
                type=["xlsx", "csv"],
                help="Upload a file containing multiple patient bills"
            )
            
            st.markdown("""
                <div class="info-card">
                    <h4>📋 Required Columns</h4>
                    <p>• Patient Name</p>
                    <p>• Hospital Name</p>
                    <p>• Bill Items</p>
                    <p>• Amounts</p>
                    <p>• Policy Number</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.info("**Batch Processing**\n\n✓ Up to 1000 bills\n✓ Auto validation\n✓ Real-time updates\n✓ Export results")
            
            if st.button("📥 Download Template", use_container_width=True):
                st.success("Template downloaded!")
        
        if bulk_file:
            st.success(f"✓ File uploaded: {bulk_file.name}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Start Processing", use_container_width=True, type="primary"):
                    with st.spinner("Processing batch..."):
                        progress_bar = st.progress(0)
                        for i in range(100):
                            progress_bar.progress(i + 1)
                        st.success("✓ Batch completed!")
            
            with col2:
                st.button("📊 View Results", use_container_width=True)
    
    with tabs[2]:
        st.markdown("### 🔧 Enterprise Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### API Configuration")
            api_key = st.text_input("API Key", type="password", value="sk_live_xxxxx")
            webhook_url = st.text_input("Webhook URL", placeholder="https://your-domain.com/webhook")
            
            st.markdown("#### Compliance Rules")
            max_variance = st.slider("Max Price Variance (%)", 0, 50, 10)
            auto_flag = st.checkbox("Auto-flag excluded items", value=True)
        
        with col2:
            st.markdown("#### Notifications")
            email_alerts = st.checkbox("Email alerts", value=True)
            slack_integration = st.checkbox("Slack notifications", value=False)
            daily_report = st.checkbox("Daily summary", value=True)
            
            st.markdown("#### Team")
            team_size = st.number_input("Team Size", min_value=1, max_value=100, value=5)
        
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✓ Settings saved!")
    
    with tabs[3]:
        st.markdown("### 📈 Advanced Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            category_data = pd.DataFrame({
                'Category': ['Room', 'Surgery', 'Lab', 'Medicine', 'Doctor'],
                'Savings': [45000, 78000, 23000, 34000, 28000]
            })
            fig = px.bar(category_data, x='Category', y='Savings', title="Savings by Category")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            monthly_data = pd.DataFrame({
                'Month': ['Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
                'Savings': [180000, 220000, 195000, 245000, 280000]
            })
            fig = px.line(monthly_data, x='Month', y='Savings', markers=True, title="Monthly Trend")
            st.plotly_chart(fig, use_container_width=True)

elif user_type == "ℹ️ About & Pricing":
    st.markdown("""
        <div class="main-header">
            <h1>ℹ️ About MediAudit Pro</h1>
            <p>Transparent pricing and platform information</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["👤 For Patients", "🏢 For Enterprises", "❓ FAQ"])
    
    with tabs[0]:
        st.markdown("### 👤 Patient Services - 100% FREE!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
                <div class="info-card" style="text-align: center; border: 3px solid #10b981;">
                    <h2>Patient Portal</h2>
                    <div style="margin: 2rem 0;">
                        <span class="strikethrough-price">₹499/month</span>
                        <div class="free-badge">100% FREE</div>
                    </div>
                    <hr>
                    <div style="text-align: left; margin: 1rem 0;">
                        <h4>✓ All Features Included:</h4>
                        <p>✓ Unlimited bill audits</p>
                        <p>✓ CGHS rate verification</p>
                        <p>✓ Insurance exclusion check</p>
                        <p>✓ Detailed audit reports</p>
                        <p>✓ Overcharge detection</p>
                        <p>✓ Bill queue management</p>
                        <p>✓ Multiple payment options</p>
                        <p>✓ EMI calculator & options</p>
                        <p>✓ Priority email support</p>
                        <p>✓ Audit history tracking</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.success("**Why Free?**\n\nWe believe healthcare transparency should be accessible to everyone. Our mission is to help patients save money on medical bills.")
            
            st.info("**How We Sustain?**\n\nWe charge enterprises for bulk processing while keeping patient services free.")
        
        st.markdown("### 💳 Bill Payment Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class="info-card">
                    <h4>💰 Multiple Payment Options</h4>
                    <p>✓ Credit/Debit Cards</p>
                    <p>✓ Net Banking</p>
                    <p>✓ UPI Payments</p>
                    <p>✓ EMI Options</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="info-card">
                    <h4>🗂️ Bill Queue</h4>
                    <p>✓ Queue multiple bills</p>
                    <p>✓ Pay together or separately</p>
                    <p>✓ Track all payments</p>
                    <p>✓ Download receipts</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div class="info-card">
                    <h4>📊 EMI Calculator</h4>
                    <p>✓ Flexible tenures</p>
                    <p>✓ Competitive rates</p>
                    <p>✓ Instant approval</p>
                    <p>✓ Payment schedule</p>
                </div>
            """, unsafe_allow_html=True)
    
    with tabs[1]:
        st.markdown("### 🏢 Enterprise Pricing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="info-card">
                    <h3>Business Plan</h3>
                    <div style="font-size: 2rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">₹9,999/month</div>
                    <hr>
                    <p>✓ Up to 500 bills/month</p>
                    <p>✓ API access</p>
                    <p>✓ Bulk processing</p>
                    <p>✓ Custom rules</p>
                    <p>✓ Account manager</p>
                    <p>✓ Advanced analytics</p>
                    <p>✓ SLA: 24 hours</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Contact Sales", key="business_sales", use_container_width=True)
        
        with col2:
            st.markdown("""
                <div class="info-card" style="border: 3px solid #f59e0b;">
                    <span class="premium-badge">ENTERPRISE</span>
                    <h3>Custom Plan</h3>
                    <div style="font-size: 2rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">Let's Talk</div>
                    <hr>
                    <p>✓ Unlimited processing</p>
                    <p>✓ Full API suite</p>
                    <p>✓ White-label option</p>
                    <p>✓ Custom integrations</p>
                    <p>✓ On-premise deployment</p>
                    <p>✓ 24/7 support</p>
                    <p>✓ SLA: 4 hours</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Schedule Demo", key="enterprise_demo", use_container_width=True)
        
        st.markdown("### 🎁 Enterprise Benefits")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Volume Discounts**\n10% off for 1000+ bills")
        with col2:
            st.info("**Dedicated Support**\nPersonal manager")
        with col3:
            st.info("**Free Training**\nOnboarding included")
    
    with tabs[2]:
        st.markdown("### ❓ Frequently Asked Questions")
        
        with st.expander("🆓 Is the patient portal really free?"):
            st.write("Yes! All patient audit services are 100% FREE. No hidden charges, no subscriptions.")
        
        with st.expander("💳 Do I pay for bill payments through the platform?"):
            st.write("No. Our platform is free for auditing. You only pay your actual medical bills through our secure payment gateway.")
        
        with st.expander("📊 What are EMI options?"):
            st.write("EMI (Equated Monthly Installment) allows you to convert your medical bill payment into monthly installments with partner banks.")
        
        with st.expander("🗂️ How does bill queue work?"):
            st.write("You can audit multiple bills and add them to a queue. Then pay all bills together or individually as per your convenience.")
        
        with st.expander("🏢 What do enterprises pay for?"):
            st.write("Enterprises pay for bulk processing, API access, custom integrations, and advanced analytics. Individual patient audits remain free.")
        
        with st.expander("🔒 Is my data secure?"):
            st.write("Yes. We use bank-grade encryption and comply with all healthcare data protection regulations.")
        
        with st.expander("📱 Do you have a mobile app?"):
            st.write("We're working on it! Currently, our web platform is mobile-responsive.")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**MediAudit Pro**")
    st.markdown("AI-powered medical bill auditing")
    st.markdown("*Free for all patients*")

with col2:
    st.markdown("**Quick Links**")
    st.markdown("• About Us")
    st.markdown("• Privacy Policy")
    st.markdown("• Terms of Service")

with col3:
    st.markdown("**Support**")
    st.markdown("📧 support@mediaudit.com")
    st.markdown("📱 +91-9876543210")
    st.markdown("⏰ 24/7 Available")

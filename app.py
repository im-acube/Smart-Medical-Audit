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
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a8a 0%, #2563eb 100%);
        }
        
        [data-testid="stSidebar"] .css-1d391kg, [data-testid="stSidebar"] .st-emotion-cache-1dp5vir {
            color: white !important;
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
        
        /* Status badges */
        .status-normal {
            background: #d1fae5;
            color: #065f46;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-weight: 600;
        }
        
        .status-overcharged {
            background: #fee2e2;
            color: #991b1b;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-weight: 600;
        }
        
        .status-excluded {
            background: #fef3c7;
            color: #92400e;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-weight: 600;
        }
        
        /* Payment card */
        .payment-option {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #e5e7eb;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .payment-option:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59,130,246,0.2);
        }
        
        .payment-selected {
            border-color: #3b82f6;
            background: #eff6ff;
        }
        
        /* Premium badge */
        .premium-badge {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.75rem;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 2rem;
            border-radius: 8px 8px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Helper functions (keeping your existing functions)
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
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🏥 MediAudit Pro")
    st.markdown("---")
    
    user_type = st.radio(
        "Select User Type",
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "💳 Pricing & Plans"],
        key="user_type_selector"
    )
    
    st.markdown("---")
    
    if user_type in ["👤 Patient Portal", "🏢 B2B Enterprise"]:
        st.markdown("### Quick Stats")
        st.metric("Audits Today", "47")
        st.metric("Savings Generated", "₹2.4L")
        st.metric("Active Users", "1,243")
    
    st.markdown("---")
    st.markdown("### 📞 Support")
    st.markdown("📧 support@mediaudit.com")
    st.markdown("📱 +91-9876543210")
    st.markdown("⏰ 24/7 Available")

# Main content based on user type
if user_type == "🏠 Home":
    # Landing Page
    st.markdown("""
        <div class="main-header">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing & Insurance Claims Management</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="info-card">
                <h3>👤 For Patients</h3>
                <p>✓ Instant bill verification</p>
                <p>✓ Insurance claim support</p>
                <p>✓ Overcharge detection</p>
                <p>✓ EMI payment options</p>
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
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Key Benefits")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">₹2.4Cr</div>
                <div class="metric-label">Total Savings Generated</div>
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
                <div class="metric-label">Support Available</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("**Step 1**\n📤 Upload Bill")
    with col2:
        st.info("**Step 2**\n🤖 AI Processing")
    with col3:
        st.info("**Step 3**\n📊 Get Audit Report")
    with col4:
        st.info("**Step 4**\n💰 Track Savings")

elif user_type == "👤 Patient Portal":
    # Patient Portal
    st.markdown("""
        <div class="main-header">
            <h1>👤 Patient Portal</h1>
            <p>Upload and audit your medical bills instantly</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 Upload Bill", "📋 My Audits", "💳 Payment History"])
    
    with tabs[0]:
        # Patient details
        st.markdown("### 👤 Patient Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name")
            patient_id = st.text_input("Patient ID", placeholder="Auto-generated", disabled=True, value=f"PAT{datetime.now().strftime('%Y%m%d%H%M')}")
        
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
            st.info("**Supported Files**\n- PDF Bills\n- Excel/CSV\n- Scanned Images\n- Max size: 10MB")
        
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
                                if "amount" in lc or "₹" in lc or "rs" in lc or "cost" in lc:
                                    col_map[c] = "Amount (₹)"
                            df_items = df_items.rename(columns=col_map)
                            
                            if "Item" in df_items.columns and "Amount (₹)" in df_items.columns:
                                df_items = df_items[["Item", "Amount (₹)"]]
                            else:
                                st.warning("Could not identify Item and Amount columns automatically.")
                        except Exception as e:
                            st.error(f"Error reading file: {e}")
                    
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
            st.info("Review and edit the extracted items before auditing")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                run_audit = st.button("🚀 Run Audit", use_container_width=True)
            with col2:
                if st.button("💾 Save Draft", use_container_width=True):
                    st.success("✓ Draft saved successfully!")
            
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
                        alerts.append(f"🚫 {r.get('Item')} is excluded by your insurance")
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
                                comment = f"Charged ₹{amount:,.0f}, Standard ₹{rate:,.0f}"
                                alerts.append(f"⚠️ {r.get('Item')}: Overcharged by ₹{amount-rate:,.0f}")
                                flagged_count += 1
                            else:
                                total_standard += amount
                        else:
                            status = "Unlisted"
                            comment = "Service not in CGHS list"
                            total_standard += amount
                    
                    results.append({
                        "Service": r.get("Item"),
                        "Billed Amount (₹)": amount,
                        "Standard Rate (₹)": standard_rate,
                        "Status": status,
                        "Comments": comment
                    })
                
                results_df = pd.DataFrame(results)
                potential_savings = total_billed - total_standard
                audit_score = max(0, 100 - flagged_count * 8)
                
                st.session_state.audit_results = {
                    'results_df': results_df,
                    'total_items': len(results_df),
                    'flagged_count': flagged_count,
                    'audit_score': audit_score,
                    'total_billed': total_billed,
                    'total_standard': total_standard,
                    'potential_savings': potential_savings,
                    'alerts': alerts
                }
                
                st.success("✅ Audit completed successfully!")
                st.markdown("---")
                
                # Audit Summary
                st.markdown("### 📊 Audit Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(results_df)}</div>
                            <div class="metric-label">Total Items</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{flagged_count}</div>
                            <div class="metric-label">Issues Found</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{audit_score}</div>
                            <div class="metric-label">Audit Score</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{potential_savings:,.0f}</div>
                            <div class="metric-label">Potential Savings</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("### 🔍 Detailed Audit Results")
                
                # Color-coded dataframe
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
                    height=400
                )
                
                # Visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    status_counts = results_df['Status'].value_counts()
                    fig = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="Audit Status Distribution",
                        color_discrete_map={
                            'Normal': '#10b981',
                            'Overcharged': '#ef4444',
                            'Excluded': '#f59e0b',
                            'Unlisted': '#3b82f6'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = go.Figure(data=[
                        go.Bar(name='Billed', x=['Total'], y=[total_billed], marker_color='#ef4444'),
                        go.Bar(name='Standard', x=['Total'], y=[total_standard], marker_color='#10b981')
                    ])
                    fig.update_layout(title="Billing Comparison", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Alerts
                if alerts:
                    st.markdown("### ⚠️ Important Alerts")
                    for alert in alerts:
                        st.warning(alert)
                
                # Payment options
                if potential_savings > 0 or total_billed > 10000:
                    st.markdown("---")
                    if st.button("💳 Proceed to Payment Options", use_container_width=True):
                        st.session_state.show_payment = True
                        st.rerun()
    
    with tabs[1]:
        st.markdown("### 📋 My Previous Audits")
        
        # Sample audit history
        audit_history = pd.DataFrame({
            'Date': ['2025-10-20', '2025-10-15', '2025-10-10'],
            'Hospital': ['Apollo Hospital', 'Fortis Hospital', 'AIIMS Delhi'],
            'Amount': [45000, 32000, 78000],
            'Savings': [5400, 2800, 8900],
            'Status': ['Completed', 'Completed', 'Under Review']
        })
        
        st.dataframe(audit_history, use_container_width=True)
    
    with tabs[2]:
        st.markdown("### 💳 Payment History")
        st.info("No payment history available yet")

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
                    <div class="metric-label">Avg Processing Time</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📈 Recent Activity")
        
        activity_data = pd.DataFrame({
            'Date': pd.date_range(start='2025-10-17', periods=7),
            'Bills Processed': [45, 52, 48, 61, 55, 58, 63],
            'Savings (₹)': [45000, 52000, 48000, 61000, 55000, 58000, 63000]
        })
        
        fig = px.line(activity_data, x='Date', y='Bills Processed', markers=True)
        fig.update_layout(title="Daily Processing Volume")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 🏥 Top Hospitals")
        hospital_stats = pd.DataFrame({
            'Hospital': ['Apollo', 'Fortis', 'Max', 'Medanta', 'AIIMS'],
            'Bills': [234, 198, 176, 143, 121],
            'Avg Savings': [4500, 3800, 5200, 4100, 3600]
        })
        st.dataframe(hospital_stats, use_container_width=True)
    
    with tabs[1]:
        st.markdown("### 📤 Bulk Bill Upload")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            bulk_file = st.file_uploader(
                "Upload Excel/CSV with multiple bills",
                type=["xlsx", "csv"],
                help="Upload a file containing multiple patient bills for batch processing"
            )
            
            st.markdown("""
                <div class="info-card">
                    <h4>📋 Required Columns</h4>
                    <p>• Patient Name</p>
                    <p>• Hospital Name</p>
                    <p>• Bill Items (JSON or separate columns)</p>
                    <p>• Amounts</p>
                    <p>• Policy Number (optional)</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.info("**Batch Processing**\n\n✓ Process up to 1000 bills\n✓ Automated validation\n✓ Real-time status updates\n✓ Export results")
            
            if st.button("📥 Download Sample Template", use_container_width=True):
                st.success("Template downloaded!")
        
        if bulk_file:
            st.success(f"✓ File uploaded: {bulk_file.name}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🚀 Start Batch Processing", use_container_width=True):
                    with st.spinner("Processing batch..."):
                        progress_bar = st.progress(0)
                        for i in range(100):
                            progress_bar.progress(i + 1)
                        st.success("✓ Batch processing completed!")
            
            with col2:
                st.button("⏸️ Pause Processing", use_container_width=True)
            
            with col3:
                st.button("📊 View Results", use_container_width=True)
    
    with tabs[2]:
        st.markdown("### 🔧 Enterprise Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### API Configuration")
            api_key = st.text_input("API Key", type="password", value="sk_live_xxxxx")
            webhook_url = st.text_input("Webhook URL", placeholder="https://your-domain.com/webhook")
            
            st.markdown("#### Compliance Rules")
            max_variance = st.slider("Maximum Price Variance (%)", 0, 50, 10)
            auto_flag = st.checkbox("Auto-flag excluded items", value=True)
            require_approval = st.checkbox("Require manual approval for high-value bills", value=True)
        
        with col2:
            st.markdown("#### Notification Settings")
            email_alerts = st.checkbox("Email alerts for flagged items", value=True)
            slack_integration = st.checkbox("Slack notifications", value=False)
            daily_report = st.checkbox("Daily summary report", value=True)
            
            st.markdown("#### Team Management")
            team_size = st.number_input("Team Size", min_value=1, max_value=100, value=5)
            st.multiselect("Assigned Users", ["admin@company.com", "user1@company.com", "user2@company.com"])
        
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✓ Settings saved successfully!")
    
    with tabs[3]:
        st.markdown("### 📈 Advanced Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Savings by category
            category_data = pd.DataFrame({
                'Category': ['Room Charges', 'Surgery', 'Lab Tests', 'Medicines', 'Doctor Fees'],
                'Savings': [45000, 78000, 23000, 34000, 28000]
            })
            fig = px.bar(category_data, x='Category', y='Savings', title="Savings by Category")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly trend
            monthly_data = pd.DataFrame({
                'Month': ['Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
                'Savings': [180000, 220000, 195000, 245000, 280000]
            })
            fig = px.line(monthly_data, x='Month', y='Savings', markers=True, title="Monthly Savings Trend")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 Performance Metrics")
        metrics_df = pd.DataFrame({
            'Metric': ['Average Processing Time', 'Accuracy Rate', 'Customer Satisfaction', 'ROI'],
            'Value': ['2.4 hours', '98.3%', '4.7/5.0', '340%'],
            'Change': ['+12%', '+2.1%', '+0.3', '+45%']
        })
        st.dataframe(metrics_df, use_container_width=True)

elif user_type == "💳 Pricing & Plans":
    # Pricing page
    st.markdown("""
        <div class="main-header">
            <h1>💳 Pricing & Plans</h1>
            <p>Choose the perfect plan for your needs</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["👤 Individual Plans", "🏢 Enterprise Plans", "💰 Payment Options"])
    
    with tabs[0]:
        st.markdown("### 👤 Plans for Individuals & Families")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class="info-card" style="text-align: center;">
                    <h3>Basic</h3>
                    <div style="font-size: 2.5rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">₹99</div>
                    <p style="color: #64748b;">per bill</p>
                    <hr>
                    <p>✓ Single bill audit</p>
                    <p>✓ CGHS verification</p>
                    <p>✓ Basic report</p>
                    <p>✓ Email support</p>
                    <p style="color: #cbd5e1;">✗ Priority processing</p>
                    <p style="color: #cbd5e1;">✗ EMI options</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Select Basic", key="basic", use_container_width=True)
        
        with col2:
            st.markdown("""
                <div class="info-card" style="text-align: center; border: 3px solid #3b82f6;">
                    <span class="premium-badge">POPULAR</span>
                    <h3>Premium</h3>
                    <div style="font-size: 2.5rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">₹499</div>
                    <p style="color: #64748b;">per month</p>
                    <hr>
                    <p>✓ Unlimited audits</p>
                    <p>✓ CGHS + insurer check</p>
                    <p>✓ Detailed analytics</p>
                    <p>✓ Priority support</p>
                    <p>✓ 24hr processing</p>
                    <p>✓ EMI available</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Select Premium", key="premium", use_container_width=True):
                st.session_state.show_payment = True
                st.session_state.selected_plan = "Premium - ₹499/month"
        
        with col3:
            st.markdown("""
                <div class="info-card" style="text-align: center;">
                    <h3>Family</h3>
                    <div style="font-size: 2.5rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">₹999</div>
                    <p style="color: #64748b;">per month</p>
                    <hr>
                    <p>✓ Up to 6 members</p>
                    <p>✓ Unlimited audits</p>
                    <p>✓ All Premium features</p>
                    <p>✓ Dedicated manager</p>
                    <p>✓ Instant processing</p>
                    <p>✓ Flexible EMI</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Select Family", key="family", use_container_width=True)
    
    with tabs[1]:
        st.markdown("### 🏢 Enterprise Solutions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="info-card">
                    <h3>Business</h3>
                    <div style="font-size: 2rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">₹9,999/month</div>
                    <hr>
                    <p>✓ Up to 500 bills/month</p>
                    <p>✓ API access</p>
                    <p>✓ Bulk processing</p>
                    <p>✓ Custom compliance rules</p>
                    <p>✓ Dedicated account manager</p>
                    <p>✓ Advanced analytics</p>
                    <p>✓ SLA guarantee (24hrs)</p>
                    <p>✓ Quarterly payments available</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Contact Sales", key="business", use_container_width=True)
        
        with col2:
            st.markdown("""
                <div class="info-card" style="border: 3px solid #f59e0b;">
                    <span class="premium-badge">ENTERPRISE</span>
                    <h3>Custom</h3>
                    <div style="font-size: 2rem; color: #3b82f6; font-weight: 700; margin: 1rem 0;">Let's Talk</div>
                    <hr>
                    <p>✓ Unlimited processing</p>
                    <p>✓ Full API suite</p>
                    <p>✓ White-label option</p>
                    <p>✓ Custom integrations</p>
                    <p>✓ On-premise deployment</p>
                    <p>✓ 24/7 dedicated support</p>
                    <p>✓ SLA guarantee (4hrs)</p>
                    <p>✓ Flexible payment terms</p>
                </div>
            """, unsafe_allow_html=True)
            st.button("Schedule Demo", key="enterprise", use_container_width=True)
        
        st.markdown("### 🎁 Enterprise Benefits")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Volume Discounts**\n10% off for 1000+ bills/month")
        with col2:
            st.info("**Dedicated Support**\nPersonal account manager")
        with col3:
            st.info("**Custom Training**\nFree onboarding & training")
    
    with tabs[2]:
        st.markdown("### 💰 Payment & EMI Options")
        
        if st.session_state.show_payment:
            st.success(f"✓ Selected: {st.session_state.get('selected_plan', 'Premium Plan')}")
        
        st.markdown("#### Choose Payment Method")
        
        payment_method = st.radio(
            "Payment Method",
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
            st.markdown("### 📊 EMI Calculator")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                bill_amount = st.number_input("Bill Amount (₹)", min_value=1000, max_value=1000000, value=50000, step=1000)
            
            with col2:
                emi_tenure = st.selectbox("EMI Tenure", ["3 months", "6 months", "9 months", "12 months"])
            
            with col3:
                interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=30.0, value=12.0, step=0.5)
            
            # Calculate EMI
            tenure_months = int(emi_tenure.split()[0])
            monthly_rate = interest_rate / (12 * 100)
            
            if monthly_rate > 0:
                emi = (bill_amount * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
            else:
                emi = bill_amount / tenure_months
            
            total_payment = emi * tenure_months
            total_interest = total_payment - bill_amount
            
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
                        <div class="metric-value">₹{total_payment:,.0f}</div>
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
            st.checkbox("I agree to the Terms & Conditions and Privacy Policy")
        
        with col2:
            if st.button("💳 Pay Now", use_container_width=True):
                with st.spinner("Processing payment..."):
                    import time
                    time.sleep(2)
                st.success("✅ Payment successful! Thank you for choosing MediAudit Pro.")
                st.balloons()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**MediAudit Pro**")
    st.markdown("AI-powered medical bill auditing")

with col2:
    st.markdown("**Quick Links**")
    st.markdown("• About Us")
    st.markdown("• Contact")
    st.markdown("• Privacy Policy")

with col3:
    st.markdown("**Support**")
    st.markdown("📧 support@mediaudit.com")
    st.markdown("📱 +91-8148186386")

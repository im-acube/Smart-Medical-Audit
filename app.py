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

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="logo.png", # Use logo as favicon
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced Custom CSS Block ---
st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Apply Font */
        html, body, [class*="st-"], .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* --- Color Palette --- */
        :root {
            --primary-blue: #3b82f6; /* blue-500 */
            --primary-blue-dark: #2563eb; /* blue-600 */
            --primary-sky: #0ea5e9; /* sky-500 */
            --primary-sky-light: #e0f2fe; /* sky-100 */
            --success-green: #10b981; /* emerald-500 */
            --success-green-light: #d1fae5; /* emerald-100 */
            --warning-amber: #f59e0b; /* amber-500 */
            --warning-amber-light: #fef3c7; /* amber-100 */
            --danger-red: #ef4444; /* red-500 */
            --danger-red-light: #fee2e2; /* red-100 */
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-300: #cbd5e1;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-600: #475569;
            --slate-700: #334155;
            --slate-800: #1e293b;
            --white: #ffffff;
        }

        /* --- General App Styling --- */
        .stApp {
            background-color: var(--slate-100); /* Lighter background */
        }
        h1, h2, h3, h4 {
            color: var(--slate-800); /* Darker heading color */
            font-weight: 600;
            letter-spacing: -0.02em; /* Tighter letter spacing */
        }
         h1 { font-size: 2.2rem; margin-bottom: 0.5rem; }
         h2 { font-size: 1.8rem; margin-bottom: 0.4rem; }
         h3 { font-size: 1.3rem; margin-bottom: 0.3rem; }
         h4 { font-size: 1.1rem; font-weight: 500; }

        /* --- Sidebar --- */
        [data-testid="stSidebar"] {
            background: var(--white);
            border-right: 1px solid var(--slate-200);
            box-shadow: 2px 0 10px rgba(0,0,0,0.03);
            padding-top: 1.5rem;
        }
        [data-testid="stSidebar"] h3 {
             color: var(--primary-blue-dark) !important;
             font-weight: 700;
             font-size: 1.2rem;
             margin-bottom: 0.5rem;
        }
         [data-testid="stSidebar"] [role="radiogroup"] label {
            background: var(--white);
            border: 1px solid var(--slate-200);
            transition: all 0.2s ease;
            padding: 0.7rem 1rem;
            margin-bottom: 0.4rem; /* Slightly more space */
            border-radius: 8px; /* Rounded corners */
            font-weight: 500;
            color: var(--slate-600);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: var(--primary-sky);
            background: var(--primary-sky-light);
            transform: translateX(3px);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            color: var(--primary-blue-dark);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
            background: linear-gradient(135deg, var(--primary-sky) 0%, var(--primary-blue) 100%);
            color: var(--white) !important;
            border-color: var(--primary-blue-dark);
            font-weight: 600;
            box-shadow: 0 2px 5px rgba(59, 130, 246, 0.3);
            transform: translateX(0); /* Reset hover transform */
        }
        [data-testid="stSidebar"] .stButton > button { /* Style sidebar buttons */
            border: 1px solid var(--slate-300);
            background-color: var(--white);
            color: var(--slate-600);
            font-weight: 500;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
             border-color: var(--slate-400);
             background-color: var(--slate-50);
        }


        /* --- Card Styling (Enhanced) --- */
        /* Applied via markdown, requires class="info-card" etc. in markdown */
        .info-card, .metric-card, .negotiation-card, .audit-category, .queued-bill {
            background: var(--white);
            padding: 1.75rem; /* Increased padding */
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid var(--slate-200);
            margin-bottom: 1.75rem; /* Increased spacing */
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .info-card:hover, .metric-card:hover, .negotiation-card:hover, .audit-category:hover, .queued-bill:hover {
             transform: translateY(-3px); /* Slightly more lift */
             box-shadow: 0 10px 20px rgba(0,0,0,0.07), 0 3px 6px rgba(0,0,0,0.07);
        }
        /* Style Streamlit Expander like a card */
         div[data-testid="stExpander"] {
             background: var(--white) !important;
             border-radius: 12px !important;
             box-shadow: 0 4px 12px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.05) !important;
             border: 1px solid var(--slate-200) !important;
             margin-bottom: 1.5rem !important;
             overflow: hidden; /* Ensure rounded corners apply */
         }
         div[data-testid="stExpander"] summary {
             padding: 1rem 1.5rem;
             font-weight: 600;
             font-size: 1.1rem;
             color: var(--primary-blue-dark);
         }
         div[data-testid="stExpander"] summary:hover {
             background-color: var(--slate-50) !important;
         }
         div[data-testid="stExpander"] > div:first-child + div { /* Content area */
            padding: 0 1.5rem 1.5rem 1.5rem;
            background: var(--white);
         }


        /* Metric Card Specific */
        .metric-card {
            background: var(--white); /* Simple white */
            text-align: center;
            border-left: 5px solid var(--primary-blue);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-blue-dark);
            line-height: 1.1; /* Adjusted line height */
        }
        .metric-label {
            color: var(--slate-500);
            font-size: 0.8rem; /* Slightly smaller label */
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        /* Savings Metric Card */
        .savings-metric-card {
             background: var(--warning-amber-light);
             border-left-color: var(--warning-amber);
        }
        .savings-metric-card .metric-value { color: #92400e; /* Amber-900 */ }
        .savings-metric-card .metric-label { color: #b45309; /* Amber-700 */ }


        /* Audit Categories (More subtle) */
        .audit-category {
            padding: 1rem 1.25rem;
            border-left-width: 4px;
            background: #f8fafc; /* Slate-50 */
        }
        .audit-category h4 { font-size: 1rem; margin-bottom: 0.25rem; }
        .audit-category p { font-size: 0.85rem; color: var(--slate-600); }

        .audit-category-pass { border-left-color: var(--success-green); background: var(--success-green-light); }
        .audit-category-fail { border-left-color: var(--danger-red); background: var(--danger-red-light); }
        .audit-category-fail h4 { color: #b91c1c; /* Red-800 */}
        .audit-category-pass h4 { color: #047857; /* Green-800 */}


        /* Negotiation Card */
        .negotiation-card {
            background: linear-gradient(135deg, var(--primary-sky-light) 0%, #dbeafe 100%); /* Blue-100 */
            border: 2px solid var(--primary-blue);
            color: var(--slate-700);
            padding: 2rem; /* More padding */
        }
         .negotiation-card h3 { color: var(--primary-blue-dark); font-size: 1.5rem; margin-bottom: 0.75rem; }
        .negotiation-card strong { color: var(--primary-blue-dark); }
         .negotiation-card p { margin-bottom: 0.5rem; }

        /* --- Button Styling --- */
        /* Targeting Streamlit's button structure */
        div[data-testid="stButton"] > button {
            border: none; /* Remove default border */
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            font-family: 'Inter', sans-serif; /* Ensure font */
        }
        /* Primary Button Style */
        div[data-testid="stButton"] > button:not(:disabled):not([kind="secondary"]) {
            background: linear-gradient(135deg, var(--primary-sky) 0%, var(--primary-blue) 100%);
            color: var(--white);
        }
        div[data-testid="stButton"] > button:not(:disabled):not([kind="secondary"]):hover {
             filter: brightness(1.1);
             box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
             transform: translateY(-2px); /* Lift effect */
        }
        /* Secondary Button Style */
         div[data-testid="stButton"] > button[kind="secondary"] {
            background-color: var(--white);
            border: 1px solid var(--slate-300);
            color: var(--slate-700); /* Darker text */
            font-weight: 500;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
             background-color: var(--slate-50);
             border-color: var(--slate-400);
             box-shadow: 0 1px 3px rgba(0,0,0,0.05);
             transform: translateY(-1px);
        }
         /* Disabled Button Style */
        div[data-testid="stButton"] > button:disabled {
            background-color: var(--slate-200);
            color: var(--slate-400);
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        /* --- Other Enhancements --- */
        /* Progress Bar */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, var(--primary-sky), var(--primary-blue));
            border-radius: 8px;
            height: 10px !important; /* Make it thicker */
        }
        .stProgress > div {
             border-radius: 8px;
        }
         /* Dataframe styling */
         .stDataFrame {
              border-radius: 8px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.05);
              border: 1px solid var(--slate-200);
         }
         /* Style table headers */
         .stDataFrame thead th {
             background-color: var(--slate-100);
             color: var(--slate-600);
             font-weight: 600;
             text-transform: uppercase;
             font-size: 0.8rem;
             letter-spacing: 0.05em;
         }

         /* Hero Banner (Using Placeholder) */
         .hero-banner {
             background: linear-gradient(rgba(30, 64, 175, 0.85), rgba(59, 130, 246, 0.85)), /* Adjusted gradient */
                         url('https://placehold.co/1200x400/f0f4f8/3b82f6?text=Modern+Healthcare+Tech&font=inter'); /* Placeholder */
             background-size: cover;
             background-position: center;
             padding: 4rem 2rem; /* More padding */
             border-radius: 16px; /* Larger radius */
             margin-bottom: 2.5rem; /* More space */
             box-shadow: 0 10px 25px rgba(0,0,0,0.1);
             color: var(--white);
             text-align: center;
         }
         .hero-banner img { /* Style for logo if placed inside */
             height: 50px;
             width: auto;
             margin-bottom: 1.5rem;
             filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));
         }
         .hero-banner h1 { /* Style for h1 if text is used instead of logo */
              font-size: 3rem;
              text-shadow: 1px 1px 3px rgba(0,0,0,0.4);
              color: var(--white); /* Ensure white color */
              margin-bottom: 0.5rem;
         }
         .hero-banner p {
             color: #dbeafe; /* Lighter blue for subtext */
             font-size: 1.25rem;
             margin-top: 0.5rem;
             text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
             max-width: 700px; /* Limit width */
             margin-left: auto;
             margin-right: auto;
         }
         .hero-banner p:last-child {
             font-size: 1rem;
             margin-top: 1.5rem; /* More space before last line */
             font-weight: 500;
             opacity: 0.9;
         }

        /* Strikethrough Price Styling */
        .strikethrough-price {
            text-decoration: line-through;
            color: var(--slate-400); /* Lighter gray */
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }
        .free-badge {
            background: linear-gradient(135deg, var(--success-green) 0%, #059669 100%); /* Emerald-600 */
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.3rem;
            display: inline-block;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3); /* Green shadow */
        }
        /* Premium badge for enterprise */
        .premium-badge {
             background: linear-gradient(135deg, #a855f7, #7c3aed); /* Purple */
             color: white;
             font-size: 0.7rem;
             font-weight: bold;
             padding: 2px 8px;
             border-radius: 10px;
             display: inline-block;
             margin-bottom: 0.5rem;
             letter-spacing: 0.05em;
             text-transform: uppercase;
        }

        /* WhatsApp Float - Adjusted shadow and size */
        .whatsapp-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }
        .whatsapp-button {
            background: #25D366;
            color: white;
            padding: 12px 18px; /* Slightly smaller */
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 6px 15px rgba(37, 211, 102, 0.4); /* Enhanced shadow */
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .whatsapp-button:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(37, 211, 102, 0.5);
        }

    </style>
""", unsafe_allow_html=True)
# --- End of CSS Block ---


# WhatsApp Chatbot Float Button
st.markdown("""
    <div class="whatsapp-float">
        <a href="https://wa.me/919876543210?text=Hi%20MediAudit%20Pro,%20I%20need%20help%20with%20my%20medical%20bill"
           target="_blank" class="whatsapp-button">
            💬 Chat Support
        </a>
    </div>
""", unsafe_allow_html=True)

# Helper functions (No changes needed in these)
@st.cache_data
def load_reference_data():
    # ... (keep existing function)
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({
            "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges", "CT Scan", "MRI", "X-Ray", "Surgical Gloves (Box)", "Injection Syringe (Pack of 10)"],
            "Rate (₹)": [4000, 2500, 1500, 50000, 8000, 3000, 5000, 800, 800, 500] # Added sample rates
        })
    return cghs

def normalize_text(s):
    # ... (keep existing function)
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.70):
    # ... (keep existing function)
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

def detect_overcharge_type(item_name, amount, standard_rate):
    # ... (keep existing function - can be refined further if needed)
    item_lower = item_name.lower()
    if any(word in item_lower for word in ['syringe', 'gloves', 'mask', 'cotton', 'bandage', 'gauze', 'sanitizer']):
        if amount > standard_rate * 1.5: # Lower threshold for consumables
            return "Inflated Consumables"
    return "Overcharge Detected" # Default if not consumable

def text_to_items_from_lines(lines):
    # ... (keep existing function)
    items = []
    for line in lines:
        line = line.strip()
        if not line: continue
        # Improved logic to handle cases with Rs. or ₹ symbol anywhere
        parts = line.split()
        amount_str = None
        item_parts = []
        for part in reversed(parts):
            cleaned_part = part.replace("₹", "").replace("Rs.", "").replace(",", "").strip()
            if cleaned_part.replace(".", "", 1).isdigit():
                amount_str = cleaned_part
                break
            else:
                item_parts.insert(0, part)

        if amount_str is not None:
             try:
                 amt = float(amount_str)
                 item_name = " ".join(item_parts).strip()
                 if item_name: # Ensure item name is not empty
                     items.append((item_name, amt))
             except ValueError:
                 pass # Ignore if conversion fails
        # Fallback for simple space split if the above fails (less reliable)
        elif len(parts) >= 2:
             left, right = line.rsplit(" ", 1)
             amount_token = right.replace("₹", "").replace(",", "").replace("Rs.", "").strip()
             if amount_token.replace(".", "", 1).isdigit():
                 try:
                     amt = float(amount_token)
                     items.append((left.strip(), amt))
                 except ValueError:
                     pass

    return items


def extract_text_from_pdf_bytes(pdf_bytes):
    # ... (keep existing function)
    text_accum = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1, y_tolerance=1) # Adjust tolerance
                if page_text:
                    text_accum += page_text + "\n"
    except Exception as e:
        print(f"PDF Extraction Error: {e}") # Add logging
        pass
    return text_accum

def extract_text_from_image_bytes(img_bytes):
    # ... (keep existing function)
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        # Add config for better OCR if needed, e.g., --psm 6 for assuming a single uniform block of text
        text = pytesseract.image_to_string(img, config='--psm 6')
        return text
    except Exception as e:
        print(f"Image Extraction Error: {e}") # Add logging
        return ""

# Initialize session state (No changes needed)
if 'bill_queue' not in st.session_state:
    st.session_state.bill_queue = []
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None
if 'payment_history' not in st.session_state:
    st.session_state.payment_history = []
if 'negotiation_requests' not in st.session_state:
    st.session_state.negotiation_requests = []

# Sidebar (Add logo)
with st.sidebar:
    # --- Display Logo in Sidebar ---
    st.image("logo.png", width=150) # Adjust width as needed
    # --- End Logo ---
    st.markdown("### 🏥 MediAudit Pro") # Keep text title as well
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")

    user_type = st.radio(
        "Navigation Menu", # Changed label
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "ℹ️ About & Pricing"],
        key="user_type_selector"
    )

    st.markdown("---")

    if user_type == "👤 Patient Portal":
        st.markdown("### 📊 Your Portal Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Audits", str(len(st.session_state.payment_history) + len(st.session_state.bill_queue)))
        with col2:
            st.metric("Bills In Queue", str(len(st.session_state.bill_queue)))

        if st.session_state.bill_queue:
            st.markdown("---")
            total_queue = sum([b.get('total_billed', 0) for b in st.session_state.bill_queue]) # Use .get for safety
            st.info(f"**Queue Total Amount**\n## ₹{total_queue:,.0f}")

    st.markdown("---")
    st.markdown("### 💬 Quick Help")
    # Using markdown for button look to control link opening
    st.link_button("📱 WhatsApp Support", "https://wa.me/919876543210", use_container_width=True)
    st.markdown("📧 support@mediaudit.com")

# Main content
if user_type == "🏠 Home":
    # --- Use Logo in Hero Banner ---
    st.markdown("""
        <div class="hero-banner">
             <img src="https://placehold.co/200x60/FFFFFF/3b82f6?text=MediAudit+Pro&font=inter" alt="MediAudit Logo" style="height: 50px; width: auto; margin-bottom: 1.5rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));">
             {/* Removed H1 text, logo serves as title */}
             <p>AI-Powered Medical Bill Auditing - Detect Overcharges & Save Money</p>
             <p>✓ Free Audits | ✓ Expert Negotiation | ✓ WhatsApp Support</p>
        </div>
    """, unsafe_allow_html=True)
    # --- End Hero Banner ---

    st.markdown("### 🎯 What We Audit For")
    st.markdown("Our AI meticulously checks every line item for common overcharging patterns.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <span style="font-size: 2.5rem;">💊</span>
                <h4 style="margin-top: 0.5rem;">Inflated Consumables</h4>
                <p style="font-size: 0.85rem; color: var(--slate-600);">Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                 <span style="font-size: 2.5rem;">🔄</span>
                 <h4 style="margin-top: 0.5rem;">Duplicate Billing</h4>
                <p style="font-size: 0.85rem; color: var(--slate-600);">Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                 <span style="font-size: 2.5rem;">📈</span>
                 <h4 style="margin-top: 0.5rem;">Upcoding</h4>
                <p style="font-size: 0.85rem; color: var(--slate-600);">Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                 <span style="font-size: 2.5rem;">📦</span>
                 <h4 style="margin-top: 0.5rem;">Unbundling</h4>
                <p style="font-size: 0.85rem; color: var(--slate-600);">Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### 💼 Our Services")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class="info-card">
                <h3><span style="font-size: 1.5rem; margin-right: 0.5rem;">🔬</span> FREE Bill Audit</h3>
                <ul style="list-style-type: '✓ '; padding-left: 1.5rem; color: var(--slate-600); margin-top: 1rem; space-y: 0.5rem;">
                    <li>AI-powered error detection</li>
                    <li>Checks all 4 overcharge types</li>
                    <li>Detailed audit report</li>
                    <li>CGHS / Market rate comparison</li>
                    <li>Instant results online</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="negotiation-card">
                <h3><span style="font-size: 1.5rem; margin-right: 0.5rem;">🤝</span> Expert Negotiation</h3>
                 <ul style="list-style-type: '✓ '; padding-left: 1.5rem; color: var(--slate-700); margin-top: 1rem; space-y: 0.5rem;">
                     <li>We negotiate directly with hospitals</li>
                     <li>Get overcharges reduced/removed</li>
                     <li>Dedicated case manager</li>
                     <li><strong style="color: #92400e;">Pay only 15% commission on *actual* savings</strong></li>
                 </ul>
                 <p style="font-size: 0.9rem; margin-top: 1rem; background: var(--white); padding: 0.5rem; border-radius: 6px; border: 1px solid var(--primary-blue);">
                    Example: We save you ₹10,000 → You pay us only ₹1,500
                 </p>
            </div>
        """, unsafe_allow_html=True)

elif user_type == "👤 Patient Portal":
    # --- Use Logo in Hero Banner ---
    st.markdown("""
        <div class="hero-banner">
             <img src="https://placehold.co/200x60/FFFFFF/3b82f6?text=MediAudit+Pro&font=inter" alt="MediAudit Logo" style="height: 50px; width: auto; margin-bottom: 1.5rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));">
            {/* Removed H1 text */}
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    # --- End Hero Banner ---

    tabs = st.tabs(["📤 New Bill Audit", "🗂️ Bill Queue & Payment", "🤝 Negotiation Requests", "📋 History"])

    with tabs[0]:
        st.markdown("### 👤 Patient Information")
        # Use columns for better layout on wider screens
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name")
            hospital_list = ["Select hospital", "AIIMS Delhi", "Apollo Hospital", "Fortis Hospital",
                           "Medanta", "Manipal Hospital", "Narayana Health", "Max Hospital", "Other"]
            hospital = st.selectbox("Hospital", hospital_list)
            if hospital == "Other":
                hospital = st.text_input("Enter Hospital Name")
            contact_number = st.text_input("Contact Number", placeholder="+91-XXXXXXXXXX")

        with col_info2:
            patient_id = st.text_input("Patient ID (Optional)", placeholder="From hospital records")
            admission_date = st.date_input("Admission Date", value=datetime.now() - timedelta(days=7))
            email = st.text_input("Email Address", placeholder="your.email@example.com")

        st.markdown("---")
        st.markdown("### 📁 Upload Medical Bill")
        st.caption("Please upload the **detailed, itemized** bill, not just the summary.")

        col_upload1, col_upload2 = st.columns([3, 1]) # Give more space to uploader

        with col_upload1:
            uploaded = st.file_uploader(
                "Upload Bill (PDF, JPG, PNG, Excel, CSV)",
                type=["pdf", "jpg", "jpeg", "png", "xlsx", "csv"],
                label_visibility="collapsed" # Use markdown title instead
            )

        with col_upload2:
            st.markdown("""
                <div class="info-card !p-4 !mb-0" style="background-color: var(--primary-sky-light); border-color: var(--primary-sky);">
                    <h4 style="color: var(--primary-blue-dark); font-size: 0.9rem; margin-bottom: 0.3rem;">We Check For:</h4>
                    <ul style="font-size: 0.8rem; color: var(--slate-600); list-style-type: '✓ '; padding-left: 1rem; space-y: 0.2rem;">
                        <li>Inflated Items</li>
                        <li>Duplicates</li>
                        <li>Upcoding</li>
                        <li>Unbundling</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)


        manual_extract = st.checkbox("📝 Enter items manually instead of uploading")

        # --- Audit Logic Section ---
        # Initialize variables
        df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
        extracted_text_display = ""
        extraction_successful = False

        if manual_extract:
            txt_manual = st.text_area("Paste bill text here (each item on a new line, amount at the end)", height=200)
            if txt_manual:
                with st.spinner("Parsing pasted text..."):
                    lines_manual = txt_manual.splitlines()
                    items_manual = text_to_items_from_lines(lines_manual)
                    if items_manual:
                        df_items = pd.DataFrame(items_manual, columns=["Item", "Amount (₹)"])
                        extraction_successful = True
                    else:
                        st.warning("Could not parse items. Ensure amount is at the end of each line.")

        elif uploaded:
            ext = uploaded.name.split(".")[-1].lower()
            with st.spinner(f"🔄 Reading {ext.upper()} file and extracting items..."):
                try:
                    bytes_data = uploaded.read()
                    if ext in ("csv", "xlsx"):
                        df_read = pd.read_csv(BytesIO(bytes_data)) if ext == "csv" else pd.read_excel(BytesIO(bytes_data))
                        col_map = {}
                        item_col, amount_col = None, None
                        for c in df_read.columns:
                            lc = str(c).strip().lower() # Ensure string conversion
                            if ("item" in lc or "service" in lc or "description" in lc or "particular" in lc) and not item_col:
                                item_col = c
                            if ("amount" in lc or "cost" in lc or "price" in lc or "rate" in lc or "₹" in str(c)) and not amount_col:
                                amount_col = c
                        if item_col and amount_col:
                            df_items = df_read[[item_col, amount_col]].rename(columns={item_col: "Item", amount_col: "Amount (₹)"})
                            # Clean amount column
                            df_items["Amount (₹)"] = pd.to_numeric(df_items["Amount (₹)"].astype(str).str.replace(r'[₹,Rs.\s]', '', regex=True), errors='coerce')
                            df_items = df_items.dropna(subset=["Item", "Amount (₹)"])
                            df_items = df_items[df_items["Amount (₹)"] > 0] # Remove zero/negative amounts
                            extraction_successful = not df_items.empty
                        else:
                             st.warning("Could not automatically identify 'Item' and 'Amount' columns. Trying text extraction...")
                             # Fallback to text extraction if columns not found
                             txt_fallback = extract_text_from_pdf_bytes(bytes_data) if ext == 'pdf' else "" # Add other text extractions if needed
                             if txt_fallback:
                                 items_fallback = text_to_items_from_lines(txt_fallback.splitlines())
                                 if items_fallback:
                                      df_items = pd.DataFrame(items_fallback, columns=["Item", "Amount (₹)"])
                                      extraction_successful = True
                                 else:
                                     extracted_text_display = txt_fallback # Show raw text if parsing fails


                    elif ext in ("jpg", "jpeg", "png"):
                        txt_img = extract_text_from_image_bytes(bytes_data)
                        if txt_img:
                            items_img = text_to_items_from_lines(txt_img.splitlines())
                            if items_img:
                                df_items = pd.DataFrame(items_img, columns=["Item", "Amount (₹)"])
                                extraction_successful = True
                            else:
                                extracted_text_display = txt_img # Show raw text if parsing fails
                        else:
                            st.error("Could not extract text from image. Please ensure good quality image or try manual entry.")

                    elif ext == "pdf":
                        txt_pdf = extract_text_from_pdf_bytes(bytes_data)
                        if txt_pdf:
                            items_pdf = text_to_items_from_lines(txt_pdf.splitlines())
                            if items_pdf:
                                df_items = pd.DataFrame(items_pdf, columns=["Item", "Amount (₹)"])
                                extraction_successful = True
                            else:
                                extracted_text_display = txt_pdf # Show raw text if parsing fails
                        else:
                             st.error("Could not extract text from PDF. The PDF might be image-based or protected. Try manual entry or image upload.")

                except Exception as e:
                    st.error(f"An error occurred during file processing: {e}")
                    print(f"File Processing Error: {e}") # Log error

            if not extraction_successful and extracted_text_display:
                 st.warning("Automatic item extraction failed. Displaying raw text. Please use manual entry or edit below.")
                 st.text_area("Extracted Text (for reference)", extracted_text_display, height=150, disabled=True)
                 # Provide empty editor if extraction failed but text was found
                 if df_items.empty:
                    df_items = pd.DataFrame([["", ""], ["", ""]], columns=["Item", "Amount (₹)"])


        # --- Display Editor and Audit Button ---
        if extraction_successful or manual_extract or (uploaded and extracted_text_display): # Show editor if upload attempted or manual mode active
            st.markdown("### 📋 Verify Extracted Items")
            st.caption("Please review and correct the items and amounts below before running the audit.")
            # Ensure Amount column is numeric for editing, handle potential errors
            try:
                df_items["Amount (₹)"] = pd.to_numeric(df_items["Amount (₹)"], errors='coerce').fillna(0).round(2)
            except Exception:
                 st.warning("Could not format Amount column automatically, please check values.")
                 pass # Keep original if conversion fails

            edited_df = st.data_editor(
                df_items,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Item": st.column_config.TextColumn("Service / Item Description", required=True),
                    "Amount (₹)": st.column_config.NumberColumn("Billed Amount (₹)", required=True, min_value=0, format="%.2f"),
                },
                key="data_editor"
            )

            col_audit_btn1, col_audit_btn2 = st.columns(2)
            with col_audit_btn1:
                 run_audit = st.button("🚀 Run FREE Audit", use_container_width=True, type="primary", disabled=(edited_df.empty or not patient_name or not hospital or hospital=="Select hospital"))
            if not patient_name or not hospital or hospital=="Select hospital":
                 st.warning("Please fill in Patient Name and select a Hospital to enable the audit.")


            # --- Audit Execution and Results Display ---
            if run_audit:
                # Filter out empty rows from edited_df
                valid_items_df = edited_df.dropna(subset=['Item', 'Amount (₹)'])
                valid_items_df = valid_items_df[valid_items_df['Item'].astype(str).str.strip() != '']
                valid_items_df = valid_items_df[pd.to_numeric(valid_items_df['Amount (₹)'], errors='coerce') > 0]


                if valid_items_df.empty:
                    st.error("No valid items found in the table. Please add or correct items and amounts.")
                else:
                    with st.spinner("🔍 Auditing Your Bill... (AI analysis in progress)"):
                        # --- Audit Logic ---
                        cghs_df = load_reference_data()
                        cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
                        cghs_services = list(cghs_df["service_norm"].dropna().unique())

                        results = []
                        alerts = []
                        overcharge_types = { "Inflated Consumables": 0, "Duplicate Billing": 0, "Upcoding": 0, "Unbundling": 0, "Other Overcharge": 0 }
                        item_counts = {} # For duplicate detection
                        total_billed = 0.0
                        total_standard = 0.0
                        potential_savings = 0.0

                        for idx, r in valid_items_df.iterrows():
                            item_raw = r.get("Item", "")
                            item = normalize_text(item_raw)
                            if not item: continue

                            try:
                                amount = float(str(r.get("Amount (₹)", 0)).replace(",", "").replace("₹", "").strip())
                            except: amount = 0.0
                            if amount <= 0: continue # Skip zero/negative amounts post-edit

                            total_billed += amount
                            status = "Normal ✓" # Default status
                            overcharge_type = ""
                            comment = ""
                            standard_rate = amount # Default standard rate is billed amount

                            # --- Duplicate Check ---
                            item_counts[item] = item_counts.get(item, 0) + 1
                            if item_counts[item] > 1:
                                status = "Overcharged ⚠️"
                                overcharge_type = "Duplicate Billing"
                                overcharge_types["Duplicate Billing"] += 1
                                # Assume standard rate is 0 for duplicates after the first
                                standard_rate = 0
                                potential_savings += amount
                                comment = f"Duplicate item found! (Save ₹{amount:,.2f})"
                                alerts.append(f"🔄 {item_raw}: Duplicate Billing - Save ₹{amount:,.2f}")
                            else:
                                # --- Rate Check (Only if not duplicate) ---
                                matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                                if matched:
                                    row_ref = cghs_df[cghs_df["service_norm"] == matched].iloc[0]
                                    rate = float(row_ref["Rate (₹)"])
                                    standard_rate = rate # Set standard rate from reference

                                    if amount > rate * 1.15: # 15% tolerance
                                        status = "Overcharged ⚠️"
                                        savings = amount - rate
                                        potential_savings += savings

                                        # Determine overcharge type
                                        detected_type = detect_overcharge_type(item, amount, rate)
                                        if detected_type == "Inflated Consumables":
                                            overcharge_type = "Inflated Consumables"
                                            overcharge_types["Inflated Consumables"] += 1
                                        elif amount > rate * 2: # Simple upcoding heuristic
                                             overcharge_type = "Upcoding"
                                             overcharge_types["Upcoding"] += 1
                                        else:
                                             overcharge_type = "Other Overcharge"
                                             overcharge_types["Other Overcharge"] += 1

                                        comment = f"Billed ₹{amount:,.2f} vs Standard ₹{rate:,.2f} (Potential Save ₹{savings:,.2f})"
                                        alerts.append(f"❗ {item_raw}: {overcharge_type} - Save ₹{savings:,.2f}")
                                    else:
                                        status = "Fair Price ✓"
                                        comment = f"Billed ₹{amount:,.2f} vs Standard ₹{rate:,.2f}"
                                else:
                                    status = "Unlisted ?"
                                    comment = "Rate not in reference data"
                                    standard_rate = amount # Use billed if unlisted

                            # Accumulate standard total
                            total_standard += standard_rate


                            results.append({
                                "Service": item_raw,
                                "Billed (₹)": amount,
                                "Standard (₹)": standard_rate if status != "Duplicate Billing" else 'N/A', # Show N/A for duplicates
                                "Status": status,
                                "Type": overcharge_type,
                                "Comments": comment
                            })
                        # --- End Audit Logic ---

                        results_df = pd.DataFrame(results)
                        flagged_count = len([r for r in results if 'Overcharged' in r['Status']])
                        audit_score = max(0, 100 - int((potential_savings / total_billed) * 100) if total_billed > 0 else 100) # Score based on % savings

                        # Store audit in session state
                        st.session_state.current_audit = {
                            'patient_name': patient_name, 'hospital': hospital, 'contact': contact_number, 'email': email,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'results_df': results_df,
                            'total_billed': total_billed, 'total_standard': total_standard, 'potential_savings': potential_savings,
                            'audit_score': audit_score, 'flagged_count': flagged_count, 'alerts': alerts,
                            'overcharge_types': overcharge_types, 'original_input': edited_df # Store edited df
                        }

                        st.success("✅ Audit Complete!")
                        st.balloons()
                        st.markdown("---")

                        # --- Display Results ---
                        st.markdown("### 📊 Audit Summary")
                        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                        with col_res1: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(results_df)}</div><div class="metric-label">Items Checked</div></div>', unsafe_allow_html=True)
                        with col_res2: st.markdown(f'<div class="metric-card"><div class="metric-value">{flagged_count}</div><div class="metric-label">Issues Found</div></div>', unsafe_allow_html=True)
                        with col_res3: st.markdown(f'<div class="metric-card"><div class="metric-value">{audit_score}</div><div class="metric-label">Audit Score (/100)</div></div>', unsafe_allow_html=True)
                        with col_res4: st.markdown(f'<div class="metric-card savings-metric-card"><div class="metric-value">₹{potential_savings:,.0f}</div><div class="metric-label">Potential Savings</div></div>', unsafe_allow_html=True)

                        st.markdown("### 🔍 Overcharge Analysis by Type")
                        col_type1, col_type2, col_type3, col_type4 = st.columns(4)
                        types_data = st.session_state.current_audit['overcharge_types']
                        with col_type1:
                            status_class = "audit-category-pass" if types_data["Inflated Consumables"] == 0 else "audit-category-fail"
                            st.markdown(f'<div class="audit-category {status_class}"><h4>💊 Inflated Consumables</h4><p>Found: {types_data["Inflated Consumables"]}</p></div>', unsafe_allow_html=True)
                        with col_type2:
                            status_class = "audit-category-pass" if types_data["Duplicate Billing"] == 0 else "audit-category-fail"
                            st.markdown(f'<div class="audit-category {status_class}"><h4>🔄 Duplicate Billing</h4><p>Found: {types_data["Duplicate Billing"]}</p></div>', unsafe_allow_html=True)
                        with col_type3:
                            status_class = "audit-category-pass" if types_data["Upcoding"] == 0 else "audit-category-fail"
                            st.markdown(f'<div class="audit-category {status_class}"><h4>📈 Upcoding</h4><p>Found: {types_data["Upcoding"]}</p></div>', unsafe_allow_html=True)
                        with col_type4:
                            # Combining Unbundling and Other for simplicity unless data exists
                            other_issues = types_data.get("Unbundling", 0) + types_data.get("Other Overcharge", 0)
                            status_class = "audit-category-pass" if other_issues == 0 else "audit-category-fail"
                            st.markdown(f'<div class="audit-category {status_class}"><h4>❓ Other/Unbundling</h4><p>Found: {other_issues}</p></div>', unsafe_allow_html=True)

                        st.markdown("### 🧾 Detailed Audit Results")
                        def style_results(df):
                            def highlight_row(row):
                                if 'Overcharged' in row["Status"]: return ['background-color: var(--danger-red-light)'] * len(row)
                                elif 'Unlisted' in row["Status"]: return ['background-color: var(--primary-sky-light)'] * len(row)
                                else: return ['background-color: var(--success-green-light)'] * len(row)
                            return df.style.apply(highlight_row, axis=1).format({
                                "Billed (₹)": "₹{:,.2f}",
                                "Standard (₹)": lambda x: f"₹{x:,.2f}" if isinstance(x, (int, float)) else x # Format only if numeric
                            })

                        st.dataframe(style_results(results_df[['Service', 'Billed (₹)', 'Standard (₹)', 'Status', 'Type', 'Comments']]), use_container_width=True, height=min(35 * (len(results_df) + 1), 400)) # Dynamic height

                        if alerts:
                            st.markdown("### ⚠️ Key Issues Identified")
                            for alert in alerts: st.warning(alert)

                        # Negotiation Offer
                        if potential_savings > 100: # Lower threshold
                            st.markdown("---")
                            st.markdown(f"""
                                <div class="negotiation-card">
                                    <h3>🤝 Want Us To Negotiate Savings For You?</h3>
                                    <p>We found potential savings of **₹{potential_savings:,.2f}**!</p>
                                    <p>Our experts can negotiate with {hospital if hospital != 'Other' else 'the hospital'} on your behalf.</p>
                                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                                        Pay only 15% commission on actual savings achieved.
                                    </p>
                                    <p style="font-size: 0.9rem;">Example: If we save you ₹{potential_savings:,.0f} → Your fee is only ₹{potential_savings*0.15:,.2f}</p>
                                </div>
                            """, unsafe_allow_html=True)

                            col_neg1, col_neg2 = st.columns(2)
                            with col_neg1:
                                if st.button("✅ Yes, Request Negotiation!", use_container_width=True, type="primary"):
                                    negotiation_request = {
                                        'id': f"NEG{datetime.now().strftime('%Y%m%d%H%M%S%f')}", # Added microseconds for uniqueness
                                        'patient_name': patient_name, 'hospital': hospital, 'contact': contact_number, 'email': email,
                                        'potential_savings': potential_savings, 'commission_estimate': potential_savings * 0.15,
                                        'status': 'Pending', 'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        'audit_data': st.session_state.current_audit # Store the full audit context
                                    }
                                    st.session_state.negotiation_requests.append(negotiation_request)
                                    st.success("✅ Negotiation request submitted! Our team will contact you within 24 business hours.")
                                    st.info("Check the 'Negotiation Requests' tab for status updates.")
                                    # Clear current audit to prevent resubmission
                                    st.session_state.current_audit = None
                                    time.sleep(1.5)
                                    st.rerun() # Rerun to clear form and update tabs

                            with col_neg2:
                                if st.button("No Thanks", use_container_width=True, type="secondary"):
                                    st.info("Okay! You can still add this bill to your queue or download the report.")

                        # Action buttons
                        st.markdown("---")
                        st.markdown("### 💾 Next Steps for This Audit")
                        col_act1, col_act2, col_act3 = st.columns(3)
                        with col_act1:
                            if st.button("➕ Add to Bill Queue", use_container_width=True):
                                if st.session_state.current_audit:
                                    st.session_state.bill_queue.append(st.session_state.current_audit)
                                    st.success(f"✓ Added! {len(st.session_state.bill_queue)} bill(s) in queue.")
                                    st.session_state.current_audit = None # Clear after adding
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("Audit data not found. Please run audit again.")

                        with col_act2:
                            # Button disabled for now, add payment logic later if needed here
                             st.button("💰 Pay (Via Queue)", disabled=True, use_container_width=True)
                             st.caption("Add to queue first")


                        with col_act3:
                             # Logic to create a downloadable report (e.g., CSV or TXT)
                             try:
                                 report_csv = results_df.to_csv(index=False).encode('utf-8')
                                 st.download_button(
                                     label="📥 Download Audit Report (CSV)",
                                     data=report_csv,
                                     file_name=f"MediAudit_Report_{patient_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                                     mime='text/csv',
                                     use_container_width=True
                                 )
                             except Exception as e:
                                 st.error(f"Failed to generate report: {e}")

        # Demo Option (Keep existing, but use the enhanced styling implicitly)
        st.markdown("---")
        st.markdown("### 🎭 Demo Mode")
        st.info("Don't have a bill? Try our demo to see how the audit works!")
        if st.button("🚀 Run Demo Bill Audit", use_container_width=True, type="secondary"):
            # --- Demo Logic (Keep existing, styles will apply automatically) ---
            # ... (rest of your demo logic remains the same) ...
            # Create dummy bill
            demo_bill = pd.DataFrame({
                'Item': [
                    'Room Rent (General Ward)', 'Doctor Consultation', 'Blood Test - CBC',
                    'Surgical Gloves (Box)', 'CT Scan - Head', 'Injection Syringe (Pack of 10)',
                    'ICU Charges (Per Day)', 'X-Ray - Chest'
                ],
                'Amount (₹)': [8500, 3000, 2000, 4500, 6000, 2500, 12000, 1200]
            })
            demo_patient_name = "Demo Patient"
            demo_hospital = "Apollo Hospital"
            demo_contact = "+91-9876543210"
            demo_email = "demo@mediaudit.com"

            with st.spinner("🔍 Running Demo Audit..."): time.sleep(2) # Simulate delay

            # Perform Demo Audit
            cghs_df = load_reference_data() # Ensure reference data is loaded
            cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
            cghs_services = list(cghs_df["service_norm"].dropna().unique())

            # Static Demo Results (Aligned with helper data)
            demo_results = [
                 {"Service": "Room Rent (General Ward)", "Billed (₹)": 8500, "Standard (₹)": 4000.0, "Status": "Overcharged ⚠️", "Type": "Upcoding", "Comments": "Billed ₹8,500.00 vs Standard ₹4,000.00 (Potential Save ₹4,500.00)"},
                 {"Service": "Doctor Consultation", "Billed (₹)": 3000, "Standard (₹)": 2500.0, "Status": "Fair Price ✓", "Type": "", "Comments": "Billed ₹3,000.00 vs Standard ₹2,500.00"},
                 {"Service": "Blood Test - CBC", "Billed (₹)": 2000, "Standard (₹)": 1500.0, "Status": "Fair Price ✓", "Type": "", "Comments": "Billed ₹2,000.00 vs Standard ₹1,500.00"},
                 {"Service": "Surgical Gloves (Box)", "Billed (₹)": 4500, "Standard (₹)": 800.0, "Status": "Overcharged ⚠️", "Type": "Inflated Consumables", "Comments": "Billed ₹4,500.00 vs Standard ₹800.00 (Potential Save ₹3,700.00)"},
                 {"Service": "CT Scan - Head", "Billed (₹)": 6000, "Standard (₹)": 3000.0, "Status": "Overcharged ⚠️", "Type": "Other Overcharge", "Comments": "Billed ₹6,000.00 vs Standard ₹3,000.00 (Potential Save ₹3,000.00)"},
                 {"Service": "Injection Syringe (Pack of 10)", "Billed (₹)": 2500, "Standard (₹)": 500.0, "Status": "Overcharged ⚠️", "Type": "Inflated Consumables", "Comments": "Billed ₹2,500.00 vs Standard ₹500.00 (Potential Save ₹2,000.00)"},
                 {"Service": "ICU Charges (Per Day)", "Billed (₹)": 12000, "Standard (₹)": 8000.0, "Status": "Fair Price ✓", "Type": "", "Comments": "Billed ₹12,000.00 vs Standard ₹8,000.00"},
                 {"Service": "X-Ray - Chest", "Billed (₹)": 1200, "Standard (₹)": 800.0, "Status": "Fair Price ✓", "Type": "", "Comments": "Billed ₹1,200.00 vs Standard ₹800.00"}
            ]

            results_df = pd.DataFrame(demo_results)
            total_billed = results_df['Billed (₹)'].sum()
            potential_savings = sum(r['Billed (₹)'] - r['Standard (₹)'] for r in demo_results if 'Overcharged' in r['Status'])
            total_standard = total_billed - potential_savings
            flagged_count = len([r for r in demo_results if 'Overcharged' in r['Status']])
            audit_score = 60 # Example score
            alerts = [
                 "❗ Room Rent (General Ward): Upcoding - Save ₹4,500.00",
                 "❗ Surgical Gloves (Box): Inflated Consumables - Save ₹3,700.00",
                 "❗ CT Scan - Head: Other Overcharge - Save ₹3,000.00",
                 "❗ Injection Syringe (Pack of 10): Inflated Consumables - Save ₹2,000.00"
            ]
            overcharge_types = { "Inflated Consumables": 2, "Duplicate Billing": 0, "Upcoding": 1, "Unbundling": 0, "Other Overcharge": 1 }


            # Store demo audit
            st.session_state.current_audit = {
                'patient_name': demo_patient_name, 'hospital': demo_hospital, 'contact': demo_contact, 'email': demo_email,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'results_df': results_df,
                'total_billed': total_billed, 'total_standard': total_standard, 'potential_savings': potential_savings,
                'audit_score': audit_score, 'flagged_count': flagged_count, 'alerts': alerts,
                'overcharge_types': overcharge_types, 'is_demo': True, 'original_input': demo_bill # Store original demo input
            }

            st.success("✅ Demo Audit Complete!")
            st.markdown("---")

            # Demo Results Display (same structure as real results)
            st.markdown("### 📊 Demo Audit Summary")
            col_dres1, col_dres2, col_dres3, col_dres4 = st.columns(4)
            with col_dres1: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(results_df)}</div><div class="metric-label">Items Checked</div></div>', unsafe_allow_html=True)
            with col_dres2: st.markdown(f'<div class="metric-card"><div class="metric-value">{flagged_count}</div><div class="metric-label">Issues Found</div></div>', unsafe_allow_html=True)
            with col_dres3: st.markdown(f'<div class="metric-card"><div class="metric-value">{audit_score}</div><div class="metric-label">Audit Score (/100)</div></div>', unsafe_allow_html=True)
            with col_dres4: st.markdown(f'<div class="metric-card savings-metric-card"><div class="metric-value">₹{potential_savings:,.0f}</div><div class="metric-label">Potential Savings</div></div>', unsafe_allow_html=True)

            st.markdown("### 🔍 Demo Overcharge Analysis by Type")
            col_dtype1, col_dtype2, col_dtype3, col_dtype4 = st.columns(4)
            types_data = st.session_state.current_audit['overcharge_types']
            with col_dtype1:
                status_class = "audit-category-pass" if types_data["Inflated Consumables"] == 0 else "audit-category-fail"
                st.markdown(f'<div class="audit-category {status_class}"><h4>💊 Inflated Consumables</h4><p>Found: {types_data["Inflated Consumables"]}</p></div>', unsafe_allow_html=True)
            with col_dtype2:
                status_class = "audit-category-pass" if types_data["Duplicate Billing"] == 0 else "audit-category-fail"
                st.markdown(f'<div class="audit-category {status_class}"><h4>🔄 Duplicate Billing</h4><p>Found: {types_data["Duplicate Billing"]}</p></div>', unsafe_allow_html=True)
            with col_dtype3:
                status_class = "audit-category-pass" if types_data["Upcoding"] == 0 else "audit-category-fail"
                st.markdown(f'<div class="audit-category {status_class}"><h4>📈 Upcoding</h4><p>Found: {types_data["Upcoding"]}</p></div>', unsafe_allow_html=True)
            with col_dtype4:
                other_issues = types_data.get("Unbundling", 0) + types_data.get("Other Overcharge", 0)
                status_class = "audit-category-pass" if other_issues == 0 else "audit-category-fail"
                st.markdown(f'<div class="audit-category {status_class}"><h4>❓ Other/Unbundling</h4><p>Found: {other_issues}</p></div>', unsafe_allow_html=True)

            st.markdown("### 🧾 Detailed Demo Results")
            st.dataframe(style_results(results_df[['Service', 'Billed (₹)', 'Standard (₹)', 'Status', 'Type', 'Comments']]), use_container_width=True, height=min(35 * (len(results_df) + 1), 400))

            if alerts:
                st.markdown("### ⚠️ Key Issues Identified (Demo)")
                for alert in alerts: st.warning(alert)

            # Demo Negotiation Offer
            st.markdown("---")
            st.markdown(f"""
                <div class="negotiation-card">
                    <h3>🤝 Demo: Our Negotiation Service</h3>
                    <p>In this demo, we found potential savings of **₹{potential_savings:,.2f}**.</p>
                    <p>Our experts would negotiate with the hospital on your behalf.</p>
                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">Pay only 15% commission on actual savings.</p>
                    <p style="font-size: 0.9rem;">Example: If we save you ₹{potential_savings:,.0f} → Your fee: ₹{potential_savings*0.15:,.2f}</p>
                    <p style="margin-top: 1rem; padding: 0.75rem; background: var(--white); border-radius: 8px; border: 1px solid var(--primary-blue);">
                        <strong>This is a demo.</strong> Upload a real bill to use our actual negotiation service!
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Demo Action buttons
            st.markdown("### 💾 Demo Actions")
            col_dact1, col_dact2, col_dact3 = st.columns(3)
            with col_dact1:
                if st.button("➕ Add Demo to Queue", key="add_demo_queue", use_container_width=True):
                    if st.session_state.current_audit and st.session_state.current_audit.get('is_demo'):
                        st.session_state.bill_queue.append(st.session_state.current_audit)
                        st.success(f"✓ Demo added! {len(st.session_state.bill_queue)} bill(s) in queue.")
                        st.session_state.current_audit = None
                        time.sleep(1)
                        st.rerun()
                    else: st.warning("No demo audit data found.")
            with col_dact2:
                 st.button("💰 Try Payment (Demo)", disabled=True, use_container_width=True)
                 st.caption("Add to queue first")
            with col_dact3:
                 try:
                     report_csv = results_df.to_csv(index=False).encode('utf-8')
                     st.download_button(
                         label="📥 Download Demo Report (CSV)",
                         data=report_csv,
                         file_name=f"MediAudit_Demo_Report_{datetime.now().strftime('%Y%m%d')}.csv",
                         mime='text/csv',
                         use_container_width=True,
                         key="download_demo"
                     )
                 except Exception as e: st.error(f"Failed to generate demo report: {e}")
            st.session_state.current_audit = None # Clear demo audit after showing results/actions


    # --- Bill Queue & Payment Tab ---
    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        if not st.session_state.bill_queue:
            st.info("Your bill queue is empty. Audit a bill using the 'New Bill Audit' tab and click 'Add to Bill Queue' to manage payments here.")
        else:
            total_queue_billed = sum([b.get('total_billed', 0) for b in st.session_state.bill_queue])
            total_queue_savings = sum([b.get('potential_savings', 0) for b in st.session_state.bill_queue])

            st.markdown(f"""
                <div class="info-card" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-color: var(--primary-sky);">
                    <h3>📋 {len(st.session_state.bill_queue)} Bill(s) in Queue</h3>
                    <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
                        <div><strong style="color: var(--primary-blue-dark); font-size: 1.5rem;">₹{total_queue_billed:,.0f}</strong><br><span style="font-size: 0.8rem; color: var(--slate-500);">Total Billed</span></div>
                        <div><strong style="color: var(--warning-amber); font-size: 1.5rem;">₹{total_queue_savings:,.0f}</strong><br><span style="font-size: 0.8rem; color: var(--slate-500);">Total Potential Savings</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Display queued bills with enhanced styling
            for idx, bill in enumerate(st.session_state.bill_queue):
                is_demo = bill.get('is_demo', False)
                demo_badge = " <span style='background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;'>DEMO</span>" if is_demo else ""
                expander_title = f"Bill #{idx+1}{demo_badge}: **{bill.get('patient_name', 'N/A')}** @ {bill.get('hospital', 'N/A')} (Billed: ₹{bill.get('total_billed', 0):,.0f} | Savings: ₹{bill.get('potential_savings', 0):,.0f})"

                with st.expander(expander_title):
                    col_q1, col_q2, col_q3 = st.columns(3)
                    with col_q1:
                        st.caption(f"Audit Date: {bill.get('date', 'N/A')}")
                        st.write(f"**Hospital:** {bill.get('hospital', 'N/A')}")
                    with col_q2:
                        st.write(f"**Audit Score:** {bill.get('audit_score', 'N/A')}/100")
                        st.write(f"**Issues Found:** {bill.get('flagged_count', 'N/A')}")
                    with col_q3:
                        st.write(f"**Total Billed:** ₹{bill.get('total_billed', 0):,.2f}")
                        st.write(f"**Potential Savings:** ₹{bill.get('potential_savings', 0):,.2f}")

                    st.markdown("###### Audit Details")
                    # Display styled dataframe
                    st.dataframe(style_results(bill.get('results_df', pd.DataFrame())), use_container_width=True)

                    if bill.get('alerts'):
                         st.markdown("###### Key Issues")
                         for alert in bill['alerts']: st.warning(alert)


                    # Action buttons within expander
                    st.markdown("---")
                    col_act_q1, col_act_q2 = st.columns([1,1]) # Use 2 columns for buttons
                    with col_act_q1:
                        # Allow payment button only for non-demo bills
                        pay_disabled = is_demo
                        pay_tooltip = "Demo bills cannot be paid." if is_demo else "Pay this bill individually."
                        if st.button(f"💰 Pay Bill #{idx+1} (₹{bill.get('total_billed', 0):,.0f})", key=f"pay_{idx}", use_container_width=True, disabled=pay_disabled, help=pay_tooltip):
                            st.session_state.payment_bills = [bill]
                            st.session_state.show_payment = True
                            st.rerun()

                    with col_act_q2:
                        if st.button(f"🗑️ Remove Bill #{idx+1}", key=f"remove_{idx}", use_container_width=True, type="secondary"):
                            st.session_state.bill_queue.pop(idx)
                            st.success("Bill removed from queue.")
                            time.sleep(1)
                            st.rerun()

            st.markdown("---")

            # Consolidated Actions
            col_pall1, col_pall2 = st.columns(2)
            non_demo_bills = [b for b in st.session_state.bill_queue if not b.get('is_demo', False)]
            with col_pall1:
                pay_all_disabled = not non_demo_bills
                pay_all_tooltip = "No payable (non-demo) bills in queue." if pay_all_disabled else "Pay all non-demo bills together."
                if st.button(f"💳 Pay All {len(non_demo_bills)} Bills (₹{sum([b.get('total_billed',0) for b in non_demo_bills]):,.0f})", use_container_width=True, type="primary", disabled=pay_all_disabled, help=pay_all_tooltip):
                    st.session_state.payment_bills = non_demo_bills
                    st.session_state.show_payment = True
                    st.rerun()

            with col_pall2:
                if st.button("🗑️ Clear Entire Queue", use_container_width=True, type="secondary"):
                    st.session_state.bill_queue = []
                    st.success("Queue cleared.")
                    time.sleep(1)
                    st.rerun()

        # --- Payment Section Logic (Keep existing, styles will apply automatically) ---
        if st.session_state.get('show_payment', False):
            st.markdown("---")
            st.markdown("## 💳 Complete Your Payment")
            # ... (Rest of your existing payment logic remains the same) ...
            # ... It will inherit the new button styles, card styles etc. ...

            payment_bills = st.session_state.get('payment_bills', [])
            total_payment = sum([bill.get('total_billed', 0) for bill in payment_bills])

            st.markdown(f"""
            <div class="info-card" style="background: var(--success-green-light); border-color: var(--success-green);">
                 <h3 style="color: #047857;">💰 Total Payment Amount: ₹{total_payment:,.2f}</h3>
                 <p style="color: var(--slate-600);">You are paying for {len(payment_bills)} bill(s).</p>
            </div>
            """, unsafe_allow_html=True)

            payment_method = st.radio(
                "Select Payment Method",
                ["💳 Credit/Debit Card", "🏦 Net Banking", "📱 UPI", "💼 EMI Options"],
                horizontal=True, key="payment_method_select"
            )

            # ... (keep existing logic for each payment method) ...
            if payment_method == "💳 Credit/Debit Card":
                 st.markdown("###### Enter Card Details")
                 col1, col2 = st.columns(2)
                 with col1:
                     st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX", key="card_num")
                     st.text_input("Cardholder Name", placeholder="Name as on Card", key="card_name")
                 with col2:
                     col_a, col_b = st.columns(2)
                     with col_a: st.text_input("Expiry (MM/YY)", placeholder="MM/YY", key="card_exp")
                     with col_b: st.text_input("CVV", placeholder="XXX", type="password", key="card_cvv")
                 st.checkbox("Save card securely for future payments", key="save_card")

            elif payment_method == "🏦 Net Banking":
                 st.markdown("###### Select Your Bank")
                 st.selectbox("Select Bank", [
                     "State Bank of India", "HDFC Bank", "ICICI Bank",
                     "Axis Bank", "Kotak Mahindra Bank", "Punjab National Bank", "Other..."
                 ], key="netbanking_bank")
                 st.info("You will be redirected to your bank's secure payment portal.")

            elif payment_method == "📱 UPI":
                 st.markdown("###### Enter UPI ID or Scan QR")
                 upi_id = st.text_input("Enter your UPI ID", placeholder="yourname@bank", key="upi_id")
                 # In a real app, you might generate a QR code here
                 st.info("📱 A payment request will be sent to your UPI app.")
                 # Display logos using markdown for better control
                 st.markdown("""
                     <div style="display: flex; gap: 20px; margin-top: 1rem; opacity: 0.8;">
                         <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Google_Pay_Logo_%282020%29.svg/150px-Google_Pay_Logo_%282020%29.svg.png" height="30">
                         <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/PhonePe_Logo.svg/150px-PhonePe_Logo.svg.png" height="30">
                         <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Paytm_Logo_%28standalone%29.svg/120px-Paytm_Logo_%28standalone%29.svg.png" height="25">
                     </div>
                 """, unsafe_allow_html=True)


            elif payment_method == "💼 EMI Options":
                 st.markdown("### 📊 EMI Calculator - Convert Bill to Monthly Payments")
                 st.info("💡 Convert your medical bill into easy monthly installments. Select tenure and check options.")

                 col1, col2, col3 = st.columns(3)
                 with col1:
                     bill_amount_emi = st.number_input("Bill Amount (₹)", value=float(total_payment), disabled=True, key="emi_amount")
                     st.caption("From selected bills")
                 with col2:
                     emi_tenure = st.selectbox("Select EMI Tenure", ["3 months", "6 months", "9 months", "12 months", "18 months", "24 months"], index=1, key="emi_tenure") # Default 6 months
                 with col3:
                     interest_rate = st.number_input("Interest Rate (% p.a.)", min_value=0.0, max_value=24.0, value=14.0, step=0.5, key="emi_rate") # Example rate
                     st.caption("Approx. rate, varies by partner")

                 # Calculate EMI (same logic as before)
                 tenure_months = int(emi_tenure.split()[0])
                 monthly_rate = interest_rate / (12 * 100)
                 if monthly_rate > 0: emi_amount = (bill_amount_emi * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
                 else: emi_amount = bill_amount_emi / tenure_months if tenure_months > 0 else 0
                 total_payment_emi = emi_amount * tenure_months
                 total_interest = total_payment_emi - bill_amount_emi

                 st.markdown("#### Your EMI Breakdown")
                 col_emi1, col_emi2, col_emi3 = st.columns(3)
                 with col_emi1: st.markdown(f'<div class="metric-card !py-4"><div class="metric-value !text-2xl">₹{emi_amount:,.0f}</div><div class="metric-label">Monthly EMI</div></div>', unsafe_allow_html=True)
                 with col_emi2: st.markdown(f'<div class="metric-card !py-4"><div class="metric-value !text-2xl">{tenure_months}</div><div class="metric-label">Months</div></div>', unsafe_allow_html=True)
                 with col_emi3: st.markdown(f'<div class="metric-card !py-4"><div class="metric-value !text-2xl">₹{total_interest:,.0f}</div><div class="metric-label">Total Interest</div></div>', unsafe_allow_html=True)

                 # EMI Schedule (keep existing logic)
                 # ... schedule calculation ...
                 schedule_data = []
                 remaining_principal = bill_amount_emi
                 for month in range(1, tenure_months + 1):
                     interest_component = remaining_principal * monthly_rate
                     principal_component = emi_amount - interest_component
                     remaining_principal -= principal_component
                     schedule_data.append({
                         'Month': month,
                         'EMI (₹)': f"{emi_amount:,.2f}",
                         'Principal (₹)': f"{principal_component:,.2f}",
                         'Interest (₹)': f"{interest_component:,.2f}",
                         'Balance (₹)': f"{max(0, remaining_principal):,.2f}"
                     })
                 schedule_df = pd.DataFrame(schedule_data)
                 with st.expander("📅 View Month-by-Month Payment Schedule"):
                      st.dataframe(schedule_df, use_container_width=True, height=300)

                 # EMI Partners (keep existing logic)
                 st.markdown("#### Available EMI Partners")
                 # ... partner markdown columns ...
                 col_p1, col_p2, col_p3 = st.columns(3)
                 with col_p1: st.markdown('<div class="info-card !p-4"><h4>💳 Bajaj Finserv</h4><p style="font-size: 0.8rem;">✓ 0% options*<br/>✓ Instant approval*</p></div>', unsafe_allow_html=True)
                 with col_p2: st.markdown('<div class="info-card !p-4"><h4>🏦 HDFC/ICICI/Axis..</h4><p style="font-size: 0.8rem;">✓ 3-24 months<br/>✓ Bank rates apply</p></div>', unsafe_allow_html=True)
                 with col_p3: st.markdown('<div class="info-card !p-4"><h4>💳 Credit Card EMI</h4><p style="font-size: 0.8rem;">✓ Convert existing cards<br/>✓ Check eligibility</p></div>', unsafe_allow_html=True)


                 st.markdown("###### Select EMI Provider")
                 emi_provider = st.radio("Choose partner", ["Bajaj Finserv", "HDFC Bank", "ICICI Bank", "Axis Bank", "My Credit Card"], horizontal=True, key="emi_provider")
                 st.success(f"✓ Selected: {emi_provider} | Monthly EMI approx. ₹{emi_amount:,.0f}")

            # Final payment button
            st.markdown("---")
            col_pay1, col_pay2 = st.columns([3, 1])
            with col_pay1:
                agree = st.checkbox("I agree to the Terms & Conditions and authorize this payment of ₹" + f"{total_payment:,.2f}", key="agree_pay")
            with col_pay2:
                if st.button("🔒 Complete Payment", use_container_width=True, type="primary", disabled=not agree, key="final_pay_btn"):
                    with st.spinner("Processing secure payment..."): time.sleep(2.5) # Simulate processing

                    # Add to payment history (existing logic)
                    for bill in payment_bills:
                        payment_record = bill.copy()
                        payment_record['payment_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        payment_record['payment_method'] = payment_method
                        payment_record['payment_status'] = 'Completed ✅'
                        if payment_method == "💼 EMI Options":
                            payment_record['emi_tenure'] = emi_tenure
                            payment_record['monthly_emi'] = emi_amount
                        st.session_state.payment_history.append(payment_record)

                    # Remove from queue (existing logic)
                    st.session_state.bill_queue = [b for b in st.session_state.bill_queue if b not in payment_bills]
                    st.session_state.show_payment = False

                    st.success("✅ Payment Successful!")
                    st.balloons()
                    st.info("📧 Payment confirmation sent to your email.")
                    time.sleep(2)
                    st.rerun()

    # --- Negotiation Requests Tab ---
    with tabs[2]:
        st.markdown("### 🤝 Negotiation Requests Status")
        if not st.session_state.negotiation_requests:
            st.info("You haven't requested any negotiations yet. After auditing a bill with potential savings, click 'Request Negotiation' to start the process.")
        else:
            st.markdown(f"""
                <div class="negotiation-card !py-4">
                    <h3>🤝 Your Active & Past Requests ({len(st.session_state.negotiation_requests)})</h3>
                    <p>Our expert team manages these communications for you.</p>
                </div>
            """, unsafe_allow_html=True)

            for idx, req in enumerate(st.session_state.negotiation_requests):
                status_color = {'Pending': '🟡', 'In Progress': '🔵', 'Completed': '🟢', 'Closed': '⚫', 'Failed': '🔴'}
                status_icon = status_color.get(req.get('status', '⚪'), '⚪')
                expander_title_neg = f"{status_icon} Request **#{req.get('id', 'N/A')[-6:]}** ({req.get('date', 'N/A')}) - {req.get('hospital', 'N/A')} - Status: **{req.get('status', 'N/A')}**"

                with st.expander(expander_title_neg):
                    col_neg_d1, col_neg_d2 = st.columns(2)
                    audit_data = req.get('audit_data', {}) # Get nested audit data
                    with col_neg_d1:
                         st.write(f"**Patient:** {req.get('patient_name', 'N/A')}")
                         st.write(f"**Hospital:** {req.get('hospital', 'N/A')}")
                         st.write(f"**Contact:** {req.get('contact', 'N/A')}")
                    with col_neg_d2:
                        st.write(f"**Potential Savings:** ₹{req.get('potential_savings', 0):,.2f}")
                        st.write(f"**Est. Commission:** ₹{req.get('commission_estimate', 0):,.2f}")
                        st.write(f"**Status:** {req.get('status', 'N/A')}")

                    st.markdown("###### Original Audit Summary")
                    col_neg_s1, col_neg_s2, col_neg_s3 = st.columns(3)
                    with col_neg_s1: st.metric("Billed", f"₹{audit_data.get('total_billed', 0):,.0f}")
                    with col_neg_s2: st.metric("Issues", f"{audit_data.get('flagged_count', 0)}")
                    with col_neg_s3: st.metric("Potential Savings", f"₹{audit_data.get('potential_savings', 0):,.0f}")

                    # Status Updates Timeline (Simulated)
                    st.markdown("###### Status Updates")
                    if req.get('status') == 'Pending':
                        st.info("📞 Request Received. Our team will verify details and contact you within 24 business hours to confirm strategy.")
                    elif req.get('status') == 'In Progress':
                        st.warning("⏳ Negotiation Active. Our experts are communicating with the hospital. We'll update you on progress.")
                        # Simulate a timeline
                        st.write(f"_{req.get('date')}_: Request Initiated")
                        st.write(f"_{(datetime.strptime(req.get('date'), '%Y-%m-%d %H:%M') + timedelta(days=1)).strftime('%Y-%m-%d')}_: Case assigned to negotiator")
                        st.write(f"_{(datetime.strptime(req.get('date'), '%Y-%m-%d %H:%M') + timedelta(days=2)).strftime('%Y-%m-%d')}_: Initial contact with hospital made")
                    elif req.get('status') == 'Completed':
                        actual_savings_neg = req.get('actual_savings', req.get('potential_savings', 0) * 0.85) # Simulate actual savings
                        final_commission_neg = actual_savings_neg * 0.15
                        st.success(f"✅ Negotiation Successful! Actual Savings Achieved: **₹{actual_savings_neg:,.2f}**. Your final commission is ₹{final_commission_neg:,.2f}.")
                        st.info("You will receive the revised bill and payment instructions shortly.")
                    elif req.get('status') == 'Failed':
                         st.error(f"❌ Negotiation Unsuccessful. Despite our efforts, the hospital did not agree to a reduction. Reason: {req.get('reason', 'Not specified')}. No commission charged.")
                    elif req.get('status') == 'Closed':
                         st.markdown("⚫ Request Closed.")


                    # Action Buttons (Simulated state changes for demo)
                    st.markdown("---")
                    col_neg_act1, col_neg_act2 = st.columns(2)
                    with col_neg_act1:
                         # Simulate moving to next stage
                         if req.get('status') == 'Pending':
                              if st.button("Simulate: Start Progress", key=f"progress_{idx}", use_container_width=True, type="secondary"):
                                   st.session_state.negotiation_requests[idx]['status'] = 'In Progress'
                                   st.rerun()
                         elif req.get('status') == 'In Progress':
                              if st.button("Simulate: Mark Completed (Success)", key=f"complete_{idx}", use_container_width=True, type="secondary"):
                                   st.session_state.negotiation_requests[idx]['status'] = 'Completed'
                                   st.session_state.negotiation_requests[idx]['actual_savings'] = req.get('potential_savings', 0) * 0.85 # Simulate 85% success
                                   st.rerun()
                              if st.button("Simulate: Mark Completed (Failed)", key=f"fail_{idx}", use_container_width=True, type="secondary"):
                                    st.session_state.negotiation_requests[idx]['status'] = 'Failed'
                                    st.session_state.negotiation_requests[idx]['reason'] = 'Hospital refused adjustment'
                                    st.rerun()

                    with col_neg_act2:
                         if req.get('status') in ['Pending', 'In Progress']:
                              if st.button(f"❌ Withdraw Request #{idx+1}", key=f"cancel_neg_{idx}", use_container_width=True, type="secondary"):
                                   st.session_state.negotiation_requests[idx]['status'] = 'Closed' # Mark as closed instead of removing
                                   st.warning("Negotiation request withdrawn.")
                                   time.sleep(1)
                                   st.rerun()

    # --- History Tab ---
    with tabs[3]:
        st.markdown("### 📋 Payment & Audit History")
        if not st.session_state.payment_history:
            st.info("You haven't completed any payments yet. Paid bills will appear here.")
            # Show sample history if none exists
            st.markdown("#### Sample History Preview")
            sample_history_df = pd.DataFrame({
                 'Date': [(datetime.now() - timedelta(days=d)).strftime('%Y-%m-%d %H:%M') for d in [5, 10, 15]],
                 'Patient': ['Amit Kumar', 'Priya Sharma', 'Demo Patient'],
                 'Hospital': ['Apollo Hospital', 'Fortis Hospital', 'AIIMS Delhi'],
                 'Amount Paid (₹)': [45000, 32000, 78000],
                 'Savings Found (₹)': [5400, 2800, 8900],
                 'Method': ['UPI', 'Credit Card', 'Net Banking'],
                 'Status': ['Completed ✅', 'Completed ✅', 'Completed ✅']
             })
            st.dataframe(sample_history_df.style.format({"Amount Paid (₹)": "₹{:,.0f}", "Savings Found (₹)": "₹{:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            history_data = []
            for record in sorted(st.session_state.payment_history, key=lambda x: x['payment_date'], reverse=True): # Sort by date
                history_data.append({
                    'Date': record.get('payment_date', 'N/A'),
                    'Patient': record.get('patient_name', 'N/A'),
                    'Hospital': record.get('hospital', 'N/A'),
                    'Amount Paid (₹)': record.get('total_billed', 0),
                    'Savings Found (₹)': record.get('potential_savings', 0),
                    'Method': record.get('payment_method', 'N/A'),
                    'Status': record.get('payment_status', 'N/A')
                })
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df.style.format({"Amount Paid (₹)": "₹{:,.0f}", "Savings Found (₹)": "₹{:,.0f}"}), use_container_width=True, hide_index=True)

            # Summary stats for history
            st.markdown("#### Lifetime Summary")
            col_h1, col_h2, col_h3 = st.columns(3)
            total_paid_hist = sum(r.get('total_billed', 0) for r in st.session_state.payment_history)
            total_saved_hist = sum(r.get('potential_savings', 0) for r in st.session_state.payment_history)
            total_audits_hist = len(st.session_state.payment_history)
            with col_h1: st.metric("Total Amount Paid", f"₹{total_paid_hist:,.0f}")
            with col_h2: st.metric("Total Savings Identified", f"₹{total_saved_hist:,.0f}")
            with col_h3: st.metric("Total Bills Processed", f"{total_audits_hist}")


# --- B2B Enterprise Section ---
elif user_type == "🏢 B2B Enterprise":
    # --- Use Logo in Hero Banner ---
    st.markdown("""
        <div class="hero-banner">
             <img src="https://placehold.co/200x60/FFFFFF/3b82f6?text=MediAudit+Pro&font=inter" alt="MediAudit Logo" style="height: 50px; width: auto; margin-bottom: 1.5rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));">
            <p>Bulk Bill Processing & Advanced Analytics for Healthcare Organizations</p>
        </div>
    """, unsafe_allow_html=True)
    # --- End Hero Banner ---

    tabs = st.tabs(["📊 Dashboard", "📤 Bulk Upload & Processing", "⚙️ Configuration & Settings"])

    with tabs[0]:
        st.markdown("### 📊 Enterprise Performance Dashboard")
        st.caption(f"Data as of {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

        # Key Metrics Row
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: st.markdown('<div class="metric-card"><div class="metric-value">1,247</div><div class="metric-label">Bills Processed (MTD)</div></div>', unsafe_allow_html=True)
        with col_m2: st.markdown('<div class="metric-card savings-metric-card"><div class="metric-value">₹12.4L</div><div class="metric-label">Savings Generated (MTD)</div></div>', unsafe_allow_html=True)
        with col_m3: st.markdown('<div class="metric-card"><div class="metric-value">94.2%</div><div class="metric-label">Claim Accuracy Rate</div></div>', unsafe_allow_html=True)
        with col_m4: st.markdown('<div class="metric-card"><div class="metric-value">~2.4hrs</div><div class="metric-label">Avg. Audit Turnaround</div></div>', unsafe_allow_html=True)

        st.markdown("### 📈 Recent Trends")
        col_c1, col_c2 = st.columns(2)

        with col_c1:
             st.markdown("###### Daily Processing Volume")
             # Sample data for line chart
             trend_data = pd.DataFrame({
                 'Date': pd.to_datetime([(datetime.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]),
                 'Bills Audited': [45, 52, 48, 61, 55, 58, 63],
                 'Savings (₹k)': [55, 68, 62, 75, 70, 72, 80]
             })
             fig_line = go.Figure()
             fig_line.add_trace(go.Scatter(x=trend_data['Date'], y=trend_data['Bills Audited'], mode='lines+markers', name='Bills Audited', line=dict(color='var(--primary-blue)', width=2)))
             # Add secondary y-axis for savings
             fig_line.add_trace(go.Scatter(x=trend_data['Date'], y=trend_data['Savings (₹k)'], mode='lines+markers', name='Savings (₹k)', yaxis='y2', line=dict(color='var(--warning-amber)', width=2, dash='dot')))

             fig_line.update_layout(
                 yaxis_title='Bills Audited',
                 yaxis2=dict(title='Savings (₹k)', overlaying='y', side='right'),
                 margin=dict(l=20, r=20, t=30, b=20), height=350, font_family='Inter', legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
             )
             st.plotly_chart(fig_line, use_container_width=True)

        with col_c2:
            st.markdown("###### Overcharge Types Detected (MTD)")
            # Sample data for pie chart
            category_data = pd.DataFrame({
                'Type': ['Inflated Consumables', 'Upcoding', 'Duplicate Billing', 'Unbundling', 'Other'],
                'Count': [234, 156, 89, 67, 45]
            })
            fig_pie = px.pie(category_data, values='Count', names='Type',
                           color_discrete_sequence=px.colors.qualitative.Pastel) # Use a softer color scheme
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350, font_family='Inter', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

    with tabs[1]:
        st.markdown("### 📤 Bulk Bill Upload & Processing")
        st.info("Upload an Excel (.xlsx) or CSV (.csv) file containing multiple bill records for batch auditing.")

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            bulk_file = st.file_uploader(
                "Upload Batch File",
                type=["xlsx", "csv"],
                label_visibility="collapsed"
            )
            st.markdown("""
                <div class="info-card !p-4">
                    <h4 style="font-size: 0.9rem; margin-bottom: 0.3rem;">📋 Required Columns (Example):</h4>
                    <ul style="font-size: 0.8rem; color: var(--slate-600); list-style-type: '• '; padding-left: 1rem; space-y: 0.2rem;">
                       <li>PatientID</li>
                       <li>PatientName</li>
                       <li>HospitalName</li>
                       <li>AdmissionDate</li>
                       <li>ItemDescription</li>
                       <li>BilledAmount</li>
                       <li>Optional: ItemCode, Department</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with col_b2:
            st.markdown("""
                <div class="info-card !p-4" style="background-color: var(--primary-sky-light); border-color: var(--primary-sky);">
                     <h4 style="color: var(--primary-blue-dark); font-size: 0.9rem; margin-bottom: 0.3rem;">Features:</h4>
                     <ul style="font-size: 0.8rem; color: var(--slate-600); list-style-type: '✓ '; padding-left: 1rem; space-y: 0.2rem;">
                         <li>Up to 1000 bills/batch</li>
                         <li>Auto data validation</li>
                         <li>Real-time status updates</li>
                         <li>Downloadable results</li>
                     </ul>
                 </div>
            """, unsafe_allow_html=True)
            if st.button("📥 Download Template File", use_container_width=True, type="secondary"):
                # In a real app, provide the template file
                st.success("✓ Template downloading...")

        if bulk_file:
            st.success(f"✅ File Ready: **{bulk_file.name}**. Click below to start processing.")
            if st.button("🚀 Process Batch File", use_container_width=True, type="primary"):
                with st.spinner("Processing batch file... This may take a few minutes."):
                    # Simulate batch processing
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    total_rows = 150 # Simulate rows
                    for i in range(total_rows):
                        time.sleep(0.03) # Simulate processing time per row
                        percent_complete = int(((i + 1) / total_rows) * 100)
                        progress_bar.progress(percent_complete)
                        progress_text.text(f"Processing row {i+1} of {total_rows}... ({percent_complete}%)")
                st.success(f"✅ Batch Processing Complete! {total_rows} records processed.")
                st.info("Detailed results are available in the 'Batch History' section (coming soon).")

    with tabs[2]:
        st.markdown("### ⚙️ Configuration & Settings")
        st.caption("Manage API access, compliance rules, notifications, and team settings.")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            with st.expander("🔑 API Configuration", expanded=True):
                 api_key = st.text_input("Your API Key", type="password", value="sk_live_**********", help="Use this key for programmatic access.")
                 st.button("🔄 Regenerate API Key", type="secondary")
                 webhook_url = st.text_input("Results Webhook URL", placeholder="https://your-system.com/api/mediaudit-callback")
                 st.caption("We'll POST results here when audits are complete.")

            with st.expander("⚖️ Compliance & Audit Rules"):
                 max_variance_percent = st.slider("Allowable Price Variance (%)", 0, 100, 15, help="Flag items priced above Standard Rate + this variance.")
                 auto_flag_items = st.multiselect("Auto-flag Specific Item Keywords", ['admin fee', 'registration charge', 'service charge', 'file charge'], default=['admin fee', 'file charge'])
                 st.checkbox("Enable duplicate check across patient history (beta)", value=False)

        with col_s2:
            with st.expander("🔔 Notification Settings", expanded=True):
                 alert_email = st.text_input("Alert Email Address", placeholder="billing-alerts@yourcompany.com")
                 st.checkbox("Send daily summary reports", value=True)
                 st.checkbox("Alert on high-value savings (> ₹50,000)", value=True)
                 slack_webhook = st.text_input("Slack Webhook URL (Optional)", placeholder="https://hooks.slack.com/services/...")

            with st.expander("👥 Team Management"):
                 st.write(f"Current Team Size: **5 Users**")
                 st.button("Invite New User", type="secondary")
                 st.dataframe(pd.DataFrame({ # Sample team data
                     'Name': ['Admin User', 'Auditor 1', 'Auditor 2'],
                     'Email': ['admin@yourcompany.com', 'auditor1@yourcompany.com', 'auditor2@yourcompany.com'],
                     'Role': ['Admin', 'Auditor', 'Auditor'],
                     'Status': ['Active', 'Active', 'Pending Invite']
                 }), hide_index=True, use_container_width=True)

        st.markdown("---")
        if st.button("💾 Save All Settings", use_container_width=True, type="primary"):
            st.success("✅ Enterprise settings updated successfully!")


# --- About & Pricing Section ---
elif user_type == "ℹ️ About & Pricing":
    # --- Use Logo in Hero Banner ---
    st.markdown("""
        <div class="hero-banner">
             <img src="https://placehold.co/200x60/FFFFFF/3b82f6?text=MediAudit+Pro&font=inter" alt="MediAudit Logo" style="height: 50px; width: auto; margin-bottom: 1.5rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));">
            <p>Fairness & Transparency in Healthcare Billing</p>
        </div>
    """, unsafe_allow_html=True)
    # --- End Hero Banner ---

    tabs = st.tabs(["👤 For Patients (FREE)", "🏢 For Enterprises", "❓ FAQ"])

    with tabs[0]:
        st.markdown("### 🧑‍⚕️ Patient Services: Bill Auditing is **Completely Free!**")

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
             st.markdown("""
                 <div class="info-card" style="text-align: center; border: 3px solid var(--success-green);">
                     <h2>Free Bill Auditing Service</h2>
                     <div style="margin: 1.5rem 0;">
                         <span class="strikethrough-price">₹499/audit</span>
                         <div class="free-badge">100% FREE</div>
                     </div>
                     <hr style="margin: 1.5rem 0;">
                     <div style="text-align: left; margin: 1rem 0; font-size: 0.9rem;">
                         <h4 style="font-size: 1.1rem; margin-bottom: 0.75rem;">✓ What You Get (Always Free):</h4>
                         <ul style="list-style-type: '✓ '; padding-left: 1.5rem; color: var(--slate-600); space-y: 0.5rem;">
                             <li>Unlimited AI-powered bill audits</li>
                             <li>Checks for Duplicates, Upcoding, Unbundling, Inflated Items</li>
                             <li>Reference rate comparisons (CGHS/Market)</li>
                             <li>Detailed online audit reports</li>
                             <li>Secure bill queue management</li>
                             <li>Multiple secure payment options (for final bill)</li>
                             <li>Integrated EMI calculator</li>
                             <li>WhatsApp & Email support</li>
                         </ul>
                     </div>
                 </div>
             """, unsafe_allow_html=True)
        with col_p2:
            st.success("**Our Mission: Fair Billing for All**\n\nWe believe everyone deserves transparency. Accessing fair healthcare shouldn't come at a cost.")
            st.info("**How We Sustain This?**\n\n1. Optional Negotiation Service (15% success fee).\n2. Paid Enterprise Solutions.")

        st.markdown("### 🤝 Optional Negotiation Service (Pay Only If We Save You Money!)")
        st.markdown("""
            <div class="negotiation-card">
                <h3>Expert Negotiation - Zero Risk, High Reward!</h3>
                <p style="font-size: 1.1rem; margin: 1rem 0;"><strong>How it works:</strong></p>
                <ol style="list-style-type: decimal; padding-left: 1.5rem; margin-bottom: 1rem; space-y: 0.5rem;">
                    <li>Run your FREE AI bill audit.</li>
                    <li>If overcharges are found, request our expert negotiation (optional).</li>
                    <li>Our team contacts the hospital and fights for corrections.</li>
                    <li><strong>You pay 15% commission ONLY on the actual amount saved.</strong></li>
                </ol>
                <hr style="margin: 1rem 0; border-color: var(--warning-amber);">
                <h4 style="color: #92400e;">💰 Pricing Examples (Your Fee):</h4>
                <p>• We save you ₹10,000 → You Pay ₹1,500</p>
                <p>• We save you ₹25,000 → You Pay ₹3,750</p>
                <p>• We save you ₹50,000 → You Pay ₹7,500</p>
                <p style="margin-top: 1.5rem; font-weight: 700; color: #92400e; font-size: 1.2rem; text-align: center;">
                    ⚠️ No Savings = Absolutely No Charges! ⚠️
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Bill Payment Features (Keep existing, styles will apply)
        st.markdown("### 💳 Secure Bill Payment Features")
        # ... (Keep existing 3 columns for Payment Options, Bill Queue, EMI Options) ...
        col_pay1, col_pay2, col_pay3 = st.columns(3)
        with col_pay1: st.markdown('<div class="info-card !p-4"><h4>💰 Payment Options</h4><p style="font-size:0.85rem;">✓ Cards<br/>✓ Net Banking<br/>✓ UPI<br/>✓ EMI</p></div>', unsafe_allow_html=True)
        with col_pay2: st.markdown('<div class="info-card !p-4"><h4>🗂️ Bill Queue</h4><p style="font-size:0.85rem;">✓ Manage multiple bills<br/>✓ Pay together/separately<br/>✓ Track history</p></div>', unsafe_allow_html=True)
        with col_pay3: st.markdown('<div class="info-card !p-4"><h4>📊 EMI Options</h4><p style="font-size:0.85rem;">✓ 3-24 months<br/>✓ Partner banks<br/>✓ Instant approval*</p></div>', unsafe_allow_html=True)


    with tabs[1]:
        st.markdown("### 🏢 Enterprise Solutions Pricing")
        st.caption("Tailored plans for TPAs, insurers, corporates, and hospitals.")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
             st.markdown("""
                 <div class="info-card !p-6">
                     <h3 style="color: var(--primary-blue-dark);">Business Plan</h3>
                     <div style="font-size: 2rem; color: var(--primary-blue); font-weight: 700; margin: 0.5rem 0 1rem 0;">₹9,999 / month</div>
                     <p style="font-size: 0.8rem; color: var(--slate-500); margin-bottom: 1rem;">Billed Annually</p>
                     <hr style="margin-bottom: 1rem;">
                     <ul style="list-style-type: '✓ '; padding-left: 1.5rem; color: var(--slate-600); space-y: 0.5rem; font-size: 0.9rem;">
                         <li>Up to 500 bills/month</li>
                         <li>Standard API access</li>
                         <li>Bulk CSV/Excel processing</li>
                         <li>Basic analytics dashboard</li>
                         <li>Email support (Business hours)</li>
                         <li>SLA: 24-48 hours</li>
                     </ul>
                     <div style="margin-top: 1.5rem;"></div> {/* Placeholder for button */}
                 </div>
             """, unsafe_allow_html=True)
             st.button("📧 Contact Sales", key="biz_sales", use_container_width=True, type="primary")

        with col_e2:
            st.markdown("""
                 <div class="info-card !p-6" style="border: 3px solid var(--primary-blue-dark);">
                     <span class="premium-badge">ENTERPRISE</span>
                     <h3 style="color: var(--primary-blue-dark);">Custom Plan</h3>
                     <div style="font-size: 2rem; color: var(--primary-blue); font-weight: 700; margin: 0.5rem 0 1rem 0;">Let's Talk</div>
                      <p style="font-size: 0.8rem; color: var(--slate-500); margin-bottom: 1rem;">Volume-based & Feature Needs</p>
                     <hr style="margin-bottom: 1rem;">
                     <ul style="list-style-type: '✓ '; padding-left: 1.5rem; color: var(--slate-600); space-y: 0.5rem; font-size: 0.9rem;">
                         <li>**Unlimited** bill processing</li>
                         <li>Full REST API suite</li>
                         <li>White-label / Co-branded option</li>
                         <li>Custom rule engine & integrations</li>
                         <li>Advanced analytics & reporting</li>
                         <li>Dedicated Account Manager</li>
                         <li>24/7 Priority Support</li>
                         <li>SLA: Custom (e.g., < 4 hours)</li>
                     </ul>
                     <div style="margin-top: 1.5rem;"></div> {/* Placeholder for button */}
                 </div>
             """, unsafe_allow_html=True)
            st.button("🗓️ Schedule Enterprise Demo", key="ent_demo", use_container_width=True, type="primary")

    # --- FAQ Tab ---
    with tabs[2]:
        st.markdown("### ❓ Frequently Asked Questions")
        # Keep existing FAQ expanders, styles will apply automatically
        with st.expander("🆓 Is patient bill auditing really free?"):
            st.write("Yes! 100% FREE. No hidden charges, no subscriptions. We audit unlimited bills for free for individual patients.")
        with st.expander("💰 How does the negotiation service work and cost?"):
            st.write("After our free audit identifies potential savings, you can *choose* to engage our expert negotiation service. We handle all communication with the hospital. You only pay a **15% commission** based on the *actual* savings we successfully secure for you. If we don't save you money, you pay absolutely nothing.")
        with st.expander("🔍 What types of overcharges do you look for?"):
            st.write("""
            Our AI and experts check for multiple issues, including:
            * **Inflated Consumables:** Markups on basic items like gloves, syringes, standard medicines.
            * **Duplicate Billing:** Charging twice (or more) for the same test, procedure, or item.
            * **Upcoding:** Billing for a more complex (and expensive) service than what was actually performed (e.g., billing ICU rates for a standard room).
            * **Unbundling:** Charging separately for services that should be included in a single package price (e.g., charging for standard surgical supplies separately from the surgery itself).
            * **Incorrect Codes:** Using wrong ICD/CPT codes leading to improper billing.
            * **Non-compliance:** Charges not adhering to CGHS rates or other standard benchmarks where applicable.
            """)
        with st.expander("💳 How do bill payments work through MediAudit?"):
            st.write("Once an audit is done (and potentially negotiated), you can use our secure platform to pay the final bill amount directly to the hospital (or the amount you choose if not negotiated). Add bills to the queue to pay multiple at once. We support Cards, Net Banking, UPI, and offer EMI options.")
        with st.expander("📊 What are EMI options?"):
            st.write("EMI (Equated Monthly Installment) allows you to break down your hospital bill payment into smaller, manageable monthly payments over a chosen period (e.g., 3, 6, 9, 12+ months) through our financial partners. Interest rates and eligibility apply based on the partner's terms.")
        with st.expander("💬 How does WhatsApp support work?"):
            st.write("Click the green WhatsApp icon floating at the bottom right of the screen. This will open a chat directly with our support team for quick questions and assistance regarding the app or your audit.")
        with st.expander("🏢 What do enterprise clients pay for?"):
            st.write("Our free service is for individual patients. Enterprise clients (like TPAs, Insurance Companies, Corporates offering employee benefits) subscribe to our platform for features like bulk bill processing, API integration for automation, advanced analytics dashboards, custom rule engines, white-labeling, and dedicated support.")
        with st.expander("🔒 Is my medical and financial data secure?"):
            st.write("Absolutely. Data security is our top priority. We use bank-grade encryption (AES-256) for data at rest and in transit. We adhere to strict data privacy protocols (similar to HIPAA standards) and **never** share your identifiable data without your explicit consent.")
        with st.expander("🎭 What is Demo Mode for patients?"):
            st.write("Demo Mode allows you to see exactly how the audit process works using pre-filled sample bill data. It's a great way to understand the report and features without needing to upload your own sensitive bill information immediately.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 2rem; font-size: 0.85rem; color: var(--slate-600); padding: 1rem 0;">
    <div>
        <img src="https://placehold.co/150x40/3b82f6/FFFFFF?text=MediAudit&font=inter" alt="MediAudit Logo" style="height: 30px; width: auto; margin-bottom: 0.5rem;">
        <p>AI-Powered Medical Auditing</p>
        <p style="color: var(--success-green); font-weight: 600;">Free for Patients</p>
    </div>
    <div>
        <h4 style="font-weight: 600; color: var(--slate-700); margin-bottom: 0.5rem;">Services</h4>
        <ul style="list-style: none; padding: 0; margin: 0; space-y: 0.3rem;">
            <li>Free Bill Audit</li>
            <li>Expert Negotiation</li>
            <li>Secure Payments</li>
            <li>EMI Options</li>
        </ul>
    </div>
    <div>
        <h4 style="font-weight: 600; color: var(--slate-700); margin-bottom: 0.5rem;">Quick Links</h4>
         <ul style="list-style: none; padding: 0; margin: 0; space-y: 0.3rem;">
            <li><a href="#" style="color: inherit; text-decoration: none;">About Us</a></li>
            <li><a href="#" style="color: inherit; text-decoration: none;">Privacy Policy</a></li>
            <li><a href="#" style="color: inherit; text-decoration: none;">Terms of Service</a></li>
            <li><a href="#" style="color: inherit; text-decoration: none;">FAQ</a></li>
        </ul>
    </div>
    <div>
        <h4 style="font-weight: 600; color: var(--slate-700); margin-bottom: 0.5rem;">Contact</h4>
        <ul style="list-style: none; padding: 0; margin: 0; space-y: 0.3rem;">
            <li>📧 support@mediaudit.com</li>
            <li>📱 +91-9876543210</li>
            <li>💬 WhatsApp Support</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

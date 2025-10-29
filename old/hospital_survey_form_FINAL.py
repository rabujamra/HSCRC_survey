import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Maryland HSCRC Best Practice Survey",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CUSTOM STYLING ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f4788;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1f4788;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #1f4788;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
        margin-bottom: 1.5rem;
    }
    .bp-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1f4788;
    }
    .stButton>button {
        background-color: #1f4788;
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #163a6b;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CONFIGURATION ====================

HOSPITALS = [
    "Adventist HealthCare Fort Washington Medical Center",
    "Adventist HealthCare Shady Grove Medical Center",
    "Adventist HealthCare White Oak Medical Center",
    "Anne Arundel Medical Center",
    "Atlantic General Hospital",
    "Bon Secours Hospital",
    "CalvertHealth Medical Center",
    "Carroll Hospital Center",
    "Chester River Hospital Center",
    "Christiana Care-Union Hospital",
    "Doctors Community Hospital",
    "Fort Washington Medical Center",
    "Frederick Health Hospital",
    "Garrett Regional Medical Center",
    "Greater Baltimore Medical Center",
    "Harbor Hospital",
    "Holy Cross Hospital",
    "Howard County General Hospital",
    "Johns Hopkins Bayview Medical Center",
    "Johns Hopkins Hospital",
    "Kennedy Krieger Institute",
    "Laurel Regional Hospital",
    "Levindale Hebrew Geriatric Center and Hospital",
    "MaineGeneral Medical Center",
    "Maryland General Hospital",
    "Medstar Franklin Square Medical Center",
    "Medstar Good Samaritan Hospital",
    "Medstar Harbor Hospital",
    "Medstar Montgomery Medical Center",
    "Medstar St. Mary's Hospital",
    "Medstar Union Memorial Hospital",
    "Mercy Medical Center",
    "Northwest Hospital",
    "Peninsula Regional Medical Center",
    "Saint Agnes Hospital",
    "Sinai Hospital",
    "Suburban Hospital",
    "The Johns Hopkins Hospital",
    "University of Maryland Capital Region Health",
    "University of Maryland Medical Center",
    "University of Maryland Shore Regional Health",
    "Western Maryland Regional Medical Center"
]

BEST_PRACTICES = [
    "Best Practice 1: Interdisciplinary Rounds & Early Discharge Planning",
    "Best Practice 2: Bed Capacity Alert System",
    "Best Practice 3: Standardized Daily Shift Huddles",
    "Best Practice 4: Expedited Care Intervention (Expediting team, expedited care unit)",
    "Best Practice 5: Patient Flow Throughput Performance Council",
    "Best Practice 6: Clinical Pathways & Observation Management"
]

TIERS = [
    "Tier One (Full Implementation)",
    "Tier Two (Partial Implementation)",
    "Tier Three (Planning/Early Stages)"
]

DATA_FILE = "hospital_data.csv"

# ==================== HEADER ====================
st.markdown('<div class="main-header">📋 Maryland Hospitals Best Practice Survey</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ED Throughput Best Practices - October 2025 Data Submission</div>', unsafe_allow_html=True)

st.markdown('<div class="info-box">', unsafe_allow_html=True)
st.markdown("""
**Thank you in advance for your time to complete this brief data collection.**

The purpose of this survey is to capture:
1. Which **two best practices** each hospital selected
2. The corresponding **tier** the hospital is self-reporting
3. Any **successes and/or barriers** that should be shared with the Maryland Legislature
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION A: DEMOGRAPHICS ====================
st.markdown('<div class="section-header">Section A: Demographics</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    hospital_name = st.selectbox(
        "1. Select your hospital's name from the list: *",
        options=[""] + sorted(HOSPITALS),
        help="Required field"
    )

contact_name = st.text_input(
    "2. Who is the point of contact for your hospital's ED Throughput Best Practices initiative? *",
    help="Required field"
)

contact_email = st.text_input(
    "3. What is the point of contact's email address? *",
    help="Required field"
)

st.markdown("---")

# ==================== SECTION B: BEST PRACTICES ====================
st.markdown('<div class="section-header">Section B: Best Practices Selection & Tiers</div>', unsafe_allow_html=True)

st.markdown('<div class="info-box">', unsafe_allow_html=True)
st.markdown("""
The following questions will capture each hospital's **two best practices** they chose to report on 
and the corresponding tiers they aim to self-report on in the **October 1, 2025 data submission**.
""")
st.markdown('</div>', unsafe_allow_html=True)

# First Best Practice
st.markdown("### 🎯 First Best Practice")
first_bp = st.selectbox(
    "4. Select the FIRST best practice your hospital has chosen to report on: *",
    options=[""] + BEST_PRACTICES,
    help="Required field"
)

first_bp_tier = None
first_bp_notes = ""

if first_bp:
    st.markdown('<div class="bp-card">', unsafe_allow_html=True)
    st.markdown(f"#### {first_bp}")
    
    first_bp_tier = st.radio(
        "Select the highest tier you plan to report on: *",
        options=TIERS,
        key="first_tier"
    )
    
    first_bp_notes = st.text_area(
        "Optional: Success stories or barriers?",
        height=100,
        key="first_notes"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Second Best Practice
st.markdown("### 🎯 Second Best Practice")

available_for_second = [""] + [bp for bp in BEST_PRACTICES if bp != first_bp]

second_bp = st.selectbox(
    "5. Select the SECOND best practice your hospital has chosen to report on: *",
    options=available_for_second,
    help="Must be different from first selection"
)

second_bp_tier = None
second_bp_notes = ""

if second_bp:
    st.markdown('<div class="bp-card">', unsafe_allow_html=True)
    st.markdown(f"#### {second_bp}")
    
    second_bp_tier = st.radio(
        "Select the highest tier you plan to report on: *",
        options=TIERS,
        key="second_tier"
    )
    
    second_bp_notes = st.text_area(
        "Optional: Success stories or barriers?",
        height=100,
        key="second_notes"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ==================== SUBMIT ====================
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    submit_button = st.button("📤 Submit Survey", type="primary", use_container_width=True)

if submit_button:
    errors = []
    
    if not hospital_name:
        errors.append("❌ Please select your hospital name")
    if not contact_name:
        errors.append("❌ Please enter a contact person name")
    if not contact_email:
        errors.append("❌ Please enter a contact email address")
    if not first_bp:
        errors.append("❌ Please select your first best practice")
    if first_bp and not first_bp_tier:
        errors.append("❌ Please select a tier for your first best practice")
    if not second_bp:
        errors.append("❌ Please select your second best practice")
    if second_bp and not second_bp_tier:
        errors.append("❌ Please select a tier for your second best practice")
    
    if errors:
        st.error("**Please correct the following errors:**")
        for error in errors:
            st.markdown(error)
    else:
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        
        # CLEAN 10-COLUMN FORMAT!
        data_row = {
            "Timestamp": timestamp,
            "Hospital_Name": hospital_name,
            "Contact_Name": contact_name,
            "Contact_Email": contact_email,
            "BP1_Name": first_bp,
            "BP1_Tier": first_bp_tier,
            "BP1_Notes": first_bp_notes,
            "BP2_Name": second_bp,
            "BP2_Tier": second_bp_tier,
            "BP2_Notes": second_bp_notes
        }
        
        df_new = pd.DataFrame([data_row])
        
        try:
            if os.path.exists(DATA_FILE):
                df_new.to_csv(DATA_FILE, mode='a', header=False, index=False)
            else:
                df_new.to_csv(DATA_FILE, mode='w', header=True, index=False)
            
            st.success("✅ **Survey submitted successfully!**")
            st.balloons()
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"""
            ### 🎉 Thank You, {hospital_name}!
            
            Your submission has been recorded:
            - **First Best Practice:** {first_bp} - {first_bp_tier}
            - **Second Best Practice:** {second_bp} - {second_bp_tier}
            - **Submitted on:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.download_button(
                label="📄 Download Receipt",
                data=df_new.to_csv(index=False),
                file_name=f"{hospital_name.replace(' ', '_')}_submission.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ **Error:** {str(e)}")

st.markdown("---")
st.markdown("##### Maryland Health Services Cost Review Commission (HSCRC)")
st.markdown("*ED Throughput Best Practices Initiative - October 2025*")

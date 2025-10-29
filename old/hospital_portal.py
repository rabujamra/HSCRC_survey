import streamlit as st
import pandas as pd
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Hospital Submission Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM STYLING ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f4788;
        text-align: center;
        margin-bottom: 1rem;
    }
    .hospital-name {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .bp-card {
        background: white;
        border-left: 5px solid #1f4788;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tier-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .tier-one {
        background-color: #d4edda;
        color: #155724;
    }
    .tier-two {
        background-color: #fff3cd;
        color: #856404;
    }
    .tier-three {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# ==================== AUTHENTICATION ====================
st.sidebar.title("🔐 Hospital Login")

# Hospital credentials
HOSPITAL_CREDS = {
    "Christiana Care-Union Hospital": "demo123",
    "Suburban Hospital": "demo123",
    "Adventist HealthCare White Oak Medical Center": "demo123",
    "Adventist HealthCare Fort Washington Medical Center": "demo123",
    "Atlantic General Hospital": "demo123",
    "Bon Secours Hospital": "demo123"
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.hospital = None

if not st.session_state.authenticated:
    hospital_name = st.sidebar.selectbox(
        "Hospital Name:",
        options=[""] + sorted(HOSPITAL_CREDS.keys())
    )
    password = st.sidebar.text_input("Password:", type="password")
    
    if st.sidebar.button("🔓 Login"):
        if hospital_name and hospital_name in HOSPITAL_CREDS and password == HOSPITAL_CREDS[hospital_name]:
            st.session_state.authenticated = True
            st.session_state.hospital = hospital_name
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Demo Credentials:**")
    st.sidebar.markdown("• **Hospital:** Christiana Care-Union Hospital")
    st.sidebar.markdown("• **Password:** demo123")
    st.stop()

# User is authenticated
st.sidebar.success(f"Logged in as:")
st.sidebar.info(st.session_state.hospital)

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.hospital = None
    st.rerun()

st.sidebar.markdown("---")

# ==================== DATA LOADING ====================
@st.cache_data(ttl=60)
def load_data():
    """Load data from CSV"""
    if os.path.exists('hospital_data.csv'):
        df = pd.read_csv('hospital_data.csv')
        return df
    return pd.DataFrame()

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data()

# ==================== MAIN PORTAL ====================
st.markdown('<div class="main-header">🏥 Hospital Submission Portal</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hospital-name">{st.session_state.hospital}</div>', unsafe_allow_html=True)

if df.empty:
    st.error("⚠️ No data found! Please ensure hospital_data.csv exists.")
    st.stop()

# Filter for this hospital
hospital_data = df[df['Hospital_Name'] == st.session_state.hospital]

if hospital_data.empty:
    st.warning(f"⚠️ No submissions found for {st.session_state.hospital}")
    st.info("💡 Please submit your survey using the Hospital Survey Form.")
    st.stop()

# Get latest submission
latest = hospital_data.iloc[-1]

st.markdown("---")

# ==================== SUBMISSION INFO ====================
st.markdown("## 📋 Your Latest Submission")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 👤 Contact Person")
    st.info(latest['Contact_Name'])

with col2:
    st.markdown("### ✉️ Contact Email")
    st.info(latest['Contact_Email'])

with col3:
    st.markdown("### 📅 Submission Date")
    st.info(latest['Timestamp'])

st.markdown("---")

# ==================== BEST PRACTICES ====================
st.markdown("## 📊 Your Best Practice Implementation Tiers")

# Helper function for tier badge
def get_tier_color(tier):
    if "One" in tier:
        return "tier-one"
    elif "Two" in tier:
        return "tier-two"
    else:
        return "tier-three"

# Best Practice 1
st.markdown("### 🎯 First Best Practice")
st.markdown(f"""
<div class="bp-card">
    <h4>{latest['BP1_Name']}</h4>
    <div class="tier-badge {get_tier_color(latest['BP1_Tier'])}">
        {latest['BP1_Tier']}
    </div>
    <p style="margin-top: 1rem;"><strong>Notes:</strong> {latest['BP1_Notes'] if latest['BP1_Notes'] else 'No notes provided'}</p>
</div>
""", unsafe_allow_html=True)

# Best Practice 2
st.markdown("### 🎯 Second Best Practice")
st.markdown(f"""
<div class="bp-card">
    <h4>{latest['BP2_Name']}</h4>
    <div class="tier-badge {get_tier_color(latest['BP2_Tier'])}">
        {latest['BP2_Tier']}
    </div>
    <p style="margin-top: 1rem;"><strong>Notes:</strong> {latest['BP2_Notes'] if latest['BP2_Notes'] else 'No notes provided'}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== DOWNLOAD ====================
st.markdown("## 📥 Download Your Submission")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    csv = hospital_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download Full Report (PDF)",
        data=csv,
        file_name=f"{st.session_state.hospital.replace(' ', '_')}_submission.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("---")

# ==================== SUBMISSION HISTORY ====================
if len(hospital_data) > 1:
    st.markdown("## 📜 Submission History")
    st.markdown(f"You have **{len(hospital_data)}** total submissions on record.")
    
    with st.expander("View All Submissions"):
        for idx, row in hospital_data.iterrows():
            st.markdown(f"**Submission {len(hospital_data) - list(hospital_data.index).index(idx)}** - {row['Timestamp']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**BP1:** {row['BP1_Name']}")
                st.markdown(f"*Tier:* {row['BP1_Tier']}")
            with col2:
                st.markdown(f"**BP2:** {row['BP2_Name']}")
                st.markdown(f"*Tier:* {row['BP2_Tier']}")
            st.markdown("---")

st.markdown("---")
st.markdown("##### Maryland Health Services Cost Review Commission (HSCRC)")
st.markdown("*ED Throughput Best Practices Initiative - October 2025*")

# ==================== 1. IMPORTS (FIRST) ====================
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ==================== 2. SET_PAGE_CONFIG (MUST BE HERE!) ====================
st.set_page_config(
    page_title="Hospital Submission Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 3. CONFIGURATION ====================

# Hospital credentials
HOSPITAL_CREDS = {
    "Christiana Care": "demo123",
    "Christiana Care-Union Hospital": "demo123",
    "Suburban Hospital": "demo123", 
    "Suburban": "demo123",
    "Johns Hopkins": "demo123",
    "Adventist White Oak": "demo123",
    "University of Maryland Medical Center": "demo123",
    "Mercy Medical Center": "demo123"
}

# BP Names mapping
BP_NAMES = {
    "BP1": "BP1: Interdisciplinary Rounds & Early Discharge Planning",
    "BP2": "BP2: Bed Capacity Alert System",
    "BP3": "BP3: Standardized Daily Shift Huddles",
    "BP4": "BP4: Expedited Care Intervention",
    "BP5": "BP5: Patient Flow Throughput Performance Council",
    "BP6": "BP6: Clinical Pathways & Observation Management"
}

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
    .bp-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tier-1 {border-left-color: #2ecc71 !important;}
    .tier-2 {border-left-color: #f39c12 !important;}
    .tier-3 {border-left-color: #e74c3c !important;}
    .info-card {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA FUNCTIONS ====================
@st.cache_data(ttl=60)
def load_data():
    """Load data from CSV"""
    import os
    
    if os.path.exists('hscrc_survey_submissions.csv'):
        df = pd.read_csv('hscrc_survey_submissions.csv')
        df.columns = df.columns.str.strip()
        return df
    else:
        st.error("❌ Cannot find hscrc_survey_submissions.csv")
        st.info("Please ensure the hscrc_survey_submissions.csv file is in the same directory as this app.")
        st.stop()

def generate_hospital_pdf(hospital_data):
    """Generate PDF report for a single hospital"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("Maryland HSCRC Best Practice Survey", title_style)
    subtitle = Paragraph(f"Hospital Report: {hospital_data['hospital_name']}", styles['Heading2'])
    story.extend([title, subtitle, Spacer(1, 0.3*inch)])
    
    # Hospital Info
    story.append(Paragraph("Hospital Information", heading_style))
    info_data = [
        ['Hospital:', str(hospital_data.get('hospital_name', 'N/A'))],
        ['Contact:', str(hospital_data.get('contact_name', 'N/A'))],
        ['Email:', str(hospital_data.get('email', 'N/A'))],
        ['Phone:', str(hospital_data.get('phone', 'N/A'))],
        ['Submission Date:', str(hospital_data.get('timestamp', 'N/A'))],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Best Practice 1
    if pd.notna(hospital_data.get('bp1')) and hospital_data.get('bp1') != '':
        story.append(Paragraph("Best Practice #1", heading_style))
        
        bp1_name = BP_NAMES.get(hospital_data['bp1'], hospital_data['bp1'])
        bp1_tier = hospital_data.get('bp1_tier', 'N/A')
        bp1_rationale = hospital_data.get('bp1_rationale', '')
        bp1_success = hospital_data.get('bp1_success', '')
        
        bp1_data = [
            ['Practice:', bp1_name],
            ['Tier:', f"Tier {bp1_tier}"],
        ]
        
        if bp1_rationale and str(bp1_rationale).strip() not in ('', 'None', 'nan'):
            bp1_data.append(['Rationale:', str(bp1_rationale)[:500]])
        
        if bp1_success and str(bp1_success).strip() not in ('', 'None', 'nan'):
            bp1_data.append(['Success/Barriers:', str(bp1_success)[:500]])
        
        bp1_table = Table(bp1_data, colWidths=[2*inch, 4*inch])
        bp1_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(bp1_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Best Practice 2
    if pd.notna(hospital_data.get('bp2')) and hospital_data.get('bp2') != '':
        story.append(Paragraph("Best Practice #2", heading_style))
        
        bp2_name = BP_NAMES.get(hospital_data['bp2'], hospital_data['bp2'])
        bp2_tier = hospital_data.get('bp2_tier', 'N/A')
        bp2_rationale = hospital_data.get('bp2_rationale', '')
        bp2_success = hospital_data.get('bp2_success', '')
        
        bp2_data = [
            ['Practice:', bp2_name],
            ['Tier:', f"Tier {bp2_tier}"],
        ]
        
        if bp2_rationale and str(bp2_rationale).strip() not in ('', 'None', 'nan'):
            bp2_data.append(['Rationale:', str(bp2_rationale)[:500]])
        
        if bp2_success and str(bp2_success).strip() not in ('', 'None', 'nan'):
            bp2_data.append(['Success/Barriers:', str(bp2_success)[:500]])
        
        bp2_table = Table(bp2_data, colWidths=[2*inch, 4*inch])
        bp2_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(bp2_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== LOGIN SYSTEM ====================
with st.sidebar:
    st.markdown("### 🔐 Hospital Login")
    st.markdown("---")
    
    hospital_selection = st.selectbox(
        "Select your hospital:",
        options=[""] + list(HOSPITAL_CREDS.keys())
    )
    
    password = st.text_input("Password:", type="password")
    login_button = st.button("🔓 Login", use_container_width=True)
    
    if login_button:
        if hospital_selection and password == HOSPITAL_CREDS.get(hospital_selection):
            st.session_state['logged_in'] = True
            st.session_state['hospital'] = hospital_selection
            st.success(f"✅ Welcome, {hospital_selection}!")
            st.rerun()
        else:
            st.error("❌ Invalid hospital or password")
    
    st.markdown("---")
    st.markdown("**Demo Credentials:**")
    st.markdown("- **Hospital:** Any from dropdown")
    st.markdown("- **Password:** demo123")
    
    # Logout button if logged in
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        st.markdown("---")
        st.markdown(f"**Logged in as:** {st.session_state['hospital']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ==================== CHECK LOGIN ====================
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.markdown('<div class="main-header">🏥 Hospital Submission Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Maryland HSCRC Best Practice Survey</div>', unsafe_allow_html=True)
    st.info("👈 Please login using the sidebar to view your hospital's submission")
    st.markdown("---")
    st.markdown("#### About This Portal")
    st.markdown("""
    This secure portal allows hospitals to:
    - ✅ View your Best Practice survey submission
    - ✅ Download your official PDF report
    - ✅ Review your implementation tier selections
    
    Each hospital can only access their own data. For questions, please contact HSCRC staff.
    """)
    st.stop()

# ==================== MAIN APP (AFTER LOGIN) ====================
selected_hospital = st.session_state['hospital']

# Load data
df = load_data()

# Filter to ONLY this hospital's data
hospital_data = df[df['hospital_name'] == selected_hospital]

# Header
st.markdown('<div class="main-header">🏥 Hospital Submission Portal</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{selected_hospital}</div>', unsafe_allow_html=True)
st.markdown("---")

# Check if hospital has submitted
if hospital_data.empty:
    st.warning(f"⚠️ No submission found for {selected_hospital}")
    st.info("If you believe this is an error, please contact HSCRC staff.")
    st.stop()

# Get latest submission
latest_submission = hospital_data.iloc[-1]

# Submission Info Card
st.markdown('<div class="info-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📋 Contact Person**")
    st.markdown(f"{latest_submission.get('contact_name', 'N/A')}")

with col2:
    st.markdown("**📧 Contact Email**")
    st.markdown(f"{latest_submission.get('email', 'N/A')}")

with col3:
    st.markdown("**📅 Submission Date**")
    timestamp = latest_submission.get('timestamp', 'N/A')
    if timestamp != 'N/A':
        try:
            timestamp = pd.to_datetime(timestamp).strftime('%B %d, %Y')
        except:
            pass
    st.markdown(f"{timestamp}")

st.markdown('</div>', unsafe_allow_html=True)

# PDF Download Section
col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
with col_pdf2:
    # Generate PDF on-the-fly when button is clicked
    pdf_buffer = generate_hospital_pdf(latest_submission)
    
    st.download_button(
        label="📄 Download Full Report (PDF)",
        data=pdf_buffer,
        file_name=f"{selected_hospital.replace(' ', '_')}_BestPractice_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

st.markdown("---")

# Best Practices Display
st.markdown("## 📊 Your Best Practice Implementation Tiers")
st.markdown("Review your submitted tier selections for each best practice below.")
st.markdown("")

bp_reported = False

# Display BP1
if pd.notna(latest_submission.get('bp1')) and latest_submission.get('bp1') != '':
    bp_reported = True
    bp1_code = latest_submission.get('bp1')
    bp1_name = BP_NAMES.get(bp1_code, bp1_code)
    bp1_tier = latest_submission.get('bp1_tier', '')
    bp1_rationale = latest_submission.get('bp1_rationale', '')
    bp1_success = latest_submission.get('bp1_success', '')
    
    # Tier coloring
    tier_int = int(bp1_tier) if pd.notna(bp1_tier) else 1
    tier_class = f"tier-{tier_int}"
    color = ['🟢', '🟡', '🔴'][tier_int - 1] if tier_int in [1, 2, 3] else '🔵'
    
    # Display the BP card
    st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
    st.markdown(f"### {color} First Best Practice")
    st.markdown(f"**{bp1_name}**")
    st.markdown(f"**Tier:** Tier {bp1_tier}")
    
    # Show rationale if exists
    if pd.notna(bp1_rationale) and str(bp1_rationale).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Rationale:** {bp1_rationale}")
    
    # Show success/barriers if exists
    if pd.notna(bp1_success) and str(bp1_success).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Success Stories/Barriers:** {bp1_success}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Display BP2
if pd.notna(latest_submission.get('bp2')) and latest_submission.get('bp2') != '':
    bp_reported = True
    bp2_code = latest_submission.get('bp2')
    bp2_name = BP_NAMES.get(bp2_code, bp2_code)
    bp2_tier = latest_submission.get('bp2_tier', '')
    bp2_rationale = latest_submission.get('bp2_rationale', '')
    bp2_success = latest_submission.get('bp2_success', '')
    
    # Tier coloring
    tier_int = int(bp2_tier) if pd.notna(bp2_tier) else 1
    tier_class = f"tier-{tier_int}"
    color = ['🟢', '🟡', '🔴'][tier_int - 1] if tier_int in [1, 2, 3] else '🔵'
    
    # Display the BP card
    st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
    st.markdown(f"### {color} Second Best Practice")
    st.markdown(f"**{bp2_name}**")
    st.markdown(f"**Tier:** Tier {bp2_tier}")
    
    # Show rationale if exists
    if pd.notna(bp2_rationale) and str(bp2_rationale).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Rationale:** {bp2_rationale}")
    
    # Show success/barriers if exists
    if pd.notna(bp2_success) and str(bp2_success).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Success Stories/Barriers:** {bp2_success}")
    
    st.markdown('</div>', unsafe_allow_html=True)

if not bp_reported:
    st.info("No best practices reported yet. Please complete the survey to see your tier selections here.")

st.markdown("---")

# ==================== SUBMISSION SUMMARY ====================
if bp_reported:
    st.markdown("## 📊 Submission Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📝 Quick Stats")
        st.markdown(f"- **Total Submissions:** {len(hospital_data)}")
        st.markdown(f"- **Latest Update:** {latest_submission.get('timestamp', 'N/A')}")
        st.markdown(f"- **Contact:** {latest_submission.get('contact_name', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Your Selection")
        # Count tier levels
        tier1_count = sum([1 for t in [latest_submission.get('bp1_tier'), latest_submission.get('bp2_tier')] 
                          if str(t) == '1'])
        tier2_count = sum([1 for t in [latest_submission.get('bp1_tier'), latest_submission.get('bp2_tier')] 
                          if str(t) == '2'])
        tier3_count = sum([1 for t in [latest_submission.get('bp1_tier'), latest_submission.get('bp2_tier')] 
                          if str(t) == '3'])
        
        st.markdown(f"- 🟢 **Tier 1:** {tier1_count} BP(s)")
        st.markdown(f"- 🟡 **Tier 2:** {tier2_count} BP(s)")
        st.markdown(f"- 🔴 **Tier 3:** {tier3_count} BP(s)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")

# Footer
st.markdown("##### Maryland Health Services Cost Review Commission")
st.markdown("*For questions about your submission, please contact HSCRC staff.*")

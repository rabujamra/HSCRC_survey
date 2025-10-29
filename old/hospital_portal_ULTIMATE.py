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

# Google Sheets configuration
try:
    SHEET_ID = st.secrets["hscrc"]["sheet_id"]
    GID = st.secrets["hscrc"]["gid"]
except:
    # Fallback for local dev
    SHEET_ID = "1izriK0ucWJ0gNatSvaBvxnF5JUPcCafdyhquWm1h3Jc"
    GID = "271136667"

# ==================== COLUMN MAPPING ====================
def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Google Forms headers to stable canonical names"""
    import re
    
    df = df.copy()
    
    # Map the main columns
    column_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Hospital name
        if 'hospital' in col_lower and 'name' in col_lower and 'select' in col_lower:
            column_map[col] = 'Hospital_Name'
        
        # Contact name
        elif 'point of contact' in col_lower and 'email' not in col_lower:
            column_map[col] = 'Contact_Name'
        
        # Contact email
        elif 'email' in col_lower and 'contact' in col_lower:
            column_map[col] = 'Contact_Email'
        
        # Primary BP selection
        elif 'first best practice' in col_lower or ('select' in col_lower and 'best practice' in col_lower and 'tier' not in col_lower):
            column_map[col] = 'Primary_BP'
    
    # Apply basic column mapping
    df = df.rename(columns=column_map)
    
    # Ensure timestamp column
    if 'Timestamp' not in df.columns:
        timestamp_cols = [col for col in df.columns if 'timestamp' in col.lower()]
        if timestamp_cols:
            df = df.rename(columns={timestamp_cols[0]: 'Timestamp'})
    
    # Map BP tier and notes columns
    # Pattern: "Select the highest tier you plan to report on (BP#):"
    for col in df.columns:
        # Match tier columns
        tier_match = re.search(r'tier.*\(BP(\d+)\)', col, re.IGNORECASE)
        if tier_match:
            bp_num = tier_match.group(1)
            df = df.rename(columns={col: f'BP{bp_num}_Tier'})
        
        # Match success stories/barriers columns  
        notes_match = re.search(r'(success|barriers).*\(BP(\d+)\)', col, re.IGNORECASE)
        if notes_match:
            bp_num = notes_match.group(2)
            df = df.rename(columns={col: f'BP{bp_num}_Notes'})
    
    return df

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
    .tier-one {border-left-color: #2ecc71 !important;}
    .tier-two {border-left-color: #f39c12 !important;}
    .tier-three {border-left-color: #e74c3c !important;}
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
    """Load data from Google Sheets (falls back to local CSV for development)"""
    import os
    
    # PRODUCTION: Always try Google Sheets first
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
        df = pd.read_csv(url)
    except Exception as e:
        # FALLBACK: Use local CSV for development/testing
        if os.path.exists('hospital_data.csv'):
            st.warning("⚠️ Using local CSV (Google Sheets unavailable)")
            df = pd.read_csv('hospital_data.csv')
        else:
            st.error(f"Cannot load data from Google Sheets or local CSV: {e}")
            st.stop()
    
    df.columns = df.columns.str.strip()
    df = canonicalize_columns(df)
    df = df.dropna(subset=['Hospital_Name'])
    
    return df

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
    subtitle = Paragraph(f"Hospital Report: {hospital_data['Hospital_Name']}", styles['Heading2'])
    story.extend([title, subtitle, Spacer(1, 0.3*inch)])
    
    # Hospital Info
    story.append(Paragraph("Hospital Information", heading_style))
    info_data = [
        ['Hospital:', str(hospital_data.get('Hospital_Name', 'N/A'))],
        ['Contact:', str(hospital_data.get('Contact_Name', 'N/A'))],
        ['Email:', str(hospital_data.get('Contact_Email', 'N/A'))],
        ['Submission Date:', str(hospital_data.get('Timestamp', 'N/A'))],
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
    
    # Best Practices
    story.append(Paragraph("Best Practice Implementation Tiers", heading_style))
    
    bp_data = [['Best Practice', 'Tier', 'Notes']]
    for i in range(1, 14):
        tier = hospital_data.get(f'BP{i}_Tier')
        notes = hospital_data.get(f'BP{i}_Notes', '')
        
        if pd.notna(tier) and str(tier).strip() not in ('', 'None', 'nan'):
            bp_data.append([
                f'BP {i}',
                str(tier),
                str(notes) if pd.notna(notes) and str(notes).strip() not in ('', 'None', 'nan') else 'No notes'
            ])
    
    if len(bp_data) > 1:
        bp_table = Table(bp_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        bp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(bp_table)
    else:
        story.append(Paragraph("No best practices reported yet.", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== LOGIN SYSTEM ====================
with st.sidebar:
    st.markdown("### 🔐 Hospital Login")
    st.markdown("---")
    
    hospital_name = st.text_input("Hospital Name:")
    password = st.text_input("Password:", type="password")
    login_button = st.button("🔓 Login", use_container_width=True)
    
    if login_button:
        if hospital_name in HOSPITAL_CREDS and password == HOSPITAL_CREDS[hospital_name]:
            st.session_state['logged_in'] = True
            st.session_state['hospital'] = hospital_name
            st.success(f"✅ Logged in as {hospital_name}")
            st.rerun()
        else:
            st.error("❌ Invalid hospital name or password")
    
    st.markdown("---")
    st.markdown("**Demo Credentials:**")
    st.markdown("- **Hospital:** Christiana Care-Union Hospital")
    st.markdown("- **Password:** demo123")
    
    # Logout button if logged in
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        st.markdown("---")
        st.markdown(f"**Logged in as:**  \n{st.session_state['hospital']}")
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
hospital_data = df[df['Hospital_Name'] == selected_hospital]

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
    st.markdown(f"{latest_submission.get('Contact_Name', 'N/A')}")

with col2:
    st.markdown("**📧 Contact Email**")
    st.markdown(f"{latest_submission.get('Contact_Email', 'N/A')}")

with col3:
    st.markdown("**📅 Submission Date**")
    timestamp = latest_submission.get('Timestamp', 'N/A')
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

# Display BPs from clean CSV format
bp_reported = False

# Display BP1
if 'BP1_Name' in latest_submission and pd.notna(latest_submission.get('BP1_Name')):
    bp_reported = True
    bp1_name = latest_submission.get('BP1_Name', '')
    bp1_tier = latest_submission.get('BP1_Tier', '')
    bp1_notes = latest_submission.get('BP1_Notes', '')
    
    # Detect tier level for coloring
    tier_str = str(bp1_tier).strip()
    if 'one' in tier_str.lower() or 'full' in tier_str.lower():
        tier_class = "tier-one"
        tier_normalized = "Tier One"
        color = '🟢'
        tier_desc = "Full Implementation"
    elif 'two' in tier_str.lower() or 'partial' in tier_str.lower():
        tier_class = "tier-two"
        tier_normalized = "Tier Two"
        color = '🟡'
        tier_desc = "Partial Implementation"
    else:
        tier_class = "tier-three"
        tier_normalized = "Tier Three"
        color = '🔴'
        tier_desc = "Planning/Early Stages"
    
    # Display the BP card
    st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
    st.markdown(f"### {color} First Best Practice")
    st.markdown(f"**{bp1_name}**")
    st.markdown(f"**Tier:** {tier_normalized} - *{tier_desc}*")
    
    # Show notes if they exist
    if pd.notna(bp1_notes) and str(bp1_notes).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Notes:** {bp1_notes}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Display BP2
if 'BP2_Name' in latest_submission and pd.notna(latest_submission.get('BP2_Name')):
    bp_reported = True
    bp2_name = latest_submission.get('BP2_Name', '')
    bp2_tier = latest_submission.get('BP2_Tier', '')
    bp2_notes = latest_submission.get('BP2_Notes', '')
    
    # Detect tier level for coloring
    tier_str = str(bp2_tier).strip()
    if 'one' in tier_str.lower() or 'full' in tier_str.lower():
        tier_class = "tier-one"
        tier_normalized = "Tier One"
        color = '🟢'
        tier_desc = "Full Implementation"
    elif 'two' in tier_str.lower() or 'partial' in tier_str.lower():
        tier_class = "tier-two"
        tier_normalized = "Tier Two"
        color = '🟡'
        tier_desc = "Partial Implementation"
    else:
        tier_class = "tier-three"
        tier_normalized = "Tier Three"
        color = '🔴'
        tier_desc = "Planning/Early Stages"
    
    # Display the BP card
    st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
    st.markdown(f"### {color} Second Best Practice")
    st.markdown(f"**{bp2_name}**")
    st.markdown(f"**Tier:** {tier_normalized} - *{tier_desc}*")
    
    # Show notes if they exist
    if pd.notna(bp2_notes) and str(bp2_notes).strip() not in ('', 'None', 'nan'):
        st.markdown(f"**Notes:** {bp2_notes}")
    
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
        st.markdown(f"- **Latest Update:** {latest_submission.get('Timestamp', 'N/A')}")
        st.markdown(f"- **Contact:** {latest_submission.get('Contact_Name', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Your Selection")
        # Count tier levels
        tier1_count = sum([1 for t in [latest_submission.get('BP1_Tier'), latest_submission.get('BP2_Tier')] 
                          if 'One' in str(t) or 'Full' in str(t)])
        tier2_count = sum([1 for t in [latest_submission.get('BP1_Tier'), latest_submission.get('BP2_Tier')] 
                          if 'Two' in str(t) or 'Partial' in str(t)])
        tier3_count = sum([1 for t in [latest_submission.get('BP1_Tier'), latest_submission.get('BP2_Tier')] 
                          if 'Three' in str(t) or 'Planning' in str(t)])
        
        st.markdown(f"- 🟢 **Tier One:** {tier1_count} BP(s)")
        st.markdown(f"- 🟡 **Tier Two:** {tier2_count} BP(s)")
        st.markdown(f"- 🔴 **Tier Three:** {tier3_count} BP(s)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")

# ==================== NEED HELP ====================
st.markdown("## ❓ Need Help?")

help_col1, help_col2 = st.columns(2)

with help_col1:
    st.markdown("""
    **📧 Contact HSCRC:**
    - Questions about your submission?
    - Need to update information?
    - Technical issues?
    
    Please reach out to HSCRC staff for assistance.
    """)

with help_col2:
    st.markdown("""
    **📅 Important Dates:**
    - Data submission deadline: October 1, 2025
    - Quarterly review meetings: TBD
    - Annual assessment: December 2025
    
    Check with HSCRC for specific dates.
    """)

st.markdown("---")

# Footer
st.markdown("##### Maryland Health Services Cost Review Commission")
st.markdown("*For questions about your submission, please contact HSCRC staff.*")

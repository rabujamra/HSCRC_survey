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

# Import Google Sheets connector
from google_sheets_connector import load_data_from_sheets, append_row_to_sheets

# Import email sender
from email_sender import send_submission_email, send_approval_email

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="HSCRC Best Practices - Hospital Portal (Google Sheets)",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIGURATION ====================

# Google Sheets storage - no local CSV needed!
# Data is stored in: "HSCRC Survey Submissions" spreadsheet
HOSPITAL_CREDS = {
    "Adventist White Oak": "demo123",
    "Ascension St Agnes": "demo123",
    "Atlantic General": "demo123",
    "Calvert Health": "demo123",
    "Carroll Hospital Center": "demo123",
    "Christiana Care-Union Hospital": "demo123",
    "Fort Washington": "demo123",
    "Frederick Health": "demo123",
    "Garrett Regional": "demo123",
    "GBMC": "demo123",
    "Holy Cross Germantown": "demo123",
    "Holy Cross Silver Spring": "demo123",
    "Johns Hopkins Bayview": "demo123",
    "Johns Hopkins Hospital": "demo123",
    "Johns Hopkins Howard County": "demo123",
    "Luminis Anne Arundel Medical Ctr": "demo123",
    "Luminis Health-Doctors": "demo123",
    "Medstar Franklin Square": "demo123",
    "Medstar Good Samaritan": "demo123",
    "Medstar Harbor": "demo123",
    "Medstar Montgomery": "demo123",
    "Medstar Southern Maryland": "demo123",
    "Medstar St Mary's": "demo123",
    "Medstar Union Memorial": "demo123",
    "Mercy Medical Center": "demo123",
    "Meritus": "demo123",
    "Northwest": "demo123",
    "Shady Grove": "demo123",
    "Sinai": "demo123",
    "Suburban": "demo123",
    "Tidal Health": "demo123",
    "UM BWMC": "demo123",
    "UM Capital Region Medical Center": "demo123",
    "UM Charles Regional": "demo123",
    "UM Shore Regional": "demo123",
    "UM St Joseph Medical Center": "demo123",
    "UM Upper Chesapeake": "demo123",
    "UMMC Downtown": "demo123",
    "UMMC-Midtown": "demo123",
    "UPMC Western Maryland": "demo123"
}

BP_OPTIONS = {
    "": "-- Select Best Practice --",
    "BP1": "BP1: Interdisciplinary Rounds & Early Discharge Planning",
    "BP2": "BP2: Bed Capacity Alert System",
    "BP3": "BP3: Standardized Daily Shift Huddles",
    "BP4": "BP4: Expedited Care Intervention",
    "BP5": "BP5: Patient Flow Throughput Performance Council",
    "BP6": "BP6: Clinical Pathways & Observation Management"
}

TIER_DESCRIPTIONS = {
    "BP1": {
        "name": "Interdisciplinary Rounds & Early Discharge Planning",
        1: {"title": "Tier 1: Discharge Planning", "description": "Discharge planning adult general medical and surgical inpatient admissions\n\nAccountable Measure or Outcome:\n- Documentation within 48 hours of admission discharge plan\n- KPI: 70% of inpatient admissions have documented discharge planning OR 10% improvement from baseline"},
        2: {"title": "Tier 2: HRSN Screening", "description": "Includes Tier 1 PLUS: Adult inpatients offered screening for the 5 HRSN prior to discharge\n\nAccountable Measure or Outcome:\n- Documentation of SDOH for inpatients who are screened\n- KPI: 50% OR 10% improvement from baseline of all inpatients identified in their one offered screening for HRSN"},
        3: {"title": "Tier 3: Community Referrals", "description": "Tier 3: Adult inpatients screening positive for HRSN are given referrals to community resources prior to discharge\n\nAccountable Measure or Outcome:\n- Documentation of community resources access or referral for patients screening positive for one or more of HRSN\n- KPI: 75% OR 10% improvement from baseline of all positive screens for HRSN are given referral prior to discharge identified from tier two"}
    },
    "BP2": {
        "name": "Bed Capacity Alert System",
        1: {"title": "Tier 1: Establish Capacity Metrics", "description": "Organization establishes one or more capacity metrics\n\nExamples: Total patients in hospital, % beds occupied, ED boarder patients/ total ED beds, NEDOC score"},
        2: {"title": "Tier 2: Bed Capacity Alert Process", "description": "Includes Tier 1 PLUS: Organization establishes a capacity alert process (surge plan)\n\nDriven by capacity metrics that trigger defined actions that achieve expedited throughput."},
        3: {"title": "Tier 3: Demonstrate Activation", "description": "Includes Tier 1 & 2 PLUS: Organization quantitatively demonstrates consistent activation of surge plans in response to bed capacity triggers.\n\nInternal metrics to be hospital-defined"}
    },
    "BP3": {
        "name": "Standardized Daily Shift Huddles",
        1: {"title": "Tier 1: Daily Huddles", "description": "Daily huddles using multidisciplinary team approach\n\nFocus on throughput and discharges\n\n**Accountable Measure or Outcome:**\n- KPI: Multidisciplinary daily huddles are being completed at X frequency as defined by each organization"},
        2: {"title": "Tier 2: Standardized Infrastructure and an escalation process for addressing clinical and/or non-clinical barriers to discharge or throughput.", "description": "Includes Tier 1 PLUS: Standardized infrastructure\n\nExamples: standard scripting, documentation, huddle boards"},
        3: {"title": "Tier 3: KPI Monitoring", "description": "Includes Tier 1 & 2 PLUS: Monitoring and reporting of KPIs\n\nExample: % discharge orders by noon"}
    },
    "BP4": {
        "name": "Expedited Care Intervention",
        1: {"title": "Tier 1: One Practice", "description": "Implement ONE expedited care practice\n\nOptions: Nurse Expediter, Discharge Lounge, Observation Unit, Provider Screening, Dedicated CM/SW Resources in ED\n\nReport KPI for chosen practice."},
        2: {"title": "Tier 2: Two Practices", "description": "Implement TWO expedited care practices\n\nReport KPI for each practice"},
        3: {"title": "Tier 3: Three Practices", "description": "Implement THREE expedited care practices\n\nReport KPI for each practice"}
    },
    "BP5": {
        "name": "Patient Flow Throughput Performance Council",
        1: {"title": "Tier 1: Create Structure", "description": "Create multidisciplinary team\n\nExecutive sponsor, committee charter, monthly meetings"},
        2: {"title": "Tier 2: Establish Accountability", "description": "Includes Tier 1 PLUS: Monthly meetings with stakeholders\n\n**Accountable Measure:**\n- Committee meetings include regular 'report outs' on relevant KPIs and data\n- The report outs include participation from at least one hospital executive\n- KPIs are evidence-based and shown to improve capacity or throughput or enhance patient care"},
        3: {"title": "Tier 3: Change Culture", "description": "Includes Tier 1 & 2 PLUS: Cascade goals to nursing units to ensure front line staff awareness & engagement.\n\n**Accountable Measure:**\n- KPIs are reported for key units or service lines as determined by the hospital\n- The committee ensures routine capacity/throughput huddles to drive patient flow and reduce delays\n- The committee ensures that any observation patients have built-in efficiencies & protocols that promote discharge within two midnights. Observation LOS is tracked, data is shared, and OBS PI processes are implemented on units with OBS patients"}
    },
    "BP6": {
        "name": "Clinical Pathways & Observation Management",
        1: {"title": "Tier 1: Design and Implement", "description": "Organization selects and implements a clinical pathway tailored to patient population\n\nBased on facility's unique needs"},
        2: {"title": "Tier 2: Develop Data Infrastructure", "description": "Includes Tier 1 PLUS: Data collection and analysis systems\n\nMonitor and evaluate outcomes. These systems should emphasize comparing the effectiveness of inpatient and ambulatory management strategies for the selected patient population, enabling data-driven decision-making and continuous improvement."},
        3: {"title": "Tier 3: Demonstrate Improvement", "description": "Includes Tier 1 & 2 PLUS: Demonstrate measurable results\n\nThe results will demonstrate a measurable decrease in unwarranted clinical variation and/or measurable improvement in outcomes specific to their chosen intervention."}
    }
}

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #0066cc;
        color: white;
        font-size: 18px;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        margin-top: 2rem;
    }
    .stButton>button:hover {
        background-color: #0052a3;
        border: none;
    }
    h1 {
        color: #0066cc;
    }
    h2 {
        color: #004080;
        margin-top: 2rem;
    }
    h3 {
        color: #0066cc;
        margin-top: 1.5rem;
    }
    .bp-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
        border: 2px solid #0066cc;
    }
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
    """Load data from Google Sheets"""
    try:
        df = load_data_from_sheets()
        if not df.empty:
            df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def get_hospital_submission(hospital_name):
    """
    Get the latest submission for a hospital from Google Sheets.
    Returns the most recent row (last row) for this hospital.
    """
    df = load_data()
    if df.empty:
        return None
    
    # Filter for this hospital
    hospital_data = df[df['hospital_name'] == hospital_name]
    if hospital_data.empty:
        return None
    
    # Return the last row (most recent)
    return hospital_data.iloc[-1]

def generate_hospital_pdf(latest_submission):
    """Generate PDF report for a hospital submission"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1f4788'), spaceAfter=30, alignment=TA_CENTER)
    story.append(Paragraph("HSCRC Best Practice Survey Submission", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Hospital Info
    hospital_name = latest_submission.get('hospital_name', 'N/A')
    contact_name = latest_submission.get('contact_name', 'N/A')
    email = latest_submission.get('email', 'N/A')
    phone = latest_submission.get('phone', 'N/A')
    timestamp = latest_submission.get('timestamp', 'N/A')
    
    # Approval status
    is_approved = latest_submission.get('approved', 'False')
    if pd.isna(is_approved) or is_approved == '':
        is_approved = False
    else:
        if isinstance(is_approved, bool):
            is_approved = is_approved
        else:
            is_approved = str(is_approved).strip().lower() in ('true', '1', 'yes')
    
    approved_by = latest_submission.get('approved_by', '')
    approved_at = latest_submission.get('approved_at', '')
    approval_status = 'APPROVED' if is_approved else 'DRAFT'
    
    info_data = [
        ['Hospital:', str(hospital_name)],
        ['Contact:', str(contact_name)],
        ['Email:', str(email)],
        ['Phone:', str(phone)],
        ['Submitted:', str(timestamp)],
        ['Status:', approval_status]
    ]
    
    if is_approved and approved_by:
        info_data.append(['Approved By:', str(approved_by)])
        info_data.append(['Approved At:', str(approved_at)])
    
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
    
    # BP1
    bp1_code = latest_submission.get('bp1')
    if pd.notna(bp1_code) and bp1_code != '':
        bp1_name = BP_OPTIONS.get(bp1_code, bp1_code)
        bp1_tier = latest_submission.get('bp1_tier', '')
        bp1_rationale = latest_submission.get('bp1_rationale', '')
        bp1_success = latest_submission.get('bp1_success', '')
        
        story.append(Paragraph(f"<b>First Best Practice: {bp1_name}</b>", styles['Heading2']))
        
        bp1_data = [['Tier:', f"Tier {bp1_tier}"]]
        
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
    
    # BP2
    bp2_code = latest_submission.get('bp2')
    if pd.notna(bp2_code) and bp2_code != '':
        bp2_name = BP_OPTIONS.get(bp2_code, bp2_code)
        bp2_tier = latest_submission.get('bp2_tier', '')
        bp2_rationale = latest_submission.get('bp2_rationale', '')
        bp2_success = latest_submission.get('bp2_success', '')
        
        story.append(Paragraph(f"<b>Second Best Practice: {bp2_name}</b>", styles['Heading2']))
        
        bp2_data = [['Tier:', f"Tier {bp2_tier}"]]
        
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

# ==================== QUESTION RENDERERS ====================

def render_bp1_questions(tier, prefix, existing_data=None):
    """BP1: Interdisciplinary Rounds - with Tier 3 KPI 5/6 target/actual"""
    st.markdown("### Select the KPIs you plan to achieve: *")
    
    data = {}
    existing_data = existing_data or {}
    
    # Tier 1 KPIs
    kpi1 = st.checkbox("70% of inpatient admissions have documented discharge planning", 
                       key=f"{prefix}_kpi1",
                       value=bool(existing_data.get(f'{prefix}_kpi1_target')))
    kpi2 = st.checkbox("10% improvement from baseline" if tier == 1 else "10% improvement from baseline of above KPI", 
                       key=f"{prefix}_kpi2",
                       value=bool(existing_data.get(f'{prefix}_kpi2_target')))
    
    # Tier 2 KPIs
    kpi3 = kpi4 = False
    if tier >= 2:
        kpi3 = st.checkbox("50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge", 
                          key=f"{prefix}_kpi3",
                          value=bool(existing_data.get(f'{prefix}_kpi3_target')))
        kpi4 = st.checkbox("10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN", 
                          key=f"{prefix}_kpi4",
                          value=bool(existing_data.get(f'{prefix}_kpi4_target')))
    
    # Tier 3 KPIs
    kpi5 = kpi6 = False
    if tier >= 3:
        kpi5 = st.checkbox("75% of adult inpatients that have screened positive for HRSN are given referrals to community resources prior to discharge", 
                          key=f"{prefix}_kpi5",
                          value=bool(existing_data.get(f'{prefix}_kpi5_target')))
        kpi6 = st.checkbox("10% improvement from baseline of all positive screens for HRSN are given a referral prior to discharge identified from tier two", 
                          key=f"{prefix}_kpi6",
                          value=bool(existing_data.get(f'{prefix}_kpi6_target')))
    
    st.markdown("---")
    
    # Target/Actual for KPI 1-4
    if kpi1:
        st.markdown(f"**Provide the target KPI if you selected, \"70% of inpatient admissions have documented discharge planning.\" {'*' if tier == 3 else ''}**")
        data[f'{prefix}_kpi1_target'] = st.text_input("Target:", key=f"{prefix}_kpi1_target", value=existing_data.get(f'{prefix}_kpi1_target', ''))
        st.markdown("**Provide the actual KPI performance results if you selected, \"70% of inpatient admissions have documented discharge planning.\"**")
        data[f'{prefix}_kpi1_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi1_actual", value=existing_data.get(f'{prefix}_kpi1_actual', ''))
    
    if kpi2:
        kpi2_text = "10% improvement from baseline" if tier == 1 else "10% improvement from baseline of above KPI"
        st.markdown(f"**Provide the target KPI if you selected, \"{kpi2_text}.\"**")
        data[f'{prefix}_kpi2_target'] = st.text_input("Target:", key=f"{prefix}_kpi2_target", value=existing_data.get(f'{prefix}_kpi2_target', ''))
        st.markdown(f"**Provide the actual KPI performance results if you selected, \"{kpi2_text}.\"**")
        data[f'{prefix}_kpi2_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi2_actual", value=existing_data.get(f'{prefix}_kpi2_actual', ''))
    
    if kpi3:
        st.markdown("**Provide the target KPI if you selected, \"50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge.\"**")
        data[f'{prefix}_kpi3_target'] = st.text_input("Target:", key=f"{prefix}_kpi3_target", value=existing_data.get(f'{prefix}_kpi3_target', ''))
        st.markdown("**Provide the actual KPI performance results if you selected, \"50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge.\"**")
        data[f'{prefix}_kpi3_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi3_actual", value=existing_data.get(f'{prefix}_kpi3_actual', ''))
    
    if kpi4:
        st.markdown("**Provide the target KPI if you selected, \"10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN.\"**")
        data[f'{prefix}_kpi4_target'] = st.text_input("Target:", key=f"{prefix}_kpi4_target", value=existing_data.get(f'{prefix}_kpi4_target', ''))
        st.markdown("**Provide the actual KPI performance results if you selected, \"10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN.\"**")
        data[f'{prefix}_kpi4_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi4_actual", value=existing_data.get(f'{prefix}_kpi4_actual', ''))
    
    # Target/Actual for KPI 5 & 6 in Tier 3
    if kpi5:
        st.markdown("**Provide the target KPI if you selected, \"75% of adult inpatients that have screened positive for HRSN are given referrals to community resources prior to discharge.\" *")
        data[f'{prefix}_kpi5_target'] = st.text_input("Target:", key=f"{prefix}_kpi5_target", value=existing_data.get(f'{prefix}_kpi5_target', ''))
        st.markdown("**Provide the actual KPI performance results if you selected, \"75% of adult inpatients that have screened positive for HRSN are given referrals to community resources prior to discharge.\" *")
        data[f'{prefix}_kpi5_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi5_actual", value=existing_data.get(f'{prefix}_kpi5_actual', ''))
    
    if kpi6:
        st.markdown("**Provide the target KPI if you selected, \"10% improvement from baseline of all positive screens for HRSN are given a referral prior to discharge identified from tier two.\" *")
        data[f'{prefix}_kpi6_target'] = st.text_input("Target:", key=f"{prefix}_kpi6_target", value=existing_data.get(f'{prefix}_kpi6_target', ''))
        st.markdown("**Provide the actual KPI performance results if you selected, \"10% improvement from baseline of all positive screens for HRSN are given a referral prior to discharge identified from tier two.\" *")
        data[f'{prefix}_kpi6_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi6_actual", value=existing_data.get(f'{prefix}_kpi6_actual', ''))
    
    # Rationale and Success Stories
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

def render_bp2_questions(tier, prefix, existing_data=None):
    """BP2: Bed Capacity Alert System - CUMULATIVE"""
    st.markdown("### Tier 1: Capacity Metrics")
    st.markdown("**Describe the one or more capacity metrics your organization selected to achieve tier 1: ***")
    
    data = {}
    existing_data = existing_data or {}
    
    metrics = []
    if st.checkbox("Total number of patients in hospital", key=f"{prefix}_metric_total"):
        metrics.append("Total patients")
    if st.checkbox("Percent of hospital beds occupied", key=f"{prefix}_metric_beds"):
        metrics.append("% beds occupied")
    if st.checkbox("Percent of ED border patients / overall ED beds", key=f"{prefix}_metric_ed"):
        metrics.append("% ED border")
    if st.checkbox("NEDOC score", key=f"{prefix}_metric_nedoc"):
        metrics.append("NEDOC")
    if st.checkbox("Other", key=f"{prefix}_metric_other_check"):
        other = st.text_input("Describe other capacity metric *", key=f"{prefix}_metric_other")
        metrics.append(f"Other: {other}")
    
    data[f'{prefix}_capacity_metrics'] = ", ".join(metrics)
    data[f'{prefix}_t1_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 1 *", 
                                                  key=f"{prefix}_t1_target",
                                                  value=existing_data.get(f'{prefix}_t1_target', ''))
    data[f'{prefix}_t1_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 1 *", 
                                                  key=f"{prefix}_t1_actual",
                                                  value=existing_data.get(f'{prefix}_t1_actual', ''))
    
    if tier >= 2:
        st.markdown("### Tier 2: Bed Capacity Alert Process")
        data[f'{prefix}_t2_surge'] = st.text_area("Describe the established bed capacity alert process (aka surge plan) driven by capacity metrics *", 
                                                    key=f"{prefix}_t2_surge", height=150,
                                                    value=existing_data.get(f'{prefix}_t2_surge', ''))
        data[f'{prefix}_t2_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 2 *", 
                                                      key=f"{prefix}_t2_target",
                                                      value=existing_data.get(f'{prefix}_t2_target', ''))
        data[f'{prefix}_t2_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 2 *", 
                                                      key=f"{prefix}_t2_actual",
                                                      value=existing_data.get(f'{prefix}_t2_actual', ''))
    
    if tier >= 3:
        st.markdown("### Tier 3: Demonstrate Activation")
        data[f'{prefix}_t3_quant'] = st.text_area("Describe the process to achieve tier 3, when an organization quantitatively demonstrates consistent activation of surge plans *", 
                                                    key=f"{prefix}_t3_quant", height=150,
                                                    value=existing_data.get(f'{prefix}_t3_quant', ''))
        data[f'{prefix}_t3_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 3 *", 
                                                      key=f"{prefix}_t3_target",
                                                      value=existing_data.get(f'{prefix}_t3_target', ''))
        data[f'{prefix}_t3_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 3 *", 
                                                      key=f"{prefix}_t3_actual",
                                                      value=existing_data.get(f'{prefix}_t3_actual', ''))
    
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

def render_bp3_questions(tier, prefix, existing_data=None):
    """BP3: Standardized Daily Shift Huddles - CUMULATIVE"""
    data = {}
    existing_data = existing_data or {}
    
    st.markdown("### Tier 1: Daily Huddles")
    data[f'{prefix}_t1_kpi'] = st.text_area("Provide the KPI chosen to achieve tier 1 *", 
                                             key=f"{prefix}_t1_kpi", height=100,
                                             value=existing_data.get(f'{prefix}_t1_kpi', ''))
    data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 1 *", 
                                                 key=f"{prefix}_t1_actual", height=100,
                                                 value=existing_data.get(f'{prefix}_t1_actual', ''))
    
    if tier >= 2:
        st.markdown("### Tier 2: Standardized Infrastructure")
        data[f'{prefix}_t2_kpi'] = st.text_area("Provide the KPI chosen to achieve tier 2 *", 
                                                 key=f"{prefix}_t2_kpi", height=100,
                                                 value=existing_data.get(f'{prefix}_t2_kpi', ''))
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 2 *", 
                                                     key=f"{prefix}_t2_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t2_actual', ''))
    
    if tier >= 3:
        st.markdown("### Tier 3: KPI Monitoring")
        st.markdown("**Describe the KPI your organization implemented to achieve tier 3: ***")
        kpi_types = []
        if st.checkbox("Percent of discharge orders written by noon", key=f"{prefix}_t3_noon"):
            kpi_types.append("Discharge orders by noon")
        if st.checkbox("Percent of patients leaving the facility by a designated time", key=f"{prefix}_t3_leaving"):
            kpi_types.append("Patients leaving by designated time")
        if st.checkbox("Other", key=f"{prefix}_t3_other_check"):
            other = st.text_input("Describe other KPI *", key=f"{prefix}_t3_other")
            kpi_types.append(f"Other: {other}")
        
        data[f'{prefix}_t3_kpi_type'] = ", ".join(kpi_types)
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the KPI formula chosen to achieve tier 3 *", 
                                                      key=f"{prefix}_t3_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t3_formula', ''))
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 3 *", 
                                                     key=f"{prefix}_t3_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t3_actual', ''))
    
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

def render_bp4_questions(tier, prefix, existing_data=None):
    """BP4: Expedited Care Intervention - NON-HIERARCHICAL"""
    practices = ["Nurse Expediter", "Discharge Lounge", "Observation Unit (ED or hospital based)", 
                 "Provider Screening in Triage / Early Provider Screening Process", 
                 "Dedicated CM and/or SW resources in the ED"]
    
    data = {}
    existing_data = existing_data or {}
    
    if tier == 1:
        st.markdown("### Tier 1: Select ONE Expedited Care Practice")
        data[f'{prefix}_practice'] = st.radio("Select the expedited care practice you plan to report *", practices, key=f"{prefix}_practice")
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for this practice *", 
                                                      key=f"{prefix}_t1_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t1_formula', ''))
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance results *", 
                                                     key=f"{prefix}_t1_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t1_actual', ''))
    
    elif tier == 2:
        st.markdown("### Tier 2: Select TWO Expedited Care Practices")
        selected = st.multiselect("Select two expedited care practices *", practices, key=f"{prefix}_practices")
        data[f'{prefix}_practices'] = ", ".join(selected)
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for first practice *", 
                                                      key=f"{prefix}_t1_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t1_formula', ''))
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance for first practice *", 
                                                     key=f"{prefix}_t1_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t1_actual', ''))
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the KPI formula for second practice *", 
                                                      key=f"{prefix}_t2_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t2_formula', ''))
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance for second practice *", 
                                                     key=f"{prefix}_t2_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t2_actual', ''))
    
    elif tier == 3:
        st.markdown("### Tier 3: Select THREE Expedited Care Practices")
        selected = st.multiselect("Select three expedited care practices *", practices, key=f"{prefix}_practices")
        data[f'{prefix}_practices'] = ", ".join(selected)
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for first practice *", 
                                                      key=f"{prefix}_t1_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t1_formula', ''))
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance for first practice *", 
                                                     key=f"{prefix}_t1_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t1_actual', ''))
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the KPI formula for second practice *", 
                                                      key=f"{prefix}_t2_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t2_formula', ''))
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance for second practice *", 
                                                     key=f"{prefix}_t2_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t2_actual', ''))
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the KPI formula for third practice *", 
                                                      key=f"{prefix}_t3_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t3_formula', ''))
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the actual KPI performance for third practice *", 
                                                     key=f"{prefix}_t3_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t3_actual', ''))
    
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

def render_bp5_questions(tier, prefix, existing_data=None):
    """BP5: Patient Flow Throughput Performance Council - NON-HIERARCHICAL (like BP4)"""
    data = {}
    existing_data = existing_data or {}
    
    if tier == 1:
        st.markdown("### Tier 1: Create Structure")
        st.markdown("**Select the accountable measure(s) you plan to report: ***")
        measures = []
        if st.checkbox("Committee/council scheduled monthly at minimum", key=f"{prefix}_t1_monthly"):
            measures.append("Monthly committee")
        if st.checkbox("Team develops and works on capacity and throughput projects", key=f"{prefix}_t1_projects"):
            measures.append("Throughput projects")
        if st.checkbox("Other", key=f"{prefix}_t1_other_check"):
            other = st.text_input("Describe other measure *", key=f"{prefix}_t1_other")
            measures.append(f"Other: {other}")
        
        data[f'{prefix}_t1_measures'] = ", ".join(measures)
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the target measures' formula to achieve tier 1 *", 
                                                      key=f"{prefix}_t1_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t1_formula', ''))
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 1 *", 
                                                     key=f"{prefix}_t1_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t1_actual', ''))
        data[f'{prefix}_improvements'] = st.text_area("Describe any throughput improvements measured after implementing this best practice *", 
                                                        key=f"{prefix}_improvements", height=100,
                                                        value=existing_data.get(f'{prefix}_improvements', ''))
    
    elif tier == 2:
        st.markdown("### Tier 2: Establish Accountability")
        st.markdown("**Select the accountable measure(s) you plan to report: ***")
        measures2 = []
        if st.checkbox("Committee/council scheduled monthly at minimum", key=f"{prefix}_t2_monthly"):
            measures2.append("Monthly committee")
        if st.checkbox("Committee meetings include regular report outs", key=f"{prefix}_t2_reportouts"):
            measures2.append("Report outs")
        if st.checkbox("Report outs include executive participation", key=f"{prefix}_t2_exec"):
            measures2.append("Executive participation")
        if st.checkbox("Team develops and works on capacity and throughput projects", key=f"{prefix}_t2_projects"):
            measures2.append("Throughput projects")
        if st.checkbox("KPIs are evidence-based", key=f"{prefix}_t2_evidence"):
            measures2.append("Evidence-based KPIs")
        if st.checkbox("Other", key=f"{prefix}_t2_other_check"):
            other = st.text_input("Describe other Tier 2 measure *", key=f"{prefix}_t2_other")
            measures2.append(f"Other: {other}")
        
        data[f'{prefix}_t2_measures'] = ", ".join(measures2)
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the target measures' formula to achieve tier 2 *", 
                                                      key=f"{prefix}_t2_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t2_formula', ''))
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 2 *", 
                                                     key=f"{prefix}_t2_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t2_actual', ''))
        data[f'{prefix}_improvements'] = st.text_area("Describe any throughput improvements measured after implementing this best practice *", 
                                                        key=f"{prefix}_improvements", height=100,
                                                        value=existing_data.get(f'{prefix}_improvements', ''))
    
    elif tier == 3:
        st.markdown("### Tier 3: Change Culture")
        st.markdown("**Select the accountable measure(s) you plan to report: ***")
        measures3 = []
        if st.checkbox("Committee/council scheduled monthly at minimum", key=f"{prefix}_t3_monthly"):
            measures3.append("Monthly committee")
        if st.checkbox("Committee meetings include regular report outs", key=f"{prefix}_t3_reportouts"):
            measures3.append("Report outs")
        if st.checkbox("Report outs include executive participation", key=f"{prefix}_t3_exec"):
            measures3.append("Executive participation")
        if st.checkbox("Team develops and works on capacity and throughput projects", key=f"{prefix}_t3_projects"):
            measures3.append("Throughput projects")
        if st.checkbox("Committee ensures routine capacity/throughput huddles", key=f"{prefix}_t3_huddles"):
            measures3.append("Routine huddles")
        if st.checkbox("Committee ensures observation protocols", key=f"{prefix}_t3_obs"):
            measures3.append("Observation protocols")
        if st.checkbox("KPIs are evidence-based", key=f"{prefix}_t3_evidence"):
            measures3.append("Evidence-based KPIs")
        if st.checkbox("KPIs reported for key units/service lines", key=f"{prefix}_t3_units"):
            measures3.append("KPIs for units")
        if st.checkbox("Other", key=f"{prefix}_t3_other_check"):
            other = st.text_input("Describe other Tier 3 measure *", key=f"{prefix}_t3_other")
            measures3.append(f"Other: {other}")
        
        data[f'{prefix}_t3_measures'] = ", ".join(measures3)
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the target measures' formula to achieve tier 3 *", 
                                                      key=f"{prefix}_t3_formula", height=100,
                                                      value=existing_data.get(f'{prefix}_t3_formula', ''))
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 3 *", 
                                                     key=f"{prefix}_t3_actual", height=100,
                                                     value=existing_data.get(f'{prefix}_t3_actual', ''))
        data[f'{prefix}_improvements'] = st.text_area("Describe any throughput improvements measured after implementing this best practice *", 
                                                        key=f"{prefix}_improvements", height=100,
                                                        value=existing_data.get(f'{prefix}_improvements', ''))
    
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

def render_bp6_questions(tier, prefix, existing_data=None):
    """BP6: Clinical Pathways & Observation Management - CUMULATIVE"""
    data = {}
    existing_data = existing_data or {}
    
    st.markdown("### Tier 1: Design and Implement")
    data[f'{prefix}_t1_pathway'] = st.text_area("Describe the clinical pathway that was selected and implemented to achieve tier 1 *", 
                                                 key=f"{prefix}_t1_pathway", height=150,
                                                 value=existing_data.get(f'{prefix}_t1_pathway', ''))
    
    if tier >= 2:
        st.markdown("### Tier 2: Develop Data Infrastructure")
        data[f'{prefix}_t2_data'] = st.text_area("Describe the data collection and analysis systems to monitor and evaluate outcomes that were selected and implemented to achieve tier 2 *", 
                                                   key=f"{prefix}_t2_data", height=150,
                                                   value=existing_data.get(f'{prefix}_t2_data', ''))
    
    if tier >= 3:
        st.markdown("### Tier 3: Demonstrate Improvement")
        data[f'{prefix}_t3_improvement'] = st.text_area("Describe the measurable decrease in unwarranted clinical variation and/or measurable improvement in outcomes specific to your chosen intervention to achieve tier 3 *", 
                                                          key=f"{prefix}_t3_improvement", height=150,
                                                          value=existing_data.get(f'{prefix}_t3_improvement', ''))
    
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", 
                                                key=f"{prefix}_rationale", height=150,
                                                value=existing_data.get(f'{prefix}_rationale', ''))
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", 
                                              key=f"{prefix}_success", height=150,
                                              value=existing_data.get(f'{prefix}_success', ''))
    
    return data

# ==================== INITIALIZE SESSION STATE ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'hospital' not in st.session_state:
    st.session_state.hospital = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'just_submitted' not in st.session_state:
    st.session_state.just_submitted = False

# ==================== LOGIN SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🔐 Hospital Login")
    st.markdown("---")
    
    if not st.session_state.logged_in:
        hospital_selection = st.selectbox(
            "Select your hospital:",
            options=[""] + list(HOSPITAL_CREDS.keys())
        )
        
        password = st.text_input("Password:", type="password")
        login_button = st.button("🔓 Login", use_container_width=True)
        
        if login_button:
            if hospital_selection and password == HOSPITAL_CREDS.get(hospital_selection):
                st.session_state.logged_in = True
                st.session_state.hospital = hospital_selection
                st.success(f"✅ Welcome, {hospital_selection}!")
                st.rerun()
            else:
                st.error("❌ Invalid hospital or password")
        
        st.markdown("---")
        st.markdown("**Demo Credentials:**")
        st.markdown("- **Hospital:** Any from dropdown")
        st.markdown("- **Password:** demo123")
    else:
        st.markdown(f"**Logged in as:**")
        st.info(st.session_state.hospital)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ==================== CHECK LOGIN ====================
if not st.session_state.logged_in:
    st.markdown('<div class="main-header">🏥 HSCRC Best Practices Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Maryland Health Services Cost Review Commission</div>', unsafe_allow_html=True)
    st.info("👈 Please login using the sidebar to access the survey")
    st.markdown("---")
    st.markdown("#### About This Portal")
    st.markdown("""
    This secure portal allows hospitals to:
    - ✅ Submit your Best Practice survey
    - ✅ View your submission
    - ✅ Download your official PDF report
    - ✅ Edit your submission anytime
    
    Each hospital can only access their own data. For questions, please contact HSCRC staff.
    """)
    st.stop()

# ==================== MAIN APP (AFTER LOGIN) ====================
selected_hospital = st.session_state.hospital

# Check if hospital has existing submission
existing_submission = get_hospital_submission(selected_hospital)

# Determine which screen to show
if st.session_state.just_submitted:
    # Show success message, then portal view
    st.success("## ✅ Survey Submitted Successfully!")
    st.markdown("### Your submission has been recorded in Google Sheets!")
    st.markdown("---")
    st.session_state.just_submitted = False
    st.session_state.edit_mode = False
    # Continue to show portal view below

if existing_submission is not None and not st.session_state.edit_mode:
    # ==================== PORTAL VIEW (Read-Only) ====================
    st.markdown('<div class="main-header">🏥 Your Submission</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{selected_hospital}</div>', unsafe_allow_html=True)
    
    # Check approval status
    is_approved = existing_submission.get('approved', 'False')
    # Google Sheets stores everything as strings, so we need to check string values
    if pd.isna(is_approved) or is_approved == '':
        is_approved = False
    else:
        # Handle both boolean and string representations
        if isinstance(is_approved, bool):
            is_approved = is_approved
        else:
            # Convert string to boolean
            is_approved = str(is_approved).strip().lower() in ('true', '1', 'yes')
    
    # Approval Status Banner
    if is_approved:
        approved_by = existing_submission.get('approved_by', 'Unknown')
        approved_at = existing_submission.get('approved_at', 'Unknown')
        st.success(f"✅ **APPROVED** | Approved by: {approved_by} | Date: {approved_at}")
    else:
        st.info("📝 **DRAFT** - This submission is editable and not yet approved")
    
    st.markdown("---")
    
    # Action buttons at top
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col2:
        # Edit button (only show if not approved)
        if not is_approved:
            if st.button("✏️ Edit", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
    
    with col3:
        # Approve/Un-approve button
        if not is_approved:
            # Show Approve button - updates the row with approved=True
            if st.button("✅ Approve", use_container_width=True):
                # Take current submission data and update with approval
                data = existing_submission.to_dict()
                approved_at_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data['approved'] = 'True'  # Store as string for Google Sheets
                data['approved_by'] = existing_submission.get('contact_name', 'Unknown')
                data['approved_at'] = approved_at_time
                
                with st.spinner("Approving submission..."):
                    success = append_row_to_sheets(data)  # Actually updates the row now
                
                if success:
                    # Send approval email to hospital
                    with st.spinner("Sending approval email..."):
                        email_sent = send_approval_email(
                            recipient_email=existing_submission.get('email'),
                            hospital_name=selected_hospital,
                            contact_name=existing_submission.get('contact_name'),
                            approved_by=data['approved_by'],
                            approved_at=approved_at_time
                        )
                    
                    if email_sent:
                        st.success("📧 Approval email sent!")
                    
                    st.cache_data.clear()
                    st.success("✅ Submission approved!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update approval status")
        else:
            # Show Un-approve button
            if st.button("🔓 Un-approve", use_container_width=True):
                st.session_state['show_unapprove_dialog'] = True
                st.rerun()
    
    # Un-approve dialog (using expander as modal)
    if st.session_state.get('show_unapprove_dialog', False):
        st.markdown("---")
        st.markdown("### ⚠️ Un-approve Submission")
        
        authorized_email = existing_submission.get('email', '')
        approved_by = existing_submission.get('approved_by', 'Unknown')
        approved_at = existing_submission.get('approved_at', 'Unknown')
        
        st.warning(f"""
        **This submission was approved by:** {approved_by}  
        **Approved on:** {approved_at}
        
        To un-approve this submission, enter the authorized email address.
        """)
        
        st.info(f"**Authorized email:** {authorized_email}")
        
        entered_email = st.text_input("Enter email to verify:", key="unapprove_email")
        
        col_verify1, col_verify2, col_verify3 = st.columns([2, 1, 1])
        
        with col_verify2:
            if st.button("✅ Verify & Un-approve", use_container_width=True):
                if entered_email.strip().lower() == authorized_email.strip().lower():
                    # Un-approve by updating the row with approval fields cleared
                    data = existing_submission.to_dict()
                    data['approved'] = 'False'  # Store as string for Google Sheets
                    data['approved_by'] = ''
                    data['approved_at'] = ''
                    
                    with st.spinner("Un-approving submission..."):
                        success = append_row_to_sheets(data)  # Actually updates the row now
                    
                    if success:
                        st.cache_data.clear()
                        st.session_state['show_unapprove_dialog'] = False
                        st.success("✅ Submission un-approved! You can now edit.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to un-approve submission")
                else:
                    st.error("❌ Email does not match! Unauthorized.")
        
        with col_verify3:
            if st.button("Cancel", use_container_width=True):
                st.session_state['show_unapprove_dialog'] = False
                st.rerun()
        
        st.markdown("---")
    
    # Submission Info Card
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Submission Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Contact:** {existing_submission.get('contact_name', 'N/A')}")
    with col2:
        st.markdown(f"**Email:** {existing_submission.get('email', 'N/A')}")
    with col3:
        st.markdown(f"**Submitted:** {existing_submission.get('timestamp', 'N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("## 🎯 Your Best Practices")
    
    bp_reported = False
    
    # Display BP1
    if pd.notna(existing_submission.get('bp1')) and existing_submission.get('bp1') != '':
        bp_reported = True
        bp1_code = existing_submission.get('bp1')
        bp1_name = BP_OPTIONS.get(bp1_code, bp1_code)
        bp1_tier = existing_submission.get('bp1_tier', '')
        bp1_rationale = existing_submission.get('bp1_rationale', '')
        bp1_success = existing_submission.get('bp1_success', '')
        
        tier_int = int(bp1_tier) if pd.notna(bp1_tier) else 1
        tier_class = f"tier-{tier_int}"
        color = ['🟢', '🟡', '🔴'][tier_int - 1] if tier_int in [1, 2, 3] else '🔵'
        
        st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
        st.markdown(f"### {color} First Best Practice")
        st.markdown(f"**{bp1_name}**")
        st.markdown(f"**Tier:** Tier {bp1_tier}")
        
        if pd.notna(bp1_rationale) and str(bp1_rationale).strip() not in ('', 'None', 'nan'):
            st.markdown(f"**Rationale:** {bp1_rationale}")
        
        if pd.notna(bp1_success) and str(bp1_success).strip() not in ('', 'None', 'nan'):
            st.markdown(f"**Success Stories/Barriers:** {bp1_success}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display BP2
    if pd.notna(existing_submission.get('bp2')) and existing_submission.get('bp2') != '':
        bp_reported = True
        bp2_code = existing_submission.get('bp2')
        bp2_name = BP_OPTIONS.get(bp2_code, bp2_code)
        bp2_tier = existing_submission.get('bp2_tier', '')
        bp2_rationale = existing_submission.get('bp2_rationale', '')
        bp2_success = existing_submission.get('bp2_success', '')
        
        tier_int = int(bp2_tier) if pd.notna(bp2_tier) else 1
        tier_class = f"tier-{tier_int}"
        color = ['🟢', '🟡', '🔴'][tier_int - 1] if tier_int in [1, 2, 3] else '🔵'
        
        st.markdown(f'<div class="bp-card {tier_class}">', unsafe_allow_html=True)
        st.markdown(f"### {color} Second Best Practice")
        st.markdown(f"**{bp2_name}**")
        st.markdown(f"**Tier:** Tier {bp2_tier}")
        
        if pd.notna(bp2_rationale) and str(bp2_rationale).strip() not in ('', 'None', 'nan'):
            st.markdown(f"**Rationale:** {bp2_rationale}")
        
        if pd.notna(bp2_success) and str(bp2_success).strip() not in ('', 'None', 'nan'):
            st.markdown(f"**Success Stories/Barriers:** {bp2_success}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not bp_reported:
        st.info("No best practices reported yet.")
    
    # Download PDF button
    if bp_reported:
        st.markdown("---")
        st.markdown("## 📄 Download Report")
        pdf_buffer = generate_hospital_pdf(existing_submission)
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer,
            file_name=f"{selected_hospital}_HSCRC_Survey.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown("##### Maryland Health Services Cost Review Commission")
    st.markdown("*For questions about your submission, please contact HSCRC staff.*")

else:
    # ==================== SURVEY FORM ====================
    if st.session_state.edit_mode:
        st.markdown('<div class="main-header">✏️ Edit Your Submission</div>', unsafe_allow_html=True)
        
        # Check if current submission is approved
        if existing_submission is not None:
            is_approved = existing_submission.get('approved', 'False')
            if pd.isna(is_approved) or is_approved == '':
                is_approved = False
            else:
                if isinstance(is_approved, bool):
                    is_approved = is_approved
                else:
                    is_approved = str(is_approved).strip().lower() in ('true', '1', 'yes')
            
            if is_approved:
                st.warning("⚠️ **Note:** Making changes will reset the approval status. Your submission will need to be re-approved after updating.")
    else:
        st.markdown('<div class="main-header">🏥 HSCRC Best Practices Survey</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="sub-header">{selected_hospital}</div>', unsafe_allow_html=True)
    st.markdown("### Please complete all sections below. You will select TWO best practices to report.")
    st.markdown("---")
    
    # Convert existing submission to dict if it exists
    existing_data = existing_submission.to_dict() if existing_submission is not None else {}
    
    # Hospital Info (pre-filled if editing)
    st.markdown("## 🏥 Hospital Information")
    
    col1, col2 = st.columns(2)
    with col1:
        contact_name = st.text_input("Contact Name *", value=existing_data.get('contact_name', ''))
    with col2:
        email = st.text_input("Email Address *", value=existing_data.get('email', ''))
    
    phone = st.text_input("Phone Number *", value=existing_data.get('phone', ''))
    st.markdown("---")
    
    # ==================== BP #1 ====================
    st.markdown('<div class="bp-section">', unsafe_allow_html=True)
    st.markdown("## 📋 Best Practice #1")
    
    bp1_default = existing_data.get('bp1', '')
    bp1_options_list = list(BP_OPTIONS.keys())
    bp1_default_index = bp1_options_list.index(bp1_default) if bp1_default in bp1_options_list else 0
    
    bp1 = st.selectbox("Select the first Best Practice *", 
                       bp1_options_list, 
                       format_func=lambda x: BP_OPTIONS[x], 
                       key="bp1",
                       index=bp1_default_index)
    
    bp1_data = {}
    if bp1 and bp1 != "":
        st.markdown(f"### 🎯 {TIER_DESCRIPTIONS[bp1]['name']}")
        
        for t in [1, 2, 3]:
            with st.expander(f"📖 {TIER_DESCRIPTIONS[bp1][t]['title']}", expanded=False):
                st.text(TIER_DESCRIPTIONS[bp1][t]['description'])
        
        tier1_default = int(existing_data.get('bp1_tier', 1)) if existing_data.get('bp1_tier') else 1
        tier1 = st.radio("Select the highest tier you plan to report *", 
                        [1, 2, 3], 
                        format_func=lambda x: f"Tier {x}", 
                        key="tier1", 
                        horizontal=True,
                        index=tier1_default - 1)
        
        st.markdown("---")
        st.markdown("### 📝 Questions")
        
        if bp1 == "BP1":
            bp1_data = render_bp1_questions(tier1, "bp1", existing_data)
        elif bp1 == "BP2":
            bp1_data = render_bp2_questions(tier1, "bp1", existing_data)
        elif bp1 == "BP3":
            bp1_data = render_bp3_questions(tier1, "bp1", existing_data)
        elif bp1 == "BP4":
            bp1_data = render_bp4_questions(tier1, "bp1", existing_data)
        elif bp1 == "BP5":
            bp1_data = render_bp5_questions(tier1, "bp1", existing_data)
        elif bp1 == "BP6":
            bp1_data = render_bp6_questions(tier1, "bp1", existing_data)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== BP #2 ====================
    st.markdown('<div class="bp-section">', unsafe_allow_html=True)
    st.markdown("## 📋 Best Practice #2")
    
    bp2_default = existing_data.get('bp2', '')
    bp2_options_list = list(BP_OPTIONS.keys())
    bp2_default_index = bp2_options_list.index(bp2_default) if bp2_default in bp2_options_list else 0
    
    bp2 = st.selectbox("Select the second Best Practice *", 
                       bp2_options_list, 
                       format_func=lambda x: BP_OPTIONS[x], 
                       key="bp2",
                       index=bp2_default_index)
    
    bp2_data = {}
    if bp2 and bp2 != "":
        st.markdown(f"### 🎯 {TIER_DESCRIPTIONS[bp2]['name']}")
        
        for t in [1, 2, 3]:
            with st.expander(f"📖 {TIER_DESCRIPTIONS[bp2][t]['title']}", expanded=False):
                st.text(TIER_DESCRIPTIONS[bp2][t]['description'])
        
        tier2_default = int(existing_data.get('bp2_tier', 1)) if existing_data.get('bp2_tier') else 1
        tier2 = st.radio("Select the highest tier you plan to report *", 
                        [1, 2, 3], 
                        format_func=lambda x: f"Tier {x}", 
                        key="tier2", 
                        horizontal=True,
                        index=tier2_default - 1)
        
        st.markdown("---")
        st.markdown("### 📝 Questions")
        
        if bp2 == "BP1":
            bp2_data = render_bp1_questions(tier2, "bp2", existing_data)
        elif bp2 == "BP2":
            bp2_data = render_bp2_questions(tier2, "bp2", existing_data)
        elif bp2 == "BP3":
            bp2_data = render_bp3_questions(tier2, "bp2", existing_data)
        elif bp2 == "BP4":
            bp2_data = render_bp4_questions(tier2, "bp2", existing_data)
        elif bp2 == "BP5":
            bp2_data = render_bp5_questions(tier2, "bp2", existing_data)
        elif bp2 == "BP6":
            bp2_data = render_bp6_questions(tier2, "bp2", existing_data)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== SUBMIT ====================
    st.markdown("---")
    
    submit_label = "💾 Update Survey" if st.session_state.edit_mode else "✅ Submit Survey"
    
    if st.button(submit_label):
        # Build submission data dictionary
        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'hospital_name': selected_hospital,
            'contact_name': contact_name,
            'email': email,
            'phone': phone,
            'bp1': bp1,
            'bp1_tier': tier1 if bp1 else None,
            'bp2': bp2,
            'bp2_tier': tier2 if bp2 else None,
            'approved': 'False',  # Reset approval when editing
            'approved_by': '',
            'approved_at': ''
        }
        
        # Add BP-specific data
        data.update(bp1_data)
        data.update(bp2_data)
        
        # Save/Update in Google Sheets (updates existing row if hospital exists)
        with st.spinner("Saving to Google Sheets..."):
            success = append_row_to_sheets(data)  # Actually updates the row now
        
        if success:
            # Send email notification to hospital
            with st.spinner("Sending email confirmation..."):
                email_sent = send_submission_email(
                    recipient_email=email,
                    hospital_name=selected_hospital,
                    contact_name=contact_name,
                    submission_data=data
                )
            
            if email_sent:
                st.success("📧 Confirmation email sent!")
            
            st.session_state.just_submitted = True
            st.session_state.edit_mode = False
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("❌ Failed to save submission. Please try again.")

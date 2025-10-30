import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="HSCRC Best Practices Survey",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
</style>
""", unsafe_allow_html=True)

# ==================== CONSTANTS ====================
DATA_FILE = "hscrc_survey_submissions.csv"

HOSPITALS = [
    "Adventist White Oak", "Ascension St Agnes", "Atlantic General", "Calvert Health",
    "Carroll Hospital Center", "Christiana Care-Union Hospital", "Fort Washington",
    "Frederick Health", "Garrett Regional", "GBMC", "Holy Cross Germantown",
    "Holy Cross Silver Spring", "Johns Hopkins Bayview", "Johns Hopkins Hospital",
    "Johns Hopkins Howard County", "Luminis Anne Arundel Medical Ctr", "Luminis Health-Doctors",
    "Medstar Franklin Square", "Medstar Good Samaritan", "Medstar Harbor", "Medstar Montgomery",
    "Medstar Southern Maryland", "Medstar St Mary's", "Medstar Union Memorial",
    "Mercy Medical Center", "Meritus", "Northwest", "Shady Grove", "Sinai", "Suburban",
    "Tidal Health", "UM BWMC", "UM Capital Region Medical Center", "UM Charles Regional",
    "UM Shore Regional", "UM St Joseph Medical Center", "UM Upper Chesapeake",
    "UMMC Downtown", "UMMC-Midtown", "UPMC Western Maryland", "Other"
]

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

# ==================== QUESTION RENDERERS ====================

def render_bp1_questions(tier, prefix):
    """BP1: Interdisciplinary Rounds - CUMULATIVE KPI checkboxes"""
    st.markdown("### Select the KPIs you plan to achieve: *")
    
    data = {}
    
    # Tier 1 KPIs (always shown)
    kpi1 = st.checkbox("70% of inpatient admissions have documented discharge planning", key=f"{prefix}_kpi1")
    kpi2 = st.checkbox("10% improvement from baseline" if tier == 1 else "10% improvement from baseline of above KPI", key=f"{prefix}_kpi2")
    
    # Tier 2 KPIs (shown for tier 2 and 3)
    kpi3 = kpi4 = False
    if tier >= 2:
        kpi3 = st.checkbox("50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge", key=f"{prefix}_kpi3")
        kpi4 = st.checkbox("10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN", key=f"{prefix}_kpi4")
    
    # Tier 3 KPIs (shown only for tier 3) - NOTE: These are shown but NO target/actual is collected!
    kpi5 = kpi6 = False
    if tier >= 3:
        kpi5 = st.checkbox("75% of adult inpatients that have screened positive for HRSN are given referrals to community resources prior to discharge", key=f"{prefix}_kpi5")
        kpi6 = st.checkbox("10% improvement from baseline of all positive screens for HRSN are given a referral prior to discharge identified from tier two", key=f"{prefix}_kpi6")
    
    st.markdown("---")
    
    # Collect target/actual ONLY for KPIs 1-4 (not for 5-6 even in Tier 3)
    if kpi1:
        st.markdown(f"**Provide the target KPI if you selected, \"70% of inpatient admissions have documented discharge planning.\" {'*' if tier == 3 else ''}**")
        data[f'{prefix}_kpi1_target'] = st.text_input("Target:", key=f"{prefix}_kpi1_target")
        st.markdown("**Provide the actual KPI performance results if you selected, \"70% of inpatient admissions have documented discharge planning.\"**")
        data[f'{prefix}_kpi1_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi1_actual")
    
    if kpi2:
        kpi2_text = "10% improvement from baseline" if tier == 1 else "10% improvement from baseline of above KPI"
        st.markdown(f"**Provide the target KPI if you selected, \"{kpi2_text}.\"**")
        data[f'{prefix}_kpi2_target'] = st.text_input("Target:", key=f"{prefix}_kpi2_target")
        st.markdown(f"**Provide the actual KPI performance results if you selected, \"{kpi2_text}.\"**")
        data[f'{prefix}_kpi2_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi2_actual")
    
    if kpi3:
        st.markdown("**Provide the target KPI if you selected, \"50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge.\"**")
        data[f'{prefix}_kpi3_target'] = st.text_input("Target:", key=f"{prefix}_kpi3_target")
        st.markdown("**Provide the actual KPI performance results if you selected, \"50% of adult inpatients were offered screening for the 5 (five) HRSN prior to discharge.\"**")
        data[f'{prefix}_kpi3_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi3_actual")
    
    if kpi4:
        st.markdown("**Provide the target KPI if you selected, \"10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN.\"**")
        data[f'{prefix}_kpi4_target'] = st.text_input("Target:", key=f"{prefix}_kpi4_target")
        st.markdown("**Provide the actual KPI performance results if you selected, \"10% improvement from baseline of all inpatients identified in tier one offered screening for HRSN.\"**")
        data[f'{prefix}_kpi4_actual'] = st.text_input("Actual:", key=f"{prefix}_kpi4_actual")
    
    # NOTE: KPIs 5 and 6 are shown as checkboxes in Tier 3, but NO target/actual questions are asked for them
    # This matches the specifications exactly
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

def render_bp2_questions(tier, prefix):
    """BP2: Bed Capacity Alert System - CUMULATIVE"""
    st.markdown("### Tier 1: Capacity Metrics")
    st.markdown("**Describe the one or more capacity metrics your organization selected to achieve tier 1: ***")
    
    data = {}
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
    data[f'{prefix}_t1_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 1 *", key=f"{prefix}_t1_target")
    data[f'{prefix}_t1_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 1 *", key=f"{prefix}_t1_actual")
    
    if tier >= 2:
        st.markdown("### Tier 2: Bed Capacity Alert Process")
        data[f'{prefix}_t2_surge'] = st.text_area("Describe the established bed capacity alert process (aka surge plan) driven by capacity metrics *", key=f"{prefix}_t2_surge", height=150)
        data[f'{prefix}_t2_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 2 *", key=f"{prefix}_t2_target")
        data[f'{prefix}_t2_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 2 *", key=f"{prefix}_t2_actual")
    
    if tier >= 3:
        st.markdown("### Tier 3: Demonstrate Activation")
        data[f'{prefix}_t3_quant'] = st.text_area("Describe the process to achieve tier 3, when an organization quantitatively demonstrates consistent activation of surge plans *", key=f"{prefix}_t3_quant", height=150)
        data[f'{prefix}_t3_target'] = st.text_input("Provide the target metric for your chosen capacity metric to achieve tier 3 *", key=f"{prefix}_t3_target")
        data[f'{prefix}_t3_actual'] = st.text_input("Provide the actual target metric performance results to achieve tier 3 *", key=f"{prefix}_t3_actual")
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

def render_bp3_questions(tier, prefix):
    """BP3: Standardized Daily Shift Huddles - CUMULATIVE"""
    data = {}
    
    st.markdown("### Tier 1: Daily Huddles")
    data[f'{prefix}_t1_kpi'] = st.text_area("Provide the KPI chosen to achieve tier 1 *", key=f"{prefix}_t1_kpi", height=100)
    data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 1 *", key=f"{prefix}_t1_actual", height=100)
    
    if tier >= 2:
        st.markdown("### Tier 2: Standardized Infrastructure")
        data[f'{prefix}_t2_kpi'] = st.text_area("Provide the KPI chosen to achieve tier 2 *", key=f"{prefix}_t2_kpi", height=100)
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 2 *", key=f"{prefix}_t2_actual", height=100)
    
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
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the KPI formula chosen to achieve tier 3 *", key=f"{prefix}_t3_formula", height=100)
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the actual KPI performance results to achieve tier 3 *", key=f"{prefix}_t3_actual", height=100)
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

def render_bp4_questions(tier, prefix):
    """BP4: Expedited Care Intervention"""
    practices = ["Nurse Expediter", "Discharge Lounge", "Observation Unit (ED or hospital based)", 
                 "Provider Screening in Triage / Early Provider Screening Process", 
                 "Dedicated CM and/or SW resources in the ED"]
    
    data = {}
    
    if tier == 1:
        st.markdown("### Tier 1: Select ONE Expedited Care Practice")
        data[f'{prefix}_practice'] = st.radio("Select the expedited care practice you plan to report *", practices, key=f"{prefix}_practice")
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for this practice *", key=f"{prefix}_t1_formula", height=100)
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance results *", key=f"{prefix}_t1_actual", height=100)
    
    elif tier == 2:
        st.markdown("### Tier 2: Select TWO Expedited Care Practices")
        selected = st.multiselect("Select two expedited care practices *", practices, key=f"{prefix}_practices")
        data[f'{prefix}_practices'] = ", ".join(selected)
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for first practice *", key=f"{prefix}_t1_formula", height=100)
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance for first practice *", key=f"{prefix}_t1_actual", height=100)
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the KPI formula for second practice *", key=f"{prefix}_t2_formula", height=100)
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance for second practice *", key=f"{prefix}_t2_actual", height=100)
    
    elif tier == 3:
        st.markdown("### Tier 3: Select THREE Expedited Care Practices")
        selected = st.multiselect("Select three expedited care practices *", practices, key=f"{prefix}_practices")
        data[f'{prefix}_practices'] = ", ".join(selected)
        data[f'{prefix}_t1_formula'] = st.text_area("Provide the KPI formula for first practice *", key=f"{prefix}_t1_formula", height=100)
        data[f'{prefix}_t1_actual'] = st.text_area("Provide the actual KPI performance for first practice *", key=f"{prefix}_t1_actual", height=100)
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the KPI formula for second practice *", key=f"{prefix}_t2_formula", height=100)
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the actual KPI performance for second practice *", key=f"{prefix}_t2_actual", height=100)
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the KPI formula for third practice *", key=f"{prefix}_t3_formula", height=100)
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the actual KPI performance for third practice *", key=f"{prefix}_t3_actual", height=100)
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

def render_bp5_questions(tier, prefix):
    """BP5: Patient Flow Throughput Performance Council - CUMULATIVE with all checkboxes"""
    data = {}
    
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
    data[f'{prefix}_t1_formula'] = st.text_area("Provide the target measures' formula to achieve tier 1 *", key=f"{prefix}_t1_formula", height=100)
    data[f'{prefix}_t1_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 1 *", key=f"{prefix}_t1_actual", height=100)
    data[f'{prefix}_improvements'] = st.text_area("Describe any throughput improvements measured after implementing this best practice *", key=f"{prefix}_improvements", height=100)
    
    if tier >= 2:
        st.markdown("### Tier 2: Establish Accountability")
        st.markdown("**Select the accountable measure(s) you plan to report: ***")
        measures2 = []
        # Include Tier 1 options
        if st.checkbox("Committee/council scheduled monthly at minimum (T2)", key=f"{prefix}_t2_monthly"):
            measures2.append("Monthly committee")
        # Tier 2 specific options
        if st.checkbox("Committee meetings include regular report outs", key=f"{prefix}_t2_reportouts"):
            measures2.append("Report outs")
        if st.checkbox("Report outs include executive participation", key=f"{prefix}_t2_exec"):
            measures2.append("Executive participation")
        if st.checkbox("Team develops and works on capacity and throughput projects (T2)", key=f"{prefix}_t2_projects"):
            measures2.append("Throughput projects")
        if st.checkbox("KPIs are evidence-based", key=f"{prefix}_t2_evidence"):
            measures2.append("Evidence-based KPIs")
        if st.checkbox("Other (Tier 2)", key=f"{prefix}_t2_other_check"):
            other = st.text_input("Describe other Tier 2 measure *", key=f"{prefix}_t2_other")
            measures2.append(f"Other: {other}")
        
        data[f'{prefix}_t2_measures'] = ", ".join(measures2)
        data[f'{prefix}_t2_formula'] = st.text_area("Provide the target measures' formula to achieve tier 2 *", key=f"{prefix}_t2_formula", height=100)
        data[f'{prefix}_t2_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 2 *", key=f"{prefix}_t2_actual", height=100)
    
    if tier >= 3:
        st.markdown("### Tier 3: Change Culture")
        st.markdown("**Select the accountable measure(s) you plan to report: ***")
        measures3 = []
        # Include Tier 1 options
        if st.checkbox("Committee/council scheduled monthly at minimum (T3)", key=f"{prefix}_t3_monthly"):
            measures3.append("Monthly committee")
        # Include Tier 2 options
        if st.checkbox("Committee meetings include regular report outs (T3)", key=f"{prefix}_t3_reportouts"):
            measures3.append("Report outs")
        if st.checkbox("Report outs include executive participation (T3)", key=f"{prefix}_t3_exec"):
            measures3.append("Executive participation")
        if st.checkbox("Team develops and works on capacity and throughput projects (T3)", key=f"{prefix}_t3_projects"):
            measures3.append("Throughput projects")
        # Tier 3 specific options
        if st.checkbox("Committee ensures routine capacity/throughput huddles", key=f"{prefix}_t3_huddles"):
            measures3.append("Routine huddles")
        if st.checkbox("Committee ensures observation protocols", key=f"{prefix}_t3_obs"):
            measures3.append("Observation protocols")
        if st.checkbox("KPIs are evidence-based (T3)", key=f"{prefix}_t3_evidence"):
            measures3.append("Evidence-based KPIs")
        if st.checkbox("KPIs reported for key units/service lines", key=f"{prefix}_t3_units"):
            measures3.append("KPIs for units")
        if st.checkbox("Other (Tier 3)", key=f"{prefix}_t3_other_check"):
            other = st.text_input("Describe other Tier 3 measure *", key=f"{prefix}_t3_other")
            measures3.append(f"Other: {other}")
        
        data[f'{prefix}_t3_measures'] = ", ".join(measures3)
        data[f'{prefix}_t3_formula'] = st.text_area("Provide the target measures' formula to achieve tier 3 *", key=f"{prefix}_t3_formula", height=100)
        data[f'{prefix}_t3_actual'] = st.text_area("Provide the target measures' actual performance results to achieve tier 3 *", key=f"{prefix}_t3_actual", height=100)
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

def render_bp6_questions(tier, prefix):
    """BP6: Clinical Pathways & Observation Management - CUMULATIVE"""
    data = {}
    
    st.markdown("### Tier 1: Design and Implement")
    data[f'{prefix}_t1_pathway'] = st.text_area("Describe the clinical pathway that was selected and implemented to achieve tier 1 *", key=f"{prefix}_t1_pathway", height=150)
    
    if tier >= 2:
        st.markdown("### Tier 2: Develop Data Infrastructure")
        data[f'{prefix}_t2_data'] = st.text_area("Describe the data collection and analysis systems to monitor and evaluate outcomes that were selected and implemented to achieve tier 2 *", key=f"{prefix}_t2_data", height=150)
    
    if tier >= 3:
        st.markdown("### Tier 3: Demonstrate Improvement")
        data[f'{prefix}_t3_improvement'] = st.text_area("Describe the measurable decrease in unwarranted clinical variation and/or measurable improvement in outcomes specific to your chosen intervention to achieve tier 3 *", key=f"{prefix}_t3_improvement", height=150)
    
    # Rationale and Success Stories (for all tiers)
    st.markdown("---")
    data[f'{prefix}_rationale'] = st.text_area("Provide the rationale to why you selected this best practice & tier *", key=f"{prefix}_rationale", height=150)
    data[f'{prefix}_success'] = st.text_area("Are there any success stories and/or barriers to implementing this best practice? *", key=f"{prefix}_success", height=150)
    
    return data

# ==================== INITIALIZE SESSION STATE ====================
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# ==================== MAIN APP ====================
if not st.session_state.submitted:
    
    st.markdown("# 🏥 HSCRC Best Practices Survey")
    st.markdown("### Please complete all sections below. You will select TWO best practices to report.")
    st.markdown("---")
    
    # ========== HOSPITAL INFO ==========
    st.markdown("## 🏥 Hospital Information")
    
    hospital_selection = st.selectbox("Select your hospital's name from the list *", options=HOSPITALS)
    hospital_other = ""
    if hospital_selection == "Other":
        hospital_other = st.text_input("Please specify your hospital name *")
    
    col1, col2 = st.columns(2)
    with col1:
        contact_name = st.text_input("Contact Name *")
    with col2:
        email = st.text_input("Email Address *")
    
    phone = st.text_input("Phone Number *")
    st.markdown("---")
    
    # ==================== BP #1 ====================
    st.markdown('<div class="bp-section">', unsafe_allow_html=True)
    st.markdown("## 📋 Best Practice #1")
    
    bp1 = st.selectbox("Select the first Best Practice *", list(BP_OPTIONS.keys()), format_func=lambda x: BP_OPTIONS[x], key="bp1")
    
    bp1_data = {}
    if bp1 and bp1 != "":
        st.markdown(f"### 🎯 {TIER_DESCRIPTIONS[bp1]['name']}")
        
        for t in [1, 2, 3]:
            with st.expander(f"📖 {TIER_DESCRIPTIONS[bp1][t]['title']}", expanded=False):
                st.text(TIER_DESCRIPTIONS[bp1][t]['description'])
        
        tier1 = st.radio("Select the highest tier you plan to report *", [1, 2, 3], format_func=lambda x: f"Tier {x}", key="tier1", horizontal=True)
        
        st.markdown("---")
        st.markdown("### 📝 Questions")
        
        if bp1 == "BP1":
            bp1_data = render_bp1_questions(tier1, "bp1")
        elif bp1 == "BP2":
            bp1_data = render_bp2_questions(tier1, "bp1")
        elif bp1 == "BP3":
            bp1_data = render_bp3_questions(tier1, "bp1")
        elif bp1 == "BP4":
            bp1_data = render_bp4_questions(tier1, "bp1")
        elif bp1 == "BP5":
            bp1_data = render_bp5_questions(tier1, "bp1")
        elif bp1 == "BP6":
            bp1_data = render_bp6_questions(tier1, "bp1")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== BP #2 ====================
    st.markdown('<div class="bp-section">', unsafe_allow_html=True)
    st.markdown("## 📋 Best Practice #2")
    
    bp2 = st.selectbox("Select the second Best Practice *", list(BP_OPTIONS.keys()), format_func=lambda x: BP_OPTIONS[x], key="bp2")
    
    bp2_data = {}
    if bp2 and bp2 != "":
        st.markdown(f"### 🎯 {TIER_DESCRIPTIONS[bp2]['name']}")
        
        for t in [1, 2, 3]:
            with st.expander(f"📖 {TIER_DESCRIPTIONS[bp2][t]['title']}", expanded=False):
                st.text(TIER_DESCRIPTIONS[bp2][t]['description'])
        
        tier2 = st.radio("Select the highest tier you plan to report *", [1, 2, 3], format_func=lambda x: f"Tier {x}", key="tier2", horizontal=True)
        
        st.markdown("---")
        st.markdown("### 📝 Questions")
        
        if bp2 == "BP1":
            bp2_data = render_bp1_questions(tier2, "bp2")
        elif bp2 == "BP2":
            bp2_data = render_bp2_questions(tier2, "bp2")
        elif bp2 == "BP3":
            bp2_data = render_bp3_questions(tier2, "bp2")
        elif bp2 == "BP4":
            bp2_data = render_bp4_questions(tier2, "bp2")
        elif bp2 == "BP5":
            bp2_data = render_bp5_questions(tier2, "bp2")
        elif bp2 == "BP6":
            bp2_data = render_bp6_questions(tier2, "bp2")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== SUBMIT ====================
    st.markdown("---")
    
    if st.button("✅ Submit Survey"):
        hospital_final = hospital_other if hospital_selection == "Other" else hospital_selection
        
        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'hospital_name': hospital_final,
            'contact_name': contact_name,
            'email': email,
            'phone': phone,
            'bp1': bp1,
            'bp1_tier': tier1 if bp1 else None,
            'bp2': bp2,
            'bp2_tier': tier2 if bp2 else None
        }
        
        data.update(bp1_data)
        data.update(bp2_data)
        
        df_new = pd.DataFrame([data])
        
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, df_new], ignore_index=True)
        else:
            df = df_new
        
        df.to_csv(DATA_FILE, index=False)
        
        st.session_state.submitted = True
        st.rerun()

else:
    st.success("## ✅ Survey Submitted Successfully!")
    st.markdown("### Thank you for your submission!")
    
    if st.button("Submit Another Response"):
        st.session_state.submitted = False
        st.rerun()

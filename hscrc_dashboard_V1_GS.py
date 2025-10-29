# ==================== 1. IMPORTS (FIRST) ====================
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Import Google Sheets connector
from google_sheets_connector import load_data_from_sheets

# ==================== 2. SET_PAGE_CONFIG (MUST BE HERE!) ====================
st.set_page_config(
    page_title="HSCRC Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 3. CONFIGURATION ====================

# HSCRC Staff credentials
HSCRC_STAFF = {
    "lisa": "hscrc2025",
    "tina": "hscrc2025",
    "admin": "hscrc2025"
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
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA FUNCTIONS ====================
@st.cache_data(ttl=60)
def load_data():
    """Load data from Google Sheets"""
    df = load_data_from_sheets()
    
    if df.empty:
        st.warning("⚠️ No submissions found in Google Sheets yet.")
        st.info("Hospitals can submit data using the Survey app, and it will appear here automatically!")
        st.stop()
    
    return df


# ==================== LOGIN SYSTEM ====================
with st.sidebar:
    st.markdown("### 🔐 HSCRC Staff Login")
    st.markdown("---")
    
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    login_button = st.button("🔓 Login", use_container_width=True)
    
    if login_button:
        if username in HSCRC_STAFF and password == HSCRC_STAFF[username]:
            st.session_state['hscrc_logged_in'] = True
            st.session_state['staff_name'] = username.title()
            st.success(f"✅ Welcome back, {username.title()}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    
    st.markdown("---")
    st.markdown("**Demo Credentials:**")
    st.markdown("- **Username:** lisa or tina")
    st.markdown("- **Password:** hscrc2025")
    
    # Logout button if logged in
    if 'hscrc_logged_in' in st.session_state and st.session_state['hscrc_logged_in']:
        st.markdown("---")
        st.markdown(f"**Logged in as:** {st.session_state['staff_name']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ==================== CHECK LOGIN ====================
if 'hscrc_logged_in' not in st.session_state or not st.session_state['hscrc_logged_in']:
    st.markdown('<div class="main-header">📊 HSCRC Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Maryland Best Practice Survey - Internal Analytics</div>', unsafe_allow_html=True)
    st.info("👈 HSCRC Staff: Please login using the sidebar")
    st.markdown("---")
    st.markdown("#### About This Dashboard")
    st.markdown("""
    This internal dashboard provides HSCRC staff with:
    - 📊 **Analytics & Insights** across all hospital submissions
    - 🔍 **Interactive Filtering** by hospital, best practice, and tier
    - 🗺️ **Heatmap Visualizations** showing tier patterns
    - 📈 **Drill-Down Tables** for detailed analysis
    - 📤 **Export Capabilities** for reporting
    
    **Restricted Access:** This dashboard is for authorized HSCRC staff only.
    """)
    st.stop()

# ==================== MAIN DASHBOARD (AFTER LOGIN) ====================
# Load data
df = load_data()

# Header
st.markdown('<div class="main-header">📊 HSCRC Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Welcome, {st.session_state["staff_name"]}!</div>', unsafe_allow_html=True)
st.markdown("---")

# ==================== OVERVIEW METRICS ====================
st.markdown("## 📈 Overview Metrics")

col1, col2, col3, col4 = st.columns(4)

total_hospitals = len(df['hospital_name'].unique())
total_submissions = len(df)

# Count BPs reported - each submission has 2 BPs
total_bp_selections = total_submissions * 2

# Most common BP (check both bp1 and bp2)
all_bps = []
if 'bp1' in df.columns:
    all_bps.extend(df['bp1'].dropna().tolist())
if 'bp2' in df.columns:
    all_bps.extend(df['bp2'].dropna().tolist())

if all_bps:
    from collections import Counter
    bp_counts = Counter(all_bps)
    primary_bp_mode = bp_counts.most_common(1)[0][0] if bp_counts else 'N/A'
    primary_bp_mode = BP_NAMES.get(primary_bp_mode, primary_bp_mode)
else:
    primary_bp_mode = 'N/A'

with col1:
    st.metric("Total Hospitals", total_hospitals)

with col2:
    st.metric("Total Submissions", total_submissions)

with col3:
    st.metric("BP Selections", total_bp_selections)

with col4:
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;">
            <div style="color: #666; font-size: 0.8rem; margin-bottom: 0.25rem;">Top Primary BP</div>
            <div style="color: #1f4788; font-size: 1.2rem; font-weight: 600;">{primary_bp_mode[:25]}...</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== INTERACTIVE FILTERS ====================
st.markdown("## 🔍 Interactive Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    filter_hospitals = st.multiselect(
        "Filter by Hospital:",
        options=sorted(df['hospital_name'].unique()),
        default=[]
    )

with filter_col2:
    # Get all unique BPs from bp1 and bp2
    all_bps_unique = set()
    if 'bp1' in df.columns:
        all_bps_unique.update(df['bp1'].dropna().unique())
    if 'bp2' in df.columns:
        all_bps_unique.update(df['bp2'].dropna().unique())
    
    # Map to full names for display
    bp_options = sorted([BP_NAMES.get(bp, bp) for bp in all_bps_unique])
    
    filter_bps = st.multiselect(
        "Filter by Best Practice:",
        options=bp_options,
        default=[]
    )

with filter_col3:
    filter_tiers = st.multiselect(
        "Filter by Tier:",
        options=[1, 2, 3],
        default=[]
    )

# Apply filters
filtered_df = df.copy()
if filter_hospitals:
    filtered_df = filtered_df[filtered_df['hospital_name'].isin(filter_hospitals)]

if filter_bps or filter_tiers:
    # Convert full names back to codes for filtering
    bp_codes = [code for code, name in BP_NAMES.items() if name in filter_bps]
    
    # Filter by BP/Tier combinations
    mask = pd.Series([False] * len(filtered_df))
    
    # Check bp1
    bp1_mask = pd.Series([True] * len(filtered_df))
    if bp_codes:
        bp1_mask = bp1_mask & filtered_df['bp1'].isin(bp_codes)
    if filter_tiers:
        bp1_mask = bp1_mask & filtered_df['bp1_tier'].isin(filter_tiers)
    
    # Check bp2
    bp2_mask = pd.Series([True] * len(filtered_df))
    if bp_codes:
        bp2_mask = bp2_mask & filtered_df['bp2'].isin(bp_codes)
    if filter_tiers:
        bp2_mask = bp2_mask & filtered_df['bp2_tier'].isin(filter_tiers)
    
    # Include row if either bp1 or bp2 matches
    mask = bp1_mask | bp2_mask
    filtered_df = filtered_df[mask]

st.info(f"📊 Showing {len(filtered_df)} of {len(df)} submissions")

st.markdown("---")

# ==================== VISUALIZATIONS ====================
st.markdown("## 📊 Visual Analytics")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # BP Popularity Chart
    st.markdown("**Best Practice Popularity**")
    
    # Count BPs from bp1 and bp2, but ONLY if they match the filter criteria
    all_bp_codes = []
    
    # Convert BP filter names back to codes
    bp_codes_filter = [code for code, name in BP_NAMES.items() if name in filter_bps] if filter_bps else []
    
    for _, row in filtered_df.iterrows():
        # Check bp1
        if pd.notna(row.get('bp1')):
            include_bp1 = True
            # If BP filter is active, check if bp1 matches
            if bp_codes_filter:
                include_bp1 = row['bp1'] in bp_codes_filter
            # If Tier filter is active, check if bp1_tier matches
            if filter_tiers and include_bp1:
                include_bp1 = row.get('bp1_tier') in filter_tiers
            
            if include_bp1:
                all_bp_codes.append(row['bp1'])
        
        # Check bp2
        if pd.notna(row.get('bp2')):
            include_bp2 = True
            # If BP filter is active, check if bp2 matches
            if bp_codes_filter:
                include_bp2 = row['bp2'] in bp_codes_filter
            # If Tier filter is active, check if bp2_tier matches
            if filter_tiers and include_bp2:
                include_bp2 = row.get('bp2_tier') in filter_tiers
            
            if include_bp2:
                all_bp_codes.append(row['bp2'])
    
    if all_bp_codes:
        from collections import Counter
        bp_counts = Counter(all_bp_codes)
        
        # Map to full names
        bp_labels = [BP_NAMES.get(code, code) for code in bp_counts.keys()]
        
        fig_bp_pop = px.bar(
            x=bp_labels,
            y=list(bp_counts.values()),
            labels={'x': 'Best Practice', 'y': 'Number of Selections'},
            title="Which Best Practices Are Most Popular?"
        )
        fig_bp_pop.update_traces(marker_color='#1f4788')
        fig_bp_pop.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_bp_pop, use_container_width=True)
    else:
        st.info("No BP data in filtered results")

with viz_col2:
    # Tier Distribution
    st.markdown("**Tier Distribution Across All BPs**")
    
    # Collect tiers, but ONLY for BPs that match the filter criteria
    all_tiers = []
    
    # Convert BP filter names back to codes
    bp_codes_filter = [code for code, name in BP_NAMES.items() if name in filter_bps] if filter_bps else []
    
    for _, row in filtered_df.iterrows():
        # Check bp1
        if pd.notna(row.get('bp1')) and pd.notna(row.get('bp1_tier')):
            include_bp1 = True
            # If BP filter is active, check if bp1 matches
            if bp_codes_filter:
                include_bp1 = row['bp1'] in bp_codes_filter
            # If Tier filter is active, check if bp1_tier matches
            if filter_tiers and include_bp1:
                include_bp1 = row['bp1_tier'] in filter_tiers
            
            if include_bp1:
                all_tiers.append(row['bp1_tier'])
        
        # Check bp2
        if pd.notna(row.get('bp2')) and pd.notna(row.get('bp2_tier')):
            include_bp2 = True
            # If BP filter is active, check if bp2 matches
            if bp_codes_filter:
                include_bp2 = row['bp2'] in bp_codes_filter
            # If Tier filter is active, check if bp2_tier matches
            if filter_tiers and include_bp2:
                include_bp2 = row['bp2_tier'] in filter_tiers
            
            if include_bp2:
                all_tiers.append(row['bp2_tier'])
    
    if all_tiers:
        from collections import Counter
        tier_counts = Counter(all_tiers)
        
        # Sort by tier number
        tier_counts = dict(sorted(tier_counts.items()))
        
        # Color map for tiers
        colors = []
        for tier in tier_counts.keys():
            if tier == 1:
                colors.append('#28a745')
            elif tier == 2:
                colors.append('#ffc107')
            elif tier == 3:
                colors.append('#dc3545')
            else:
                colors.append('#6c757d')
        
        tier_labels = [f"Tier {t}" for t in tier_counts.keys()]
        
        fig_tier_dist = px.pie(
            values=list(tier_counts.values()),
            names=tier_labels,
            title="Overall Tier Selection Distribution",
            color_discrete_sequence=colors
        )
        st.plotly_chart(fig_tier_dist, use_container_width=True)
    else:
        st.info("No tier data in filtered results")

st.markdown("---")

# ==================== BP × TIER MATRIX ====================
st.markdown("## 🗺️ Best Practice × Tier Matrix")
st.markdown("See which tiers are selected for each best practice")

# Build matrix data
matrix_data = []

# Convert BP filter names back to codes
bp_codes_filter = [code for code, name in BP_NAMES.items() if name in filter_bps] if filter_bps else []

# Process bp1
if 'bp1' in filtered_df.columns and 'bp1_tier' in filtered_df.columns:
    for _, row in filtered_df.iterrows():
        if pd.notna(row['bp1']) and pd.notna(row['bp1_tier']):
            include_bp1 = True
            # If BP filter is active, check if bp1 matches
            if bp_codes_filter:
                include_bp1 = row['bp1'] in bp_codes_filter
            # If Tier filter is active, check if bp1_tier matches
            if filter_tiers and include_bp1:
                include_bp1 = row['bp1_tier'] in filter_tiers
            
            if include_bp1:
                matrix_data.append({
                    'BP': BP_NAMES.get(row['bp1'], row['bp1']),
                    'Tier': f"Tier {row['bp1_tier']}",
                    'Hospital': row['hospital_name']
                })

# Process bp2
if 'bp2' in filtered_df.columns and 'bp2_tier' in filtered_df.columns:
    for _, row in filtered_df.iterrows():
        if pd.notna(row['bp2']) and pd.notna(row['bp2_tier']):
            include_bp2 = True
            # If BP filter is active, check if bp2 matches
            if bp_codes_filter:
                include_bp2 = row['bp2'] in bp_codes_filter
            # If Tier filter is active, check if bp2_tier matches
            if filter_tiers and include_bp2:
                include_bp2 = row['bp2_tier'] in filter_tiers
            
            if include_bp2:
                matrix_data.append({
                    'BP': BP_NAMES.get(row['bp2'], row['bp2']),
                    'Tier': f"Tier {row['bp2_tier']}",
                    'Hospital': row['hospital_name']
                })

if matrix_data:
    matrix_df = pd.DataFrame(matrix_data)
    
    # Count occurrences
    heatmap_counts = matrix_df.groupby(['BP', 'Tier']).size().reset_index(name='Count')
    pivot_df = heatmap_counts.pivot(index='BP', columns='Tier', values='Count').fillna(0)
    
    # Create heatmap
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='Blues',
        text=pivot_df.values,
        texttemplate='%{text}',
        textfont={"size": 12},
        hovertemplate='BP: %{y}<br>Tier: %{x}<br>Count: %{z}<extra></extra>'
    ))
    
    fig_heatmap.update_layout(
        title="Best Practice × Tier Selection Matrix",
        xaxis_title="Tier",
        yaxis_title="Best Practice",
        height=max(400, len(pivot_df) * 50)
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info("No data to display in matrix")

st.markdown("---")

# ==================== HOSPITAL DETAIL TABLE ====================
st.markdown("## 📋 Hospital Submissions Detail")

# Build detail table
detail_data = []
for _, row in filtered_df.iterrows():
    hospital = row['hospital_name']
    timestamp = row.get('timestamp', 'N/A')
    
    # Get BP details
    bp_details = []
    
    if pd.notna(row.get('bp1')) and row.get('bp1') != '':
        bp1_name = BP_NAMES.get(row['bp1'], row['bp1'])
        bp1_tier = row.get('bp1_tier', '')
        bp_details.append(f"{bp1_name} (Tier {bp1_tier})")
    
    if pd.notna(row.get('bp2')) and row.get('bp2') != '':
        bp2_name = BP_NAMES.get(row['bp2'], row['bp2'])
        bp2_tier = row.get('bp2_tier', '')
        bp_details.append(f"{bp2_name} (Tier {bp2_tier})")
    
    detail_data.append({
        'Hospital': hospital,
        'Submission Date': timestamp,
        'Total BPs Reported': len(bp_details),
        'BP Details': ' | '.join(bp_details) if bp_details else 'None'
    })

if detail_data:
    detail_df = pd.DataFrame(detail_data)
    
    # Add a truncated version for display and keep full version for hover
    detail_df['BP Details (Click to expand)'] = detail_df['BP Details'].apply(
        lambda x: x[:80] + '...' if len(x) > 80 else x
    )
    
    st.dataframe(
        detail_df[['Hospital', 'Submission Date', 'Total BPs Reported', 'BP Details (Click to expand)']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "BP Details (Click to expand)": st.column_config.TextColumn(
                "BP Details (Click to expand)",
                width="large",
                help="Click on a cell to see the full details"
            )
        }
    )
    
    # Show a more readable expandable view
    with st.expander("📋 View Full BP Details (All Rows)"):
        for idx, row in detail_df.iterrows():
            st.markdown(f"**{row['Hospital']}** ({row['Submission Date']})")
            st.markdown(f"→ {row['BP Details']}")
            st.markdown("---")
    
    # Download button for filtered data
    csv_detail = detail_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=csv_detail,
        file_name=f"filtered_submissions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.info("No data matches the current filters")

st.markdown("---")

# ==================== COMPLIANCE INSIGHTS ====================
st.markdown("## 💡 Compliance Insights")

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    # Hospitals with most BPs
    st.markdown("**Top 5 Hospitals by BP Count**")
    hospital_bp_counts = []
    for hospital in filtered_df['hospital_name'].unique():
        hosp_data = filtered_df[filtered_df['hospital_name'] == hospital].iloc[-1]
        bp_count = 0
        if pd.notna(hosp_data.get('bp1')) and hosp_data.get('bp1') != '':
            bp_count += 1
        if pd.notna(hosp_data.get('bp2')) and hosp_data.get('bp2') != '':
            bp_count += 1
        hospital_bp_counts.append({'Hospital': hospital, 'BP Count': bp_count})
    
    if hospital_bp_counts:
        top_hospitals = pd.DataFrame(hospital_bp_counts).nlargest(5, 'BP Count')
        st.dataframe(top_hospitals, hide_index=True, use_container_width=True)

with insight_col2:
    # Most common tier selections
    st.markdown("**Most Common Tier Selections**")
    tier_frequency = {}
    
    for _, row in filtered_df.iterrows():
        if pd.notna(row.get('bp1_tier')):
            tier = f"Tier {row['bp1_tier']}"
            tier_frequency[tier] = tier_frequency.get(tier, 0) + 1
        if pd.notna(row.get('bp2_tier')):
            tier = f"Tier {row['bp2_tier']}"
            tier_frequency[tier] = tier_frequency.get(tier, 0) + 1
    
    if tier_frequency:
        tier_freq_df = pd.DataFrame(
            list(tier_frequency.items()),
            columns=['Tier', 'Frequency']
        ).sort_values('Frequency', ascending=False)
        st.dataframe(tier_freq_df, hide_index=True, use_container_width=True)

st.markdown("---")

# ==================== DATA SOURCE INFO ====================
st.markdown("## ⚙️ Data Source & Refresh")

col_info1, col_info2 = st.columns(2)

with col_info1:
    st.info(f"**Data File:** `hscrc_survey_submissions.csv`")

with col_info2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data refreshed!")
        st.rerun()

st.markdown("---")

# Footer
st.markdown("##### Maryland Health Services Cost Review Commission - Internal Analytics Dashboard")
st.markdown(f"*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")

# ==================== 1. IMPORTS (FIRST) ====================
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

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
    """Load data from local CSV in clean format"""
    import os
    
    # Load clean CSV
    if os.path.exists('hospital_data.csv'):
        df = pd.read_csv('hospital_data.csv')
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Hospital_Name'])
        return df
    else:
        st.error("❌ Cannot find hospital_data.csv")
        st.info("Please ensure the hospital_data.csv file is in the same directory as this app.")
        st.stop()


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

total_hospitals = len(df['Hospital_Name'].unique())
total_submissions = len(df)

# Count BPs reported - in clean format, each submission has exactly 2 BPs
total_bp_selections = total_submissions * 2

# Most common BP (check both BP1 and BP2)
all_bps = []
if 'BP1_Name' in df.columns:
    all_bps.extend(df['BP1_Name'].dropna().tolist())
if 'BP2_Name' in df.columns:
    all_bps.extend(df['BP2_Name'].dropna().tolist())

if all_bps:
    from collections import Counter
    bp_counts = Counter(all_bps)
    primary_bp_mode = bp_counts.most_common(1)[0][0] if bp_counts else 'N/A'
    # Shorten BP name for display
    primary_bp_mode = primary_bp_mode.replace('Best Practice ', 'BP ')
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
            <div style="color: #1f4788; font-size: 1.2rem; font-weight: 600;">{primary_bp_mode[:30]}...</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== INTERACTIVE FILTERS ====================
st.markdown("## 🔍 Interactive Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    filter_hospitals = st.multiselect(
        "Filter by Hospital:",
        options=sorted(df['Hospital_Name'].unique()),
        default=[]
    )

with filter_col2:
    # Get all unique BPs from BP1_Name and BP2_Name
    all_bps = set()
    if 'BP1_Name' in df.columns:
        all_bps.update(df['BP1_Name'].dropna().unique())
    if 'BP2_Name' in df.columns:
        all_bps.update(df['BP2_Name'].dropna().unique())
    
    filter_bps = st.multiselect(
        "Filter by Best Practice:",
        options=sorted(all_bps),
        default=[]
    )

with filter_col3:
    # Get all unique tiers from BP1_Tier and BP2_Tier
    all_tiers = set()
    if 'BP1_Tier' in df.columns:
        all_tiers.update(df['BP1_Tier'].dropna().unique())
    if 'BP2_Tier' in df.columns:
        all_tiers.update(df['BP2_Tier'].dropna().unique())
    
    filter_tiers = st.multiselect(
        "Filter by Tier:",
        options=sorted(all_tiers),
        default=[]
    )

# Apply filters
filtered_df = df.copy()
if filter_hospitals:
    filtered_df = filtered_df[filtered_df['Hospital_Name'].isin(filter_hospitals)]

if filter_bps or filter_tiers:
    # Filter by BP/Tier combinations
    mask = pd.Series([False] * len(filtered_df))
    
    # Check BP1
    bp1_mask = pd.Series([True] * len(filtered_df))
    if filter_bps:
        bp1_mask = bp1_mask & filtered_df['BP1_Name'].isin(filter_bps)
    if filter_tiers:
        bp1_mask = bp1_mask & filtered_df['BP1_Tier'].isin(filter_tiers)
    
    # Check BP2
    bp2_mask = pd.Series([True] * len(filtered_df))
    if filter_bps:
        bp2_mask = bp2_mask & filtered_df['BP2_Name'].isin(filter_bps)
    if filter_tiers:
        bp2_mask = bp2_mask & filtered_df['BP2_Tier'].isin(filter_tiers)
    
    # Include row if either BP1 or BP2 matches
    mask = bp1_mask | bp2_mask
    filtered_df = filtered_df[mask]

st.info(f"📊 Showing {len(filtered_df)} of {len(df)} submissions")

st.markdown("---")

# ==================== VISUALIZATIONS ====================
st.markdown("## 📊 Analytics & Insights")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # BP Popularity Chart
    st.markdown("**Best Practice Popularity**")
    
    # Count BPs from BP1_Name and BP2_Name
    all_bp_names = []
    if 'BP1_Name' in filtered_df.columns:
        all_bp_names.extend(filtered_df['BP1_Name'].dropna().tolist())
    if 'BP2_Name' in filtered_df.columns:
        all_bp_names.extend(filtered_df['BP2_Name'].dropna().tolist())
    
    if all_bp_names:
        from collections import Counter
        bp_counts = Counter(all_bp_names)
        
        # Shorten BP names for display
        bp_labels = [name.replace('Best Practice ', 'BP ') for name in bp_counts.keys()]
        
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
    
    # Collect all tiers from BP1_Tier and BP2_Tier
    all_tiers = []
    if 'BP1_Tier' in filtered_df.columns:
        all_tiers.extend(filtered_df['BP1_Tier'].dropna().tolist())
    if 'BP2_Tier' in filtered_df.columns:
        all_tiers.extend(filtered_df['BP2_Tier'].dropna().tolist())
    
    if all_tiers:
        from collections import Counter
        tier_counts = Counter(all_tiers)
        
        # Color map for tiers
        colors = []
        for tier in tier_counts.keys():
            if 'One' in tier or 'Full' in tier:
                colors.append('#28a745')
            elif 'Two' in tier or 'Partial' in tier:
                colors.append('#ffc107')
            else:
                colors.append('#dc3545')
        
        fig_tier_dist = px.pie(
            values=list(tier_counts.values()),
            names=list(tier_counts.keys()),
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

# Build matrix data from clean CSV
matrix_data = []

# Process BP1
if 'BP1_Name' in filtered_df.columns and 'BP1_Tier' in filtered_df.columns:
    for _, row in filtered_df.iterrows():
        if pd.notna(row['BP1_Name']) and pd.notna(row['BP1_Tier']):
            matrix_data.append({
                'BP': row['BP1_Name'].replace('Best Practice ', 'BP '),
                'Tier': row['BP1_Tier'],
                'Hospital': row['Hospital_Name']
            })

# Process BP2
if 'BP2_Name' in filtered_df.columns and 'BP2_Tier' in filtered_df.columns:
    for _, row in filtered_df.iterrows():
        if pd.notna(row['BP2_Name']) and pd.notna(row['BP2_Tier']):
            matrix_data.append({
                'BP': row['BP2_Name'].replace('Best Practice ', 'BP '),
                'Tier': row['BP2_Tier'],
                'Hospital': row['Hospital_Name']
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
        height=max(400, len(pivot_df) * 40)
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
    hospital = row['Hospital_Name']
    timestamp = row.get('Timestamp', 'N/A')
    
    # Count BPs for this hospital
    bp_count = 0
    bp_list = []
    for i in range(1, 14):
        tier = row.get(f'BP{i}_Tier')
        if pd.notna(tier) and str(tier).strip() not in ('', 'None', 'nan'):
            bp_count += 1
            bp_list.append(f"BP{i}:{tier}")
    
    detail_data.append({
        'Hospital': hospital,
        'Submission Date': timestamp,
        'Total BPs Reported': bp_count,
        'BP Details': ', '.join(bp_list) if bp_list else 'None'
    })

if detail_data:
    detail_df = pd.DataFrame(detail_data)
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "BP Details": st.column_config.TextColumn(
                "BP Details",
                width="large"
            )
        }
    )
    
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
    for hospital in filtered_df['Hospital_Name'].unique():
        hosp_data = filtered_df[filtered_df['Hospital_Name'] == hospital].iloc[-1]
        bp_count = sum([
            1 for i in range(1, 14)
            if pd.notna(hosp_data.get(f'BP{i}_Tier')) and 
            str(hosp_data.get(f'BP{i}_Tier')).strip() not in ('', 'None', 'nan')
        ])
        hospital_bp_counts.append({'Hospital': hospital, 'BP Count': bp_count})
    
    if hospital_bp_counts:
        top_hospitals = pd.DataFrame(hospital_bp_counts).nlargest(5, 'BP Count')
        st.dataframe(top_hospitals, hide_index=True, use_container_width=True)

with insight_col2:
    # Most common tier selections
    st.markdown("**Most Common Tier Selections**")
    tier_frequency = {}
    for i in range(1, 14):
        bp_col = f'BP{i}_Tier'
        if bp_col in filtered_df.columns:
            for tier in filtered_df[bp_col].dropna():
                tier_str = str(tier)
                if tier_str.strip() and tier_str not in ('None', 'nan'):
                    tier_frequency[tier_str] = tier_frequency.get(tier_str, 0) + 1
    
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
    st.info(f"**Google Sheet ID:** `{SHEET_ID}`")

with col_info2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data refreshed!")
        st.rerun()

st.markdown("---")

# Footer
st.markdown("##### Maryland Health Services Cost Review Commission - Internal Analytics Dashboard")
st.markdown(f"*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")

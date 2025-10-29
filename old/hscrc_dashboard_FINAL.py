import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="HSCRC Analytics Dashboard",
    page_icon="📊",
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
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# ==================== AUTHENTICATION ====================
st.sidebar.title("🔒 HSCRC Staff Login")

# Demo credentials
STAFF_CREDS = {
    "lisa": "hscrc2025",
    "tina": "hscrc2025"
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

if not st.session_state.authenticated:
    username = st.sidebar.text_input("Username:")
    password = st.sidebar.text_input("Password:", type="password")
    
    if st.sidebar.button("🔓 Login"):
        if username in STAFF_CREDS and password == STAFF_CREDS[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Demo Credentials:**")
    st.sidebar.markdown("• **Username:** lisa or tina")
    st.sidebar.markdown("• **Password:** hscrc2025")
    st.stop()

# User is authenticated
st.sidebar.success(f"Logged in as: {st.session_state.username.title()}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
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

# ==================== MAIN DASHBOARD ====================
st.markdown('<div class="main-header">📊 HSCRC Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align: center; color: #666; font-size: 1.2rem;">Welcome, {st.session_state.username.title()}!</p>', unsafe_allow_html=True)

if df.empty:
    st.error("⚠️ No data found! Please ensure hospital_data.csv exists.")
    st.stop()

st.markdown("---")

# ==================== OVERVIEW METRICS ====================
st.markdown("## 📈 Overview Metrics")

col1, col2, col3, col4 = st.columns(4)

total_hospitals = df['Hospital_Name'].nunique()
total_submissions = len(df)
bp_selections = total_submissions * 2  # Each submission has 2 BPs

# Get most common BP
all_bps = list(df['BP1_Name']) + list(df['BP2_Name'])
bp_counts = pd.Series(all_bps).value_counts()
top_bp = bp_counts.index[0] if len(bp_counts) > 0 else "N/A"

with col1:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="metric-label">Total Hospitals</div>
        <div class="metric-value">{total_hospitals}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div class="metric-label">Total Submissions</div>
        <div class="metric-value">{total_submissions}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="metric-label">BP Selections</div>
        <div class="metric-value">{bp_selections}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Shorten BP name for display
    top_bp_short = top_bp.replace('Best Practice ', 'BP ')
    if len(top_bp_short) > 30:
        top_bp_short = top_bp_short[:27] + "..."
    
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="metric-label">Top Primary BP</div>
        <div class="metric-value" style="font-size: 1.2rem;">{top_bp_short}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== INTERACTIVE FILTERS ====================
st.markdown("## 🔍 Interactive Filters")

col1, col2, col3 = st.columns(3)

with col1:
    hospital_filter = st.selectbox(
        "Filter by Hospital:",
        options=["All"] + sorted(df['Hospital_Name'].unique().tolist())
    )

with col2:
    all_bp_names = sorted(list(set(df['BP1_Name'].tolist() + df['BP2_Name'].tolist())))
    bp_filter = st.selectbox(
        "Filter by Best Practice:",
        options=["All"] + all_bp_names
    )

with col3:
    all_tiers = sorted(list(set(df['BP1_Tier'].tolist() + df['BP2_Tier'].tolist())))
    tier_filter = st.selectbox(
        "Filter by Tier:",
        options=["All"] + all_tiers
    )

# Apply filters
filtered_df = df.copy()

if hospital_filter != "All":
    filtered_df = filtered_df[filtered_df['Hospital_Name'] == hospital_filter]

if bp_filter != "All":
    filtered_df = filtered_df[(filtered_df['BP1_Name'] == bp_filter) | (filtered_df['BP2_Name'] == bp_filter)]

if tier_filter != "All":
    filtered_df = filtered_df[(filtered_df['BP1_Tier'] == tier_filter) | (filtered_df['BP2_Tier'] == tier_filter)]

st.info(f"📊 Showing {len(filtered_df)} of {len(df)} submissions")

st.markdown("---")

# ==================== ANALYTICS & INSIGHTS ====================
st.markdown("## 📊 Analytics & Insights")

col1, col2 = st.columns(2)

with col1:
    # Best Practice Distribution
    st.markdown("### Best Practice Distribution")
    bp_data = []
    for _, row in df.iterrows():
        bp_data.append(row['BP1_Name'])
        bp_data.append(row['BP2_Name'])
    
    bp_counts = pd.Series(bp_data).value_counts()
    
    fig = px.bar(
        x=bp_counts.values,
        y=[bp.replace('Best Practice ', 'BP ') for bp in bp_counts.index],
        orientation='h',
        title="Best Practice Selection Count",
        labels={'x': 'Count', 'y': 'Best Practice'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Tier Distribution
    st.markdown("### Tier Distribution")
    tier_data = []
    for _, row in df.iterrows():
        tier_data.append(row['BP1_Tier'])
        tier_data.append(row['BP2_Tier'])
    
    tier_counts = pd.Series(tier_data).value_counts()
    
    colors = {
        'Tier One (Full Implementation)': '#28a745',
        'Tier Two (Partial Implementation)': '#ffc107',
        'Tier Three (Planning/Early Stages)': '#dc3545'
    }
    
    fig = px.pie(
        values=tier_counts.values,
        names=tier_counts.index,
        title="Implementation Tier Breakdown",
        color=tier_counts.index,
        color_discrete_map=colors
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==================== DETAILED SUBMISSIONS TABLE ====================
st.markdown("## 📋 Detailed Submissions")

# Create display dataframe
display_df = filtered_df.copy()
display_df = display_df[['Timestamp', 'Hospital_Name', 'Contact_Name', 'Contact_Email', 
                         'BP1_Name', 'BP1_Tier', 'BP2_Name', 'BP2_Tier']]

# Shorten BP names for display
display_df['BP1_Name'] = display_df['BP1_Name'].str.replace('Best Practice ', 'BP ')
display_df['BP2_Name'] = display_df['BP2_Name'].str.replace('Best Practice ', 'BP ')

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# ==================== EXPORT FUNCTIONALITY ====================
st.markdown("---")
st.markdown("## 📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download CSV",
        data=csv,
        file_name=f"hscrc_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    # Excel export placeholder
    st.button("📊 Export to Excel", disabled=True, help="Coming soon!")

with col3:
    st.button("📑 Generate Report", disabled=True, help="Coming soon!")

st.markdown("---")

# ==================== SUCCESS STORIES & BARRIERS ====================
st.markdown("## 💡 Success Stories & Barriers")

# Collect all notes
notes_data = []
for _, row in df.iterrows():
    if row['BP1_Notes']:
        notes_data.append({
            'Hospital': row['Hospital_Name'],
            'Best Practice': row['BP1_Name'],
            'Tier': row['BP1_Tier'],
            'Notes': row['BP1_Notes']
        })
    if row['BP2_Notes']:
        notes_data.append({
            'Hospital': row['Hospital_Name'],
            'Best Practice': row['BP2_Name'],
            'Tier': row['BP2_Tier'],
            'Notes': row['BP2_Notes']
        })

if notes_data:
    with st.expander(f"View All Notes ({len(notes_data)} total)"):
        for note in notes_data:
            st.markdown(f"""
            **{note['Hospital']}** - {note['Best Practice'].replace('Best Practice ', 'BP ')}
            
            *Tier:* {note['Tier']}
            
            *Notes:* {note['Notes']}
            
            ---
            """)
else:
    st.info("No notes have been submitted yet.")

st.markdown("---")
st.markdown("##### Maryland Health Services Cost Review Commission (HSCRC)")
st.markdown("*ED Throughput Best Practices Initiative - October 2025*")

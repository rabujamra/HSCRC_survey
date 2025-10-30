"""
Modified Google Sheets connector with UPDATE instead of APPEND
Each hospital has ONE row that gets updated
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Google Sheets configuration
SPREADSHEET_NAME = "HSCRC Survey Submissions"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_google_sheets_connection():
    """
    Establish connection to Google Sheets using service account credentials.
    This connection is cached and reused across the app.
    """
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
        st.stop()

def get_worksheet():
    """Get the active worksheet from the Google Sheet."""
    try:
        client = get_google_sheets_connection()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.sheet1
        return worksheet
    except Exception as e:
        st.error(f"❌ Error accessing worksheet: {str(e)}")
        st.stop()

def load_data_from_sheets():
    """Load all data from Google Sheets as a pandas DataFrame."""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        
        if not records:
            return pd.DataFrame(columns=[
                'timestamp', 'hospital_name', 'contact_name', 'email', 'phone',
                'bp1', 'bp1_tier', 'bp2', 'bp2_tier',
                'bp1_rationale', 'bp1_success', 'bp2_rationale', 'bp2_success',
                'approved', 'approved_by', 'approved_at'
            ])
        
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error loading data from Google Sheets: {str(e)}")
        return pd.DataFrame()

def save_or_update_submission(hospital_name, data_dict):
    """
    Save or update a hospital's submission.
    If hospital exists, UPDATE the row.
    If hospital doesn't exist, APPEND a new row.
    
    Args:
        hospital_name: Name of the hospital
        data_dict: Dictionary containing all submission data
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        worksheet = get_worksheet()
        
        # Get all data
        all_records = worksheet.get_all_records()
        headers = worksheet.row_values(1)
        
        # If no headers exist, create them
        if not headers or headers == ['']:
            headers = list(data_dict.keys())
            worksheet.update('A1', [headers])
            all_records = []
        
        # Find existing row for this hospital
        hospital_row_index = None
        for idx, record in enumerate(all_records):
            if record.get('hospital_name') == hospital_name:
                hospital_row_index = idx + 2  # +2 because: +1 for 0-index, +1 for header row
                break
        
        # Prepare row values in header order
        row_values = []
        for header in headers:
            value = data_dict.get(header, '')
            if value is None:
                value = ''
            row_values.append(str(value))
        
        if hospital_row_index is not None:
            # UPDATE existing row
            range_notation = f'A{hospital_row_index}'
            worksheet.update(range_notation, [row_values], value_input_option='USER_ENTERED')
            return True
        else:
            # APPEND new row (first submission for this hospital)
            worksheet.append_row(row_values, value_input_option='USER_ENTERED')
            return True
    
    except Exception as e:
        st.error(f"❌ Error saving to Google Sheets: {str(e)}")
        st.error(f"Data that failed to save: {data_dict.get('hospital_name', 'Unknown')}")
        return False

# Keep these for backwards compatibility
def append_row_to_sheets(data_dict):
    """Backwards compatibility - now calls save_or_update_submission"""
    hospital_name = data_dict.get('hospital_name')
    return save_or_update_submission(hospital_name, data_dict)

def get_spreadsheet_url():
    """Get the URL of the connected Google Sheet."""
    try:
        client = get_google_sheets_connection()
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.url
    except:
        return None

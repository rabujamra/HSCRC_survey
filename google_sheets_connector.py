"""
Shared Google Sheets connection module for HSCRC Survey System
This module is used by all three apps: Survey, Portal, and Dashboard
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
        # Get credentials from Streamlit secrets
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        
        # Authorize and return gspread client
        client = gspread.authorize(credentials)
        return client
    
    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
        st.info("""
        **Setup Required:**
        1. Create a Google Cloud service account
        2. Download the JSON key file
        3. Add it to Streamlit secrets as `gcp_service_account`
        4. Share your Google Sheet with the service account email
        
        See GOOGLE_SHEETS_SETUP_INSTRUCTIONS.md for detailed steps.
        """)
        st.stop()


def get_worksheet():
    """
    Get the active worksheet from the Google Sheet.
    Returns the first worksheet (Sheet1).
    """
    try:
        client = get_google_sheets_connection()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.sheet1  # Get first worksheet
        return worksheet
    
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ Google Sheet '{SPREADSHEET_NAME}' not found!")
        st.info("""
        **Make sure:**
        1. Your Google Sheet is named exactly: `HSCRC Survey Submissions`
        2. You've shared it with your service account email
        3. The service account has Editor permissions
        """)
        st.stop()
    
    except Exception as e:
        st.error(f"❌ Error accessing worksheet: {str(e)}")
        st.stop()


def load_data_from_sheets():
    """
    Load all data from Google Sheets as a pandas DataFrame.
    This is used by Portal and Dashboard apps.
    """
    try:
        worksheet = get_worksheet()
        
        # Get all records as list of dictionaries
        records = worksheet.get_all_records()
        
        if not records:
            # If sheet is empty, return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'timestamp', 'hospital_name', 'contact_name', 'email', 'phone',
                'bp1', 'bp1_tier', 'bp2', 'bp2_tier',
                'bp1_rationale', 'bp1_success', 'bp2_rationale', 'bp2_success'
            ])
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error loading data from Google Sheets: {str(e)}")
        return pd.DataFrame()


def append_row_to_sheets(data_dict):
    """
    Append a new row of data to Google Sheets.
    This is used by the Survey app when a hospital submits.
    
    Args:
        data_dict: Dictionary containing all submission data
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        worksheet = get_worksheet()
        
        # Get existing headers
        headers = worksheet.row_values(1)
        
        # If no headers exist, create them from the data_dict keys
        if not headers or headers == ['']:
            headers = list(data_dict.keys())
            worksheet.update('A1', [headers])
        
        # Create row values in the same order as headers
        row_values = []
        for header in headers:
            # Get value from data_dict, use empty string if not present
            value = data_dict.get(header, '')
            # Convert None to empty string
            if value is None:
                value = ''
            row_values.append(str(value))
        
        # Append the row
        worksheet.append_row(row_values, value_input_option='USER_ENTERED')
        
        return True
    
    except Exception as e:
        st.error(f"❌ Error saving to Google Sheets: {str(e)}")
        st.error(f"Data that failed to save: {data_dict.get('hospital_name', 'Unknown')}")
        return False


def initialize_sheet_headers():
    """
    Initialize the Google Sheet with proper column headers if they don't exist.
    This should be run once during initial setup.
    """
    try:
        worksheet = get_worksheet()
        
        # Check if headers already exist
        existing_headers = worksheet.row_values(1)
        if existing_headers and existing_headers[0] != '':
            return  # Headers already exist
        
        # Define default headers
        headers = [
            'timestamp', 'hospital_name', 'contact_name', 'email', 'phone',
            'bp1', 'bp1_tier', 'bp1_rationale', 'bp1_success',
            'bp2', 'bp2_tier', 'bp2_rationale', 'bp2_success'
        ]
        
        # Add headers to first row
        worksheet.update('A1', [headers])
        
        st.success("✅ Google Sheet headers initialized!")
    
    except Exception as e:
        st.error(f"❌ Error initializing headers: {str(e)}")


# Helper function to get spreadsheet URL
def get_spreadsheet_url():
    """
    Get the URL of the connected Google Sheet.
    Useful for providing a link to HSCRC staff.
    """
    try:
        client = get_google_sheets_connection()
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.url
    except:
        return None

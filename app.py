# -*- coding:utf-8 -*-
"""
Created on Tue. Mar. 19 14:30:00 2024
@author: JUN-SU PARK

This script implements a Streamlit-based web interface for the GenomicsPACS-Linker that:
1. Displays a searchable and sortable list of patient studies
2. Provides filtering by Patient ID and Study Date
3. Enables direct launching of X-ray and CT viewers
4. Implements pagination for better performance with large datasets
5. Communicates with a Flask backend API to handle viewer requests
"""

# Standard library imports
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# Custom styling including logo area and UI components
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0c3e;  /* Dark blue background */
        color: white;
    }
    .logo-container {
        background-color: #0a1157;  /* Slightly darker blue for logo area */
        padding: 1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid #1a1f4c;
    }
    .logo-text {
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }
    .logo-subtext {
        color: white;
        font-size: 1.2rem;
        opacity: 0.9;
        margin-top: 5px;
    }
    /* Expander styling for study list */
    div[data-testid="stExpander"] {
        background-color: #0b0c3e;
        border: none;
        margin: -0.9rem 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stExpanderContent"] {
        background-color: #1a1f4c;
        padding: 10px;
    }
    /* Button styling */
    button[kind="secondary"] {
        width: 100% !important;
        height: 38px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div.stButton > button {
        margin-top: 0px;
    }
    /* Layout adjustments */
    div[data-testid="stExpanderContent"] div.row-widget.stHorizontal {
        gap: 0.5rem !important;
    }
    div[data-testid="stExpanderContent"] .stButton button {
        width: 100% !important;
        margin: 0 !important;
        display: block !important;
    }
    .streamlit-expanderHeader {
        padding: 0.5rem !important;
    }
    /* Pagination styling */
    .pagination {
        margin-top: 2rem;
        padding: 1rem;
        background-color: #1a1f4c;
        border-radius: 5px;
        text-align: center;
    }
    </style>
    
    <div class="logo-container">
        <p class="logo-text">BMC</p>
        <p class="logo-subtext">GenomicsPACS-Linker</p>
    </div>
""", unsafe_allow_html=True)

# Application title
st.title("Study List")

@st.cache_data
def load_data(file_path):
    """
    Load and cache patient study data from CSV file
    
    Args:
        file_path (str): Path to the CSV file containing patient study information
        
    Returns:
        pd.DataFrame: Processed DataFrame with formatted study dates
    """
    df = pd.read_csv(file_path)
    # Convert Study_Date format to YYYY-MM-DD
    df['Study_Date'] = pd.to_datetime(df['Study_Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
    return df

def send_to_api(patient_id, study_date, modality):
    """
    Send study information to backend API for viewer launching
    
    Args:
        patient_id (str): Patient's unique identifier
        study_date (str): Date of the study in YYYY-MM-DD format
        modality (str): Type of imaging study (X-ray or CT)
        
    Returns:
        dict: Response containing status and optional error message
    """
    api_url = "http://localhost:8000/api/viewer"
    
    payload = {
        "patient_id": patient_id,
        "study_date": study_date,
        "modality": modality
    }
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        elif response.status_code == 404:
            error_data = response.json()
            return {"status": "error", "message": error_data.get('message', 'Study not found')}
        else:
            return {"status": "error", "message": "Failed to retrieve study information"}
            
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Failed to connect to server"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": "Failed to retrieve study information"}

def main():
    """
    Main application function that handles:
    - Data loading and caching
    - Search and filter functionality
    - Sorting implementation
    - Pagination logic
    - UI rendering
    - Viewer launch requests
    """
    # Initialize session state for sorting
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'Study_Date'
        st.session_state.sort_ascending = True
    
    # Load data if not already in session state
    if 'df' not in st.session_state:
        st.session_state.df = load_data('patient_info.csv')

    # Search filters UI
    col1, col2 = st.columns(2)
    with col1:
        patient_search = st.text_input("Search Patient ID")
    with col2:
        date_search = st.text_input("Search Study Date (YYYY-MM-DD)")

    # Sortable column headers
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            f"Patient ID {'↑' if st.session_state.sort_column == 'Patient_ID' and st.session_state.sort_ascending else '↓' if st.session_state.sort_column == 'Patient_ID' else ''}",
            key="sort_patient_id"
        ):
            if st.session_state.sort_column == 'Patient_ID':
                st.session_state.sort_ascending = not st.session_state.sort_ascending
            else:
                st.session_state.sort_column = 'Patient_ID'
                st.session_state.sort_ascending = True

    with col2:
        if st.button(
            f"Study Date {'↑' if st.session_state.sort_column == 'Study_Date' and st.session_state.sort_ascending else '↓' if st.session_state.sort_column == 'Study_Date' else ''}",
            key="sort_study_date"
        ):
            if st.session_state.sort_column == 'Study_Date':
                st.session_state.sort_ascending = not st.session_state.sort_ascending
            else:
                st.session_state.sort_column = 'Study_Date'
                st.session_state.sort_ascending = True

    # Apply filters and sorting
    filtered_df = st.session_state.df.copy()
    if patient_search:
        filtered_df = filtered_df[filtered_df['Patient_ID'].str.contains(patient_search, case=False)]
    if date_search:
        filtered_df = filtered_df[filtered_df['Study_Date'].str.contains(date_search, case=False)]

    filtered_df = filtered_df.sort_values(
        by=st.session_state.sort_column,
        ascending=st.session_state.sort_ascending
    )

    # Pagination setup
    items_per_page = 20
    total_pages = len(filtered_df) // items_per_page + (1 if len(filtered_df) % items_per_page > 0 else 0)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Calculate current page's data range
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_df = filtered_df.iloc[start_idx:end_idx]

    # Display study list with expandable rows
    for idx, row in page_df.iterrows():
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            patient_text = row['Patient_ID']
        with exp_col2:
            date_text = row['Study_Date']
        
        # Expandable row with viewer buttons
        with st.expander(f":blue[{patient_text}]{'　'*20}{date_text}"):
            col1, col_space, col2 = st.columns([1, 0.00001, 1])
            
            # X-ray viewer button
            with col1:
                if st.button("Open X-ray Viewer", key=f"xray_{idx}", type="primary"):
                    result = send_to_api(
                        patient_id=row['Patient_ID'],
                        study_date=row['Study_Date'],
                        modality="X-ray"
                    )
                    if result["status"] == "success":
                        st.success("X-ray viewer request sent successfully")
                    else:
                        st.error(result["message"])
            
            # CT viewer button
            with col2:
                if st.button("Open CT Viewer", key=f"ct_{idx}", type="primary"):
                    result = send_to_api(
                        patient_id=row['Patient_ID'],
                        study_date=row['Study_Date'],
                        modality="CT"
                    )
                    if result["status"] == "success":
                        st.success("CT viewer request sent successfully")
                    else:
                        st.error(result["message"])

    # Pagination UI
    st.markdown('<div class="pagination">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        st.session_state.current_page = st.number_input(
            'Page',
            min_value=1,
            max_value=max(1, total_pages),
            value=st.session_state.current_page
        )
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
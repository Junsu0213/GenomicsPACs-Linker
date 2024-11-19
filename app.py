import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# Custom styling including logo area
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0c3e;
        color: white;
    }
    .logo-container {
        background-color: #0a1157;
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
    div[data-testid="stExpander"] {
        background-color: #0b0c3e;
        border: none;
    }
    div[data-testid="stExpanderContent"] {
        background-color: #1a1f4c;
        padding: 10px;
    }
    button[kind="secondary"] {
        width: 100% !important;
        height: 38px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div.stButton > button {
        margin-top: 0px;
    }
    div[data-testid="stExpanderContent"] div.row-widget.stHorizontal {
        gap: 0.5rem !important;
    }
    
    div[data-testid="stExpanderContent"] .stButton button {
        width: 100% !important;
        margin: 0 !important;
        display: block !important;
    }
    div[data-testid="stExpander"] {
        margin: -0.9rem 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    .streamlit-expanderHeader {
        padding: 0.5rem !important;
    }
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

st.title("Study List")

@st.cache_data
def load_data(file_path):
    """Load and cache the CSV data"""
    df = pd.read_csv(file_path)
    # Study_Date 형식 변환
    df['Study_Date'] = pd.to_datetime(df['Study_Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
    return df

def send_to_api(patient_id, study_date, modality):
    """Send data to API and handle response"""
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
            # API에서 반환된 에러 메시지 사용
            error_data = response.json()
            return {"status": "error", "message": error_data.get('message', 'Study not found')}
        else:
            return {"status": "error", "message": "Failed to retrieve study information"}
            
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Failed to connect to server"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": "Failed to retrieve study information"}

def main():
    # Initialize session state
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'Study_Date'
        st.session_state.sort_ascending = True
    
    # 실제 데이터 로드
    if 'df' not in st.session_state:
        st.session_state.df = load_data('patient_info.csv')

    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        patient_search = st.text_input("Search Patient ID")
    with col2:
        date_search = st.text_input("Search Study Date (YYYY-MM-DD)")

    # Clickable column headers
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

    # Filter and sort data
    filtered_df = st.session_state.df.copy()
    if patient_search:
        filtered_df = filtered_df[filtered_df['Patient_ID'].str.contains(patient_search, case=False)]
    if date_search:
        filtered_df = filtered_df[filtered_df['Study_Date'].str.contains(date_search, case=False)]

    filtered_df = filtered_df.sort_values(
        by=st.session_state.sort_column,
        ascending=st.session_state.sort_ascending
    )

    # 페이지네이션 계산
    items_per_page = 20
    total_pages = len(filtered_df) // items_per_page + (1 if len(filtered_df) % items_per_page > 0 else 0)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_df = filtered_df.iloc[start_idx:end_idx]

    # Display data with expandable rows
    for idx, row in page_df.iterrows():
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            patient_text = row['Patient_ID']
        with exp_col2:
            date_text = row['Study_Date']
        
        with st.expander(f":blue[{patient_text}]{'　'*20}{date_text}"):
            col1, col_space, col2 = st.columns([1, 0.00001, 1])
            
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

    # 페이지네이션 UI (하단에 배치)
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
# -*- coding:utf-8 -*-
"""
Created on Tue. Mar. 19 14:30:00 2024
@author: JUN-SU PARK

This script implements a Flask-based API server that:
1. Handles viewer launch requests from the Streamlit frontend
2. Manages study metadata through a CSV database
3. Generates and opens PACS viewer URLs
4. Provides error handling and status checking endpoints
"""

# Standard library imports
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import webbrowser
from datetime import datetime
import os

# Initialize Flask application and enable CORS
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configuration
VIEWER_HOST = os.environ.get('VIEWER_HOST', '192.168.44.190')

# Global DataFrame for storing patient metadata
df = None

def load_data():
    """
    Load and preprocess patient metadata from CSV file
    
    Global Effects:
        Updates the global DataFrame 'df' with formatted study dates
    """
    global df
    df = pd.read_csv('patient_metainfo.csv')
    # Standardize Study_Date format to YYYY-MM-DD
    df['Study_Date'] = pd.to_datetime(df['Study_Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

# Load data when server starts
load_data()

@app.route('/api/viewer', methods=['POST'])
def handle_viewer_request():
    """
    Handle incoming viewer launch requests
    
    Expected JSON payload:
        patient_id (str): Patient's unique identifier
        study_date (str): Study date in YYYY-MM-DD format
        modality (str): Imaging modality type
        
    Returns:
        JSON response with status and viewer URL or error message
    """
    try:
        # Parse incoming JSON data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'study_date', 'modality']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Extract request parameters
        study_date = data['study_date']
        patient_id = data['patient_id']
        modality = data['modality']

        # Find matching study in database
        matched_row = df[
            (df['Patient_ID'] == patient_id) & 
            (df['Study_Date'] == study_date) &
            (df['Modality'] == modality)
        ]

        # Handle case when no matching study is found
        if matched_row.empty:
            return jsonify({
                'status': 'error',
                'message': 'No matching study found'
            }), 404

        # Get StudyInstanceUID and generate viewer URL using configured host
        study_instance_uid = matched_row.iloc[0]['StudyInstanceUID']
        viewer_url = f"http://{VIEWER_HOST}/segmentation?StudyInstanceUIDs={study_instance_uid}"
        
        # Open viewer in new browser tab
        webbrowser.open_new_tab(viewer_url)

        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Viewer opened successfully',
            'study_instance_uid': study_instance_uid,
            'viewer_url': viewer_url
        }), 200

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to verify API server status
    
    Returns:
        JSON response indicating server health status
    """
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    print(f"Starting API server on http://localhost:8000")
    print(f"Using viewer host: {VIEWER_HOST}")
    app.run(host='localhost', port=8000, debug=True)
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
import sqlite3

# Initialize Flask application and enable CORS
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configuration
VIEWER_HOST = os.environ.get('VIEWER_HOST', '192.168.44.190')

# DataFrame 대신 데이터베이스 연결 함수 사용
def get_db_connection():
    """데이터베이스 연결 생성"""
    conn = sqlite3.connect('genomics_pacs.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/viewer', methods=['POST'])
def handle_viewer_request():
    """뷰어 실행 요청 처리"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['patient_id', 'study_date', 'modality']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # 데이터베이스에서 매칭되는 연구 찾기
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT study_instance_uid
            FROM studies
            WHERE patient_id = ? AND study_date = ? AND modality = ?
        ''', (data['patient_id'], data['study_date'], data['modality']))
        
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({
                'status': 'error',
                'message': 'No matching study found'
            }), 404

        # 뷰어 URL 생성 및 실행
        study_instance_uid = result['study_instance_uid']
        viewer_url = f"http://{VIEWER_HOST}/segmentation?StudyInstanceUIDs={study_instance_uid}"
        
        webbrowser.open_new_tab(viewer_url)

        return jsonify({
            'status': 'success',
            'message': 'Viewer opened successfully',
            'study_instance_uid': study_instance_uid,
            'viewer_url': viewer_url
        }), 200

    except Exception as e:
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
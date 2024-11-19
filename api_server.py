from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import webbrowser
from datetime import datetime

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 전역 변수로 DataFrame 선언
df = None

def load_data():
    """데이터 로드 및 전처리 함수"""
    global df
    df = pd.read_csv('patient_metainfo.csv')
    # Study_Date를 문자열 형식으로 통일
    df['Study_Date'] = pd.to_datetime(df['Study_Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

# 앱 시작 시 데이터 로드
load_data()

@app.route('/api/viewer', methods=['POST'])
def handle_viewer_request():
    try:
        # 클라이언트로부터 JSON 데이터 받기
        data = request.get_json()
        
        # 필수 파라미터 확인
        required_fields = ['patient_id', 'study_date', 'modality']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # 데이터 매칭
        study_date = data['study_date']
        patient_id = data['patient_id']
        modality = data['modality']

        # DataFrame에서 해당 환자와 날짜에 맞는 StudyInstanceUID 찾기
        matched_row = df[
            (df['Patient_ID'] == patient_id) & 
            (df['Study_Date'] == study_date) &
            (df['Modality'] == modality)
        ]

        if matched_row.empty:
            return jsonify({
                'status': 'error',
                'message': 'No matching study found'
            }), 404

        # StudyInstanceUID 가져오기
        study_instance_uid = matched_row.iloc[0]['StudyInstanceUID']

        # PACS 뷰어 URL 생성
        viewer_url = f"http://192.168.44.190/segmentation?StudyInstanceUIDs={study_instance_uid}"
        
        # URL 실행 (새 탭에서 열기)
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

# 서버 상태 확인용 엔드포인트
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    print("Starting API server on http://localhost:8000")
    app.run(host='localhost', port=8000, debug=True)
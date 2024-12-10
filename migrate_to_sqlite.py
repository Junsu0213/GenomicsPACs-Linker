import pandas as pd
import sqlite3
from datetime import datetime
import os

def create_database():
    """데이터베이스와 테이블 생성"""
    # 기존 DB 파일이 있으면 백업
    if os.path.exists('genomics_pacs.db'):
        backup_name = f'genomics_pacs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db.bak'
        os.rename('genomics_pacs.db', backup_name)
        print(f"기존 데이터베이스를 {backup_name}으로 백업했습니다.")

    conn = sqlite3.connect('genomics_pacs.db')
    cursor = conn.cursor()
    
    # studies 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS studies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        study_date DATE NOT NULL,
        modality TEXT,
        study_instance_uid TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(patient_id, study_date, modality)
    )
    ''')
    
    # 인덱스 생성
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_patient_study 
    ON studies(patient_id, study_date, modality)
    ''')
    
    conn.commit()
    return conn

def migrate_data():
    """CSV 파일에서 SQLite로 데이터 마이그레이션"""
    # 데이터베이스 연결
    conn = create_database()
    cursor = conn.cursor()
    
    # patient_metainfo.csv 데이터 로드
    df_meta = pd.read_csv('patient_metainfo.csv')
    
    # 날짜 형식 변환
    df_meta['Study_Date'] = pd.to_datetime(df_meta['Study_Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
    
    # 데이터 삽입
    for _, row in df_meta.iterrows():
        cursor.execute('''
        INSERT INTO studies (patient_id, study_date, modality, study_instance_uid)
        VALUES (?, ?, ?, ?)
        ''', (
            row['Patient_ID'],
            row['Study_Date'],
            row['Modality'],
            row['StudyInstanceUID']
        ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_data()
    print("데이터베이스 마이그레이션이 완료되었습니다.") 
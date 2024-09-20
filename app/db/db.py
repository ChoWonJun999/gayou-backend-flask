import mysql.connector
from .queries import *
from datetime import datetime
from ..config.config import Config
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

def get_db_connection():
    """데이터베이스 연결을 생성하는 함수."""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to the database: {err}")
        return None

def create_table():
    """데이터베이스 테이블을 생성하는 함수."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_PLACES)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database table created successfully.")
    else:
        logger.error("Failed to create database table due to connection error.")

def save_to_db(df):
    """데이터프레임을 데이터베이스에 저장하는 함수."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        for index, row in df.iterrows():
            cursor.execute(INSERT_OR_UPDATE_PLACE, (
                row['contentid'],
                row.get('title', None),
                row.get('addr1', None),
                row.get('areacode', None),
                row.get('cat1', None),
                row.get('cat2', None),
                row.get('cat3', None),
                row.get('mapx', None),
                row.get('mapy', None),
                row.get('overview', None),
                datetime.now()  # 현재 시간을 last_updated에 추가
                # 기존 버전과의 차이점:
                # 기존 코드는 row.get('last_updated', None)으로 데이터프레임에서 가져온 값을 사용.
                # 1번 방법은 항상 현재 시간(datetime.now())을 저장하여,
                # DB에 저장되는 시점을 기록하도록 변경됨.
            ))
        conn.commit()  # 데이터베이스에 변경 사항 커밋
        cursor.close()  # 커서 닫기
        conn.close()  # 연결 닫기
        logger.info("Data successfully saved to the database.")
    else:
        logger.error("Failed to save data to the database due to connection error.")

def execute_query(query, params=None):
    """SQL 쿼리를 실행하는 함수."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as err:
            logger.error(f"Error executing query: {err}")
            cursor.close()
            conn.close()
            return None
    else:
        logger.error("Failed to execute query due to connection error.")
        return None

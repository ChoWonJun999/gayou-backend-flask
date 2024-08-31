import mysql.connector
from datetime import datetime
from .queries import CREATE_PLACES_TABLE, INSERT_OR_UPDATE_PLACE
from .config import Config

# 데이터베이스 연결 설정
db_config = {
    'host': Config.DB_HOST,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
    'database': Config.DB_NAME
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_PLACES_TABLE)
    conn.commit()
    conn.close()

def save_to_db(df):
    conn = get_db_connection()
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute(INSERT_OR_UPDATE_PLACE, (
            row['contentid'], row.get('title', None), row.get('addr1', None), row.get('areacode', None),
            row.get('cat1', None), row.get('cat2', None), row.get('cat3', None),
            row.get('mapx', None), row.get('mapy', None), row.get('overview', None), datetime.now()))
    conn.commit()
    conn.close()

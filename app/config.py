import os
from dotenv import load_dotenv

class Config:
    load_dotenv()
    # 기본 설정
    DEBUG = True
    TESTING = False

    # 공공데이터 API 설정
    BASE_URL = "http://apis.data.go.kr/B551011/KorService1"
    SERVICE_KEY = os.environ['SERVICE_KEY']

    # MySQL 데이터베이스 설정
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_NAME = os.getenv('DB_NAME', 'gayou')

    WERKZEUG_RUN_MAIN = 'true'

    # 스케줄러 설정
    JOBS = [
        {
            'id': 'job1',
            'func': 'app.scheduler:collect_data',
            'trigger': 'interval',
            'weeks': 1
        }
    ]
    SCHEDULER_API_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True
    CORS_ALLOWED_ORIGINS = ["*"]

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CORS_ALLOWED_ORIGINS = ["https://your-frontend-domain.com"]

import os
import secrets
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))

    """기본 설정"""
    DEBUG = True
    TESTING = False

    # 공공데이터 API 설정
    BASE_URL = "http://apis.data.go.kr/B551011/KorService1"
    SERVICE_KEY = os.getenv('SERVICE_KEY', 'your_default_service_key')

    # openAI API 키
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # MySQL 데이터베이스 설정
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_NAME = os.getenv('DB_NAME', 'gayou')

    # Flask 설정
    WERKZEUG_RUN_MAIN = os.getenv('WERKZEUG_RUN_MAIN', 'true')

    # 스케줄러 설정
    JOB_RUN = os.getenv('JOB_RUN', 'False').lower() in ['true', '1', 'yes']
    JOBS = [
        {
            'id': 'job1',
            'func': 'app.scheduler.data_collector.collect_data',  # 수정된 모듈 경로 반영
            'trigger': 'interval',
            'weeks': 1
        }
    ]
    SCHEDULER_API_ENABLED = True

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    CORS_ALLOWED_ORIGINS = ["*"]  # 모든 도메인 허용

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    TESTING = False
    CORS_ALLOWED_ORIGINS = [os.getenv('FRONTEND_DOMAIN', 'https://your-frontend-domain.com')]  # 특정 도메인만 허용

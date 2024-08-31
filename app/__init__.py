# app/__init__.py

from flask import Flask
from flask_cors import CORS
from .db import create_table
from .scheduler import scheduler
from .routes import init_routes
from .config import DevelopmentConfig, ProductionConfig
from .logging_config import setup_logging  # 로그 설정 파일에서 로그 설정 불러오기
import os

def create_app():
    app = Flask(__name__)
    
    # 환경에 따른 설정 로드
    env_config = os.getenv('FLASK_ENV', 'development')
    if env_config == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # 로그 설정
    logger = setup_logging()
    logger.info('Initializing Flask application...')

    try:
        # 테이블 생성
        logger.info('Creating database table...')
        create_table()
        logger.info('Database table created successfully.')

        # CORS 설정: 환경에 따라 허용할 도메인만 허용
        CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ALLOWED_ORIGINS']}})
        
        # 스케줄러를 메인 스레드에서만 시작
        if not app.debug or app.config.get("WERKZEUG_RUN_MAIN") == "true":
            logger.info('Starting scheduler...')
            scheduler.start()
            logger.info('Scheduler started.')

        # 라우트 초기화
        logger.info('Initializing routes...')
        init_routes(app)
        logger.info('Routes initialized successfully.')

    except Exception as e:
        logger.error(f'An error occurred during application initialization: {e}')
    
    return app

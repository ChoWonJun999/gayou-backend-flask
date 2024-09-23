from flask import Flask
from flask_cors import CORS
from .config.config import DevelopmentConfig, ProductionConfig
from .db import create_table
from .logging import setup_logging
from .routes import init_routes
from .scheduler import start_scheduler, stop_scheduler, is_scheduler_running
import os
from .config.config import Config

def create_app():
    """
    Flask 애플리케이션을 생성하고 초기화하는 함수.
    """
    app = Flask(__name__)

    # 환경에 따른 설정 로드
    env_config = os.getenv('FLASK_ENV', 'development')
    if env_config == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # 로그 설정
    logger = setup_logging()

    # CORS 설정: 환경에 따라 허용할 도메인만 허용
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ALLOWED_ORIGINS']}})

    logger.info('Initializing Flask application...')

    try:
        # 데이터베이스 테이블 생성
        logger.info('Creating database table...')
        create_table()
        logger.info('Database table created successfully.')

        if Config.JOB_RUN:
            logger.info('Starting scheduler...')
            start_scheduler()
            logger.info('Scheduler started.')

        # 라우트 초기화
        logger.info('Initializing routes...')
        init_routes(app)
        logger.info('Routes initialized successfully.')

    except Exception as e:
        logger.error(f'An error occurred during application initialization: {e}')

    return app

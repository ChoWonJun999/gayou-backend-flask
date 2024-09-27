from app import create_app
from app.scheduler.scheduler_controller import start_scheduler, stop_scheduler, is_scheduler_running
from dotenv import load_dotenv
from app.logging import setup_logging
import traceback
from app.config.config import Config

# .env 파일 로드
load_dotenv()

# Flask 애플리케이션 생성
app = create_app()

# 로그 설정 (터미널에 로그 기록)
logger = setup_logging()

def main():
    """애플리케이션 메인 실행 함수."""
    
    # 애플리케이션 시작 로그
    logger.info('Starting Flask application...')

    try:
        # Flask 애플리케이션 실행 - 디버그 모드와 reloader 비활성화
        app.run(debug=True, threaded=True, use_reloader=False, host='0.0.0.0', port=5000)
        
    except Exception as e:
        # 오류 메시지와 트레이스백을 로그에 기록
        logger.error(f'An error occurred while running the Flask application: {e}')
        logger.error(traceback.format_exc())
    finally:
        if Config.JOB_RUN:
            # 서버 종료 시 스케줄러 중지
            if is_scheduler_running():
                stop_scheduler()
                logger.info('Flask application has stopped.')

if __name__ == '__main__':
    if Config.JOB_RUN:
        # 스케줄러가 실행 중인지 확인하고, 메인 스레드에서만 실행
        if not is_scheduler_running():
            start_scheduler()
            logger.info('Scheduler started in main process.')
        else:
            logger.info('Scheduler is already running or not in the main thread.')

    main()

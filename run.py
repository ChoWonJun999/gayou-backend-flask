from app import create_app
import logging

# Flask 애플리케이션 생성
app = create_app()

# 로그 설정 (터미널에 로그 기록)
if __name__ == '__main__':
    # 기존 로그 핸들러 제거 (중복 방지)
    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    # 콘솔 핸들러 설정 (터미널 로깅)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 로그 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Flask 애플리케이션에 콘솔 핸들러 추가
    app.logger.addHandler(console_handler)
    
    # 애플리케이션 시작 로그
    app.logger.info('Starting Flask application...')
    
    try:
        # 멀티스레딩 활성화
        app.run(debug=True, threaded=True)
    except Exception as e:
        app.logger.error(f'An error occurred while running the Flask application: {e}')
    finally:
        app.logger.info('Flask application has stopped.')

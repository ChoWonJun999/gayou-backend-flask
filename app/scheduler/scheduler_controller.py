from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from .data_collector import collect_data
from ..logging import setup_logging

from ..config.config import Config

# 로그 설정
logger = setup_logging()

# 스케줄러 인스턴스 생성
scheduler = BackgroundScheduler()
is_scheduler_running_flag = not Config.WERKZEUG_RUN_MAIN  # 스케줄러 실행 상태를 저장하는 변수

# 스케줄러 작업 추가
scheduler.add_job(
    collect_data,
    'interval',
    weeks=1,
    id='collect_data_job',
    max_instances=1,
    next_run_time=datetime.now()
)

def start_scheduler():
    """스케줄러 시작 함수."""
    global is_scheduler_running_flag
    if not is_scheduler_running_flag:
        scheduler.start()
        is_scheduler_running_flag = True
        logger.info("Scheduler started.")
    else:
        logger.info("Scheduler is already running.")

def stop_scheduler():
    """스케줄러 중지 함수."""
    global is_scheduler_running_flag
    if is_scheduler_running_flag:
        scheduler.shutdown(wait=False)
        is_scheduler_running_flag = False
        logger.info("Scheduler stopped.")
    else:
        logger.info("Scheduler is not running.")

def is_scheduler_running():
    """스케줄러가 실행 중인지 확인하는 함수."""
    return is_scheduler_running_flag

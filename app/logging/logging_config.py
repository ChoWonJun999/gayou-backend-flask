import logging
import os

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[0m',      # Default
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m'  # Magenta
    }

    RESET = '\033[0m'

    def format(self, record):
        """
        로그 레코드를 색상으로 포맷합니다.
        로그 메시지의 레벨에 따라 다른 색상을 적용합니다.
        """
        log_fmt = f"{self.COLORS.get(record.levelname, self.RESET)}%(asctime)s - %(levelname)s - %(message)s{self.RESET}"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging():
    """
    로깅 설정을 구성하는 함수.
    콘솔에 컬러 로그를 출력하도록 설정하고, 파일에 로그를 기록합니다.
    """
    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # DEBUG 레벨 이상을 로깅
    color_formatter = ColoredFormatter()
    console_handler.setFormatter(color_formatter)

    # 파일 핸들러 생성
    log_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.log')
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.WARNING)  # 파일에 저장할 로그 레벨 설정
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 기본 로거 설정
    logger = logging.getLogger()
    
    # 기존 핸들러가 있으면 제거
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 콘솔 및 파일 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    return logger

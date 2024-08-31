import logging

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
        log_fmt = f"{self.COLORS.get(record.levelname, self.RESET)}%(asctime)s - %(levelname)s - %(message)s{self.RESET}"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging():
    """Setup logging configuration."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    color_formatter = ColoredFormatter()
    console_handler.setFormatter(color_formatter)

    # Get the root logger
    logger = logging.getLogger()
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    return logger

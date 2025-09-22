import logging
import os
from logging import StreamHandler, FileHandler, Formatter
from datetime import datetime
from logging.handlers import RotatingFileHandler

from src.infra.create_time import Time


class MoscowFormatter(logging.Formatter):
    """Форматтер, использующий Московское время."""

    def formatTime(self, record, datefmt=None):
        # Используем ваш класс Time для получения времени
        dt = Time.now()
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()


log_dir = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(log_dir, exist_ok=True)

formatter = MoscowFormatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = RotatingFileHandler(
    os.path.join(log_dir, "app.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
)
file_handler.setFormatter(formatter)

stream_handler = StreamHandler()
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)

logger = logging.getLogger("app")

import logging
import logging.handlers
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import structlog
from structlog._frames import _find_first_app_frame_and_name

ENV_MODE = os.getenv("ENV_MODE", "LOCAL")

# Set default logging level based on environment
if ENV_MODE.upper() == "PRODUCTION":
    default_level = "DEBUG"
else:
    default_level = "INFO"

LOGGING_LEVEL = logging.getLevelNamesMapping().get(
    os.getenv("LOGGING_LEVEL", default_level).upper(), 
    logging.DEBUG if ENV_MODE.upper() == "PRODUCTION" else logging.INFO
)

LOGS_PATH = Path(__file__).resolve().parents[1] / 'logs'
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class NoColorFormatter(logging.Formatter):
    """移除ANSI颜色转义序列的Formatter"""
    
    # DeepSeek
    ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')

    # Claude4
    # ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def format(self, record):
        message = super().format(record)
        return self.ANSI_ESCAPE_RE.sub('', message)  # 移除所有ANSI转义序列


def make_logger(name: str):
    name = str(int(time.time())) + '_' + Path(name).name

    logger_fp = LOGS_PATH / (name + '.log')
    logger_fp = logger_fp.resolve()

    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)
    logger.propagate = False

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logger_fp,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding='utf-8',
        delay=True,
    )
    file_handler.setFormatter(NoColorFormatter('%(message)s'))
    file_handler.setLevel(LOGGING_LEVEL)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    console_handler.setLevel(LOGGING_LEVEL)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


class StructLoggerFactory(structlog.stdlib.LoggerFactory):
    def __call__(self, *args: Any) -> logging.Logger:
        if sys.argv:
            name = sys.argv[0]
        elif args:
            name = args[0]
        else:
            _, name = _find_first_app_frame_and_name(self._ignore)

        return make_logger(name)


processors = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
]

if ENV_MODE.lower() == "local".lower() or ENV_MODE.lower() == "staging".lower():
    renderer = structlog.dev.ConsoleRenderer()
else:
    renderer = structlog.processors.JSONRenderer()
    processors += [structlog.processors.dict_tracebacks, ]

processors += [
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
    structlog.processors.TimeStamper(fmt="iso", utc=False),
    structlog.contextvars.merge_contextvars,
    renderer,
]

structlog.configure(
    processors=processors,
    cache_logger_on_first_use=True,
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=StructLoggerFactory(),
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

import logging.config
import logging.handlers
import os
import re
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog._frames import _find_first_app_frame_and_name

ENV_MODE = os.getenv("ENV_MODE", "LOCAL")
LOGGING_LEVEL = logging.getLevelNamesMapping().get(
    os.getenv("LOGGING_LEVEL", "DEBUG").upper(), logging.DEBUG
)

LOGS_PATH = Path(__file__).resolve().parents[1] / 'logs'
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class NoColorFormatter(logging.Formatter):
    """移除ANSI颜色转义序列的Formatter"""
    ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')  # DeepSeek

    # ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])') # Claude4

    def format(self, record):
        message = super().format(record)
        return self.ANSI_ESCAPE_RE.sub('', message)  # 移除所有ANSI转义序列


logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "root": {
                "format": '{asctime} - {thread} - [{levelname[0]}] - {funcName} : {message}',
                "style": "{",
            },
        },
        "handlers": {
            "root_file": {
                "class": logging.handlers.TimedRotatingFileHandler,
                "level": logging.ERROR,
                "formatter": "root",
                'filename': LOGS_PATH / ".log",
                'when': "midnight",
                'interval': 1,
                'backupCount': 7,
                'encoding': 'utf-8',
                'delay': True,
            },
            "root_console": {
                "class": logging.StreamHandler,
                "level": logging.INFO,
                "formatter": "root",
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": logging.INFO,
            "handlers": ["root_file", "root_console"],
        },
    },
)


def make_logger(name: str):
    name = 'struct__' + Path(name).name

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

    # wrapper_class=structlog.make_filtering_bound_logger(LOGGING_LEVEL),

    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=StructLoggerFactory(),
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

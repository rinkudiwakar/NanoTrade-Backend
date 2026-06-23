"""
app/core/logger.py

Industry-grade structured logger for NanoTrade backend.

Features:
  - Colored console output per log level
  - Rotating file handler (logs/nanotrade.log, max 10MB, 5 backups)
  - Structured format: timestamp | level | component | message
  - Single setup call — all modules use getLogger(__name__)
  - Environment-aware: DEBUG in dev, INFO in production

Usage in any module:
    from app.core.logger import get_logger
    logger = get_logger(__name__)

    logger.info("Order received", extra={"order_id": "abc", "user_id": "xyz"})
    logger.debug("Matching engine called")
    logger.error("DB insert failed", exc_info=True)
"""

import json
import logging
import logging.handlers
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# ANSI color codes for terminal
# ─────────────────────────────────────────────────────────────────
_COLORS = {
    "DEBUG": "\033[90m",  # Grey
    "INFO": "\033[36m",  # Cyan
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}


# ─────────────────────────────────────────────────────────────────
# Custom colored formatter (console only)
# ─────────────────────────────────────────────────────────────────
class ColoredFormatter(logging.Formatter):
    """
    Format: [HH:MM:SS.mmm] [LEVEL   ] [component          ] message  {extra}
    """

    LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)-30s] %(message)s"

    def __init__(self):
        super().__init__(fmt=self.LOG_FORMAT, datefmt="%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        # Inject milliseconds into asctime manually
        record.asctime = self.formatTime(record, self.datefmt)
        ms = int((record.created - int(record.created)) * 1000)
        record.asctime = f"{record.asctime}.{ms:03d}"

        # Attach any "extra" context fields to the message
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k
            not in (
                "message",
                "asctime",
                "args",
                "exc_info",
                "exc_text",
                "stack_info",
                "msg",
                "name",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            )
        }
        if extras:
            extras_str = "  " + "  ".join(f"{k}={v}" for k, v in extras.items())
            record.msg = str(record.msg) + extras_str

        color = _COLORS.get(record.levelname, "")
        reset = _COLORS["RESET"]
        return color + super().format(record) + reset


# ─────────────────────────────────────────────────────────────────
# Plain formatter for log file (no ANSI)
# ─────────────────────────────────────────────────────────────────
class PlainFormatter(logging.Formatter):
    LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)-30s] %(message)s"

    def __init__(self):
        super().__init__(fmt=self.LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        ms = int((record.created - int(record.created)) * 1000)
        record.asctime = self.formatTime(record, self.datefmt) + f".{ms:03d}"

        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k
            not in (
                "message",
                "asctime",
                "args",
                "exc_info",
                "exc_text",
                "stack_info",
                "msg",
                "name",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            )
        }
        if extras:
            extras_str = "  " + "  ".join(f"{k}={v}" for k, v in extras.items())
            record.msg = str(record.msg) + extras_str

        return super().format(record)


# ─────────────────────────────────────────────────────────────────
# JSON formatter for structured logs (metrics/observability)
# ─────────────────────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ms = int((record.created - int(record.created)) * 1000)
        asctime = self.formatTime(record, "%Y-%m-%dT%H:%M:%S") + f".{ms:03d}Z"

        log_obj = {
            "timestamp": asctime,
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Include standard exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include extra context fields
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k
            not in (
                "message",
                "asctime",
                "args",
                "exc_info",
                "exc_text",
                "stack_info",
                "msg",
                "name",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            )
        }
        if extras:
            log_obj.update(extras)

        return json.dumps(log_obj)


# ─────────────────────────────────────────────────────────────────
# Setup — called ONCE at app startup
# ─────────────────────────────────────────────────────────────────
_initialized = False


def setup_logging(log_level: str = "DEBUG", log_dir: str = "logs") -> None:
    """
    Configure the root logger with:
      - Colored StreamHandler → stdout
      - RotatingFileHandler  → logs/nanotrade.log (10 MB × 5 files)

    Call this once from app/main.py lifespan startup.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    # Resolve log level
    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "nanotrade.log"

    # Root logger
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # ── Console handler ───────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ColoredFormatter())
    root.addHandler(console_handler)

    # ── Rotating file handler (Plain Text) ────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(PlainFormatter())
    root.addHandler(file_handler)

    # ── Rotating file handler (JSON) ──────────────────────────────
    json_log_file = log_path / "nanotrade.json.log"
    json_file_handler = logging.handlers.RotatingFileHandler(
        filename=str(json_log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    json_file_handler.setLevel(numeric_level)
    json_file_handler.setFormatter(JsonFormatter())
    root.addHandler(json_file_handler)

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore", "supabase"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Keep uvicorn.error visible so startup/shutdown messages show
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    root.info(
        f"Logging initialized | level={log_level.upper()} " f"file={log_file.resolve()}"
    )


# ─────────────────────────────────────────────────────────────────
# Module-level helper
# ─────────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger. Use this in every module:

        from app.core.logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)

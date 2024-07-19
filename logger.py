from colorlog import ColoredFormatter
from pathlib import Path
import logging.handlers
import logging
import os


# Create a logger.
logger = logging.getLogger(name="log")


def init_logger(logger: logging.Logger):
    # Create the logs directory if it does not yet exist.
    current_dir = Path(__file__).parent.absolute()
    os.makedirs(f"{current_dir}/logs", exist_ok=True)

    logger.propagate = False

    # Enable logging to the console, stderr.
    ch = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        "* {log_color}{levelname:5s}{reset} - {message} - {module}.{lineno}",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="{",
    )
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

    # Enable logging to file, every week (on mondays) a new log file is made.
    # We save log files for four weeks, then they get deleted. All log files are in the "/logs" dir.
    fh = logging.handlers.TimedRotatingFileHandler(
        filename=f"{current_dir}/logs/app.log", when="w0", interval=1, backupCount=4
    )
    fh.suffix = "%Y-%m-%d.log"
    file_formatter = logging.Formatter(
        "* {asctime} {levelname:5s} - {message} - {module}.{lineno}", style="{"
    )
    fh.setFormatter(file_formatter)
    logger.addHandler(fh)

    logger.setLevel(logging.INFO)
    add_session_separator()


def add_session_separator():
    # Clear sepperation log from previous session.
    logger.info("\n" + "=" * 50 + "\nNew Logging Session\n" + "=" * 50 + "\n")

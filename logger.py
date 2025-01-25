# file: logger.py
import logging
import logging.handlers

from colorlog import ColoredFormatter

# Create a logger.
logger = logging.getLogger(name="log")


def init_logger(logger: logging.Logger):
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

    logger.setLevel(logging.INFO)

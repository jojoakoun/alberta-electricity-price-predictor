import logging


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
  """Create a simple console logger."""
  logger = logging.getLogger(name)

  # Avoid duplicate logs if the logger is requested more than once.
  if logger.handlers:
    return logger

  logger.setLevel(logging.INFO)

  console_handler = logging.StreamHandler()
  console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))

  logger.addHandler(console_handler)
  logger.propagate = False

  return logger
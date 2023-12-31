import logging
import logging.handlers

__all__ = [
    "get_logger",
]


def get_logger(name: str, level: str = "DEBUG") -> logging.Logger:  # name: __name__
    """
    Get a logger with a stream handler.

    Parameters
    ----------
    name : str
        logger name. Usually __name__.
    level : str, optional
        logging level, by default "DEBUG"

    Returns
    -------
    logging.Logger
        _description_
    """
    logger = logging.getLogger(name)
    stream_handler = logging.StreamHandler()

    # set format
    literal_formatter = logging.Formatter("%(asctime)s:%(levelname)s:\n%(name)s:%(message)s")
    stream_handler.setFormatter(literal_formatter)

    # set level
    logger.setLevel(level)
    stream_handler.setLevel(level)

    # add handler
    if not logger.hasHandlers():
        logger.addHandler(stream_handler)

    return logger

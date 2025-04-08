import logging

def setup_logger(log_file: str = None):
    logger = logging.getLogger("VoiceDetection")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Optional file handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

# Create a module-level logger instance
logger = setup_logger()

if __name__ == "__main__":
    logger.info("Logger is configured")
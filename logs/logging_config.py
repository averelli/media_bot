import logging

def get_logger(name):
    # get a new logger with a name
    logger = logging.getLogger(name)

    # set level to info
    logger.setLevel(logging.INFO)  

    # create a formatter
    formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s")

    # create a file handler to save the logs
    handler = logging.FileHandler("logs/bot_logs.log")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    # add handler to the logger
    logger.addHandler(handler)

    return logger
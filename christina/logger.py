import logging


class LoggerDelegate:
    def __init__(self, logger):
        self.logger = logger

    def format(self, *args):
        strs = [arg if isinstance(arg, str) else repr(arg) for arg in args]

        return ' '.join(strs)


def create_log_method(method: str):
    def func(self, *args):
        formatted_args = self.format(*args)

        for line in formatted_args.split('\n'):
            getattr(self.logger, method)(line)

    func.__name__ = method

    return func


for method in ['debug', 'info', 'warning', 'error', 'critical']:
    setattr(LoggerDelegate, method, create_log_method(method))


def get_logger(name: str):
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)

    # set custom log formatter
    # fmt = logging.Formatter(fmt='')
    # handler = logging.StreamHandler()
    # handler.setFormatter(fmt)
    # logger.addHandler(handler)

    if not hasattr(logger, '_delegate'):
        logger._delegate=LoggerDelegate(logger)

    return logger._delegate

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


class LogFormatter(logging.Formatter):
    fmt = r'{name:-<16}[{levelname[0]}][{asctime}] {message}'
    datefmt = r'%Y-%m-%d %H:%M:%S'

    def __init__(self):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt, style='{')


def get_logger(name: str):
    # no need to show the root module
    name = name.replace('christina.', '')

    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # set custom log formatter
    handler = logging.StreamHandler()
    handler.setFormatter(LogFormatter())
    logger.addHandler(handler)

    if not hasattr(logger, '_delegate'):
        logger._delegate = LoggerDelegate(logger)

    return logger._delegate

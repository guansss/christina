import logging


class LoggerDelegate:
    def __init__(self, logger):
        self.logger = logger

        for method in ['debug', 'info', 'warning', 'error', 'critical']:
            self.delegate_method(method, method)

        # prefer "warn" to "warning"
        self.delegate_method('warn', 'warning')

        self.delegate_method('log', 'debug')

    def exception(self, *args, **kw):
        # call as is
        self.logger.exception(*args, **kw)

    def delegate_method(self, method: str, delegated_method: str):
        if not hasattr(self, method):
            def func(self, *args):
                formatted_args = [arg if isinstance(arg, str) else repr(arg) for arg in args]
                lines = ' '.join(formatted_args).split('\n')

                for line in filter(None, lines):
                    getattr(self.logger, delegated_method)(line)

            func.__name__ = method

            setattr(LoggerDelegate, method, func)


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

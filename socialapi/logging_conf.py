import logging
from logging.config import dictConfig

from socialapi.config import Devconfig, config


# the obfuscated filter its gonna work like for xamples: julian.ferreira@example.com its gonna be -> ju************@example.com
def obfuscated(email: str, obfuscated_length: int) -> str:
    characters = email[:obfuscated_length]  # how many characters wanne be see
    first, last = email.split("@")  # (julian.ferreira, example.com)
    return characters + "*" * (len(first) - obfuscated_length) + "@" + last


class EmailObfuscationFilter(logging.Filter):
    def __init__(self, name: str = "", obfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        # record.my_variable = "123" and this is gonna be: "(%(correlation_id)s)(%(my_varaible)s)%(name)s:%(lineno)d - %(message)s",
        if "email" in record.__dict__:
            record.email = obfuscated(record.email, self.obfuscated_length)
        return True


handlers = ["default", "rotating_file"]
if isinstance(config, Devconfig):
    handlers = ["default", "rotating_file", "logtail"]


# insede the filter is gonna look like: filter= asgi_correlation_id.CorrelationIdFilter(uuid_length=8, defatul_value="-")
def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",  # constructor
                    "uuid_length": 8
                    if isinstance(config, Devconfig)
                    else 32,  # universinal unique identifier, and if we in dev, is gonna contrcut a uuid of 8 character, otherwise, for example prod, is gonna be 32 characters
                    "default_value": "-",  # if we are not in a request no uuid is generate.
                },
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscated_length": 2
                    if isinstance(config, Devconfig)
                    else 0,  # in developing we see some of the email.
                },
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s)%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s %(msecs)03dZ  %(levelname) -8s  %(correlation_id)s %(name)s %(lineno)d  %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": [
                        "correlation_id",
                        "email_obfuscation",
                    ],  # tell our handler that we are going to use it
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "socialapi.log",
                    "maxBytes": 1024 * 1024,  # 1MB
                    "backupCount": 5,  # 5 files of 2MB
                    "encoding": "utf8",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "logtail": {
                    "class": "logtail.LogtailHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email_obfuscation"],
                    "source_token": config.LOGTAIL_API_KEY,
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                "socialapi": {
                    "handlers": handlers,
                    "level": "DEBUG" if isinstance(config, Devconfig) else "INFO",
                    "propagate": False,  # i wanna do that, top level logger, anything to be set root.
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )

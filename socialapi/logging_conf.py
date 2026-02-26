from logging.config import dictConfig

from socialapi.config import Devconfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "loggin.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                }
            },
            "loggers": {
                "socialapi": {
                    "handlers": ["default"],
                    "level": "DEBUG" if isinstance(config, Devconfig) else "INFO",
                    "propagate": False,  # i wanna do that, top level logger, anything to be set root.
                }
            },
        }
    )

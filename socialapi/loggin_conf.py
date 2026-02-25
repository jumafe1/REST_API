from logging.config import dictConfig

from socialapi.config import config


def configure_logging()->None:
    dictConfig(

        {
            "version": 1
        }
    )
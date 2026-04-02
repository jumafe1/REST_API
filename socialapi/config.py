from functools import lru_cache  # for use chashing
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


# populate configuration variables
class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    model_config = ConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False  # after every test the database is clear
    MAILGUN_DOMAIN: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    LOGTAIL_API_KEY: Optional[str] = None
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None


class Devconfig(GlobalConfig):
    model_config = ConfigDict(
        env_prefix="DEV_"
    )  # prefix the variables in the .env file to differentiate dev/prod/test


class ProdConfig(GlobalConfig):
    model_config = ConfigDict(env_prefix="PROD_")


class TestConfig(GlobalConfig):
    DATABASE_URL: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True  # after every test the database is clear

    model_config = ConfigDict(env_prefix="TEST_")


# this function returns the same thing everything
@lru_cache()
def get_config(env_state: str):
    configs = {"dev": Devconfig, "prod": ProdConfig, "test": TestConfig}
    return configs[
        env_state
    ]()  # () mean that if env_state has the value, we create a object of that class ( class= devconfig, etec)


# get the current value of env_state:
# value
config = get_config(BaseConfig().ENV_STATE)

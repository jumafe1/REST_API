from functools import lru_cache  # for use chashing
from typing import Optional

from pydantic_settings import BaseSettings


# populate configuration variables
class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    class Config:
        env_file: str = ".env"
        extra = "ignore"


class GlobalConfig(BaseConfig):
    DATABASE_URL: str = None
    DB_FORCE_ROLL_BACK: bool = False  # after every test the database is clear


class Devconfig(GlobalConfig):
    class Config:
        env_prefix = "DEV_"  # this is for prefix the variables in the .env file, for example, if we want to have different variables for development and production, we can use the prefix to differentiate them/


class ProdConfig(GlobalConfig):
    class Config:
        env_prefix = "PROD_"


class TestConfig(GlobalConfig):
    DATABASE_URL: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True  # after every test the database is clear

    class Config:
        env_prefix = "TEST_"


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

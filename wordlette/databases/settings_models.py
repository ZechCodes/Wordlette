from wordlette.configs import ConfigModel
from wordlette.models import FieldSchema


class DatabaseSettings(ConfigModel, key="database"):
    driver: str @ FieldSchema

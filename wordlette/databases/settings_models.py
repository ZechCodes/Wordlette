from wordlette.configs import ConfigModel
from wordlette.models import FieldSchema


class DatabaseSettings(ConfigModel, key="database"):
    driver: str @ FieldSchema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

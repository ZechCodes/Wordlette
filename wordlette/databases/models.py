from wordlette.models import Model


class DatabaseModel(Model):
    __models__ = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        DatabaseModel.__models__.add(cls)

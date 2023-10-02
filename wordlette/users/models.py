import wordlette.users.accessors as accessors
from wordlette.models import Auto
from wordlette.orm.models import DatabaseModel
from wordlette.orm.properties import Property


class User(DatabaseModel):
    id: int | Auto @ Property
    name: str @ Property

    @property
    def metadata(self) -> "accessors.UserMetadataAccessor":
        return accessors.UserMetadataAccessor(self.id)


class UserMetadata(DatabaseModel):
    id: int | Auto @ Property
    user_id: int @ Property
    key: str @ Property
    value: str @ Property

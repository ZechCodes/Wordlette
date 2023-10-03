from wordlette.users.auth_providers import BaseAuthProvider
from wordlette.users.auth_security_levels import AuthSecurityLevel


class BasicPasswordProvider(
    BaseAuthProvider,
    name="Basic Password Authentication",
    security_level=AuthSecurityLevel.UNSAFE,
):
    ...

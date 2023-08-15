from wordlette.routes import Route


class SetupRoute(Route):
    """All subclasses of this abstract route type are automatically mounted by the Setup state."""

    class __metadata__:
        abstract = True
        registry = set()

from wordlette.routes import Route as _Route


class Route(_Route):
    """All subclasses of this abstract route type are automatically mounted by the Serving state."""

    class __metadata__:
        abstract = True
        registry = set()

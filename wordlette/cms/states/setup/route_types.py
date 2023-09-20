from typing import Iterable

from wordlette.cms.states.setup.enums import SetupStatus, SetupCategory
from wordlette.routes import Route
from wordlette.utils.dependency_injection import inject


class CategoryController:
    def __init__(self):
        self.routes: list[SetupRoute] = []
        self.completed_routes: list[SetupRoute] = []
        self.history: list[SetupRoute] = []

    def add_route(self, route: "SetupRoute"):
        self.routes.append(route)

    def completed(self, route: "SetupRoute"):
        self.routes.remove(route)
        self.completed_routes.append(route)

    def is_done(self):
        return not self.routes

    async def get_next_route(self) -> "SetupRoute | None":
        for route in self.routes.copy():
            status = await route.setup_status()
            if status is SetupStatus.Ready:
                self.history.append(route)
                return route

            elif status is SetupStatus.Complete:
                self.completed(route)

        else:
            return self.routes[0] if self.routes else None


class SetupRouteCategoryController:
    category_order: Iterable[SetupCategory] = (
        SetupCategory.Config,
        SetupCategory.Database,
        SetupCategory.Admin,
        SetupCategory.General,
    )

    def __init__(self):
        self._category_stack = iter(self.category_order)

        self.categories = self._build_categories()
        self.current_category = self.next_category()

        self.index_route: SetupRoute | None = None
        self.completed_route: SetupRoute | None = None

    def next_category(self) -> SetupCategory:
        return next(self._category_stack, SetupCategory.NoCategory)

    def add_route(self, route: "SetupRoute"):
        if route.path == "/":
            self.index_route = route

        elif route.setup_category == SetupCategory.NoCategory:
            self.completed_route = route

        else:
            self.categories[route.setup_category].add_route(route)

    async def get_next_route(self) -> "SetupRoute":
        while self.current_category is not SetupCategory.NoCategory:
            route = await self.categories[self.current_category].get_next_route()
            if route is not None:
                return route

            self.current_category = self.next_category()

        return self.completed_route

    def _build_categories(self) -> dict[SetupCategory, CategoryController]:
        categories = {}
        for category in SetupCategory:
            categories[category] = CategoryController()

        return categories


class SetupRoute(Route):
    controller: SetupRouteCategoryController @ inject
    setup_category: SetupCategory

    class __metadata__:
        abstract = True
        registry = set()

    def __init_subclass__(
        cls, setup_category: SetupCategory = SetupCategory.General, **kwargs
    ):
        super().__init_subclass__(**kwargs)

        cls.setup_category = setup_category

    def __init__(self):
        super().__init__()
        self.controller.add_route(self)

    async def setup_status(self, *_) -> SetupStatus:
        return SetupStatus.Waiting

    async def get_next_page(self) -> "SetupRoute":
        return await self.controller.get_next_route()

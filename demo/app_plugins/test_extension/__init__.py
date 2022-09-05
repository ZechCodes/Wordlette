from bevy import Bevy, Inject, bevy_method
from starlette.applications import Starlette

from wordlette.app import App
from wordlette.events import EventManager
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.templates import Template, TemplateEngine


class TestPage(Page):
    path = "/ext"

    async def response(self):
        return Template("testing.html", {})


class TestPlugin(Plugin):
    def __init__(self):
        print("STARTED PLUGIN")


class BevyPlugin(Plugin, Bevy):
    events: EventManager = Inject

    @bevy_method
    def __init__(self, app: App = Inject):
        self.app = app
        print(app.state)
        self.events.listen({"type": "changed-state"}, self.register_pages)

    async def register_pages(self, event):
        if event.new_state == self.app.state.serving_site:
            engine: TemplateEngine = self.bevy.find(TemplateEngine)
            print(engine.search_paths)
            TestPage.register(self.app.context.find(Starlette), self.app.context)

from bevy import Inject, bevy_method
from starlette.applications import Starlette

from wordlette.app import App
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.state_machine import StateMachine
from wordlette.templates import Template, TemplateEngine


class TestPage(Page):
    path = "/ext"

    async def response(self):
        return Template("testing.html", {})


class TestPlugin(Plugin):
    def __init__(self):
        print("STARTED PLUGIN")


class BevyPlugin(Plugin):
    @bevy_method
    def __init__(self, app: App = Inject):
        super().__init__()
        self.app = app
        print(">>> CURRENT STATE", app.state)

    @StateMachine.on("changed-state[serving_site]")
    async def register_pages(self, event):
        engine: TemplateEngine = self.bevy.find(TemplateEngine)
        print(">>> SEARCH PATHS", engine.search_paths)
        TestPage.register(self.app.context.find(Starlette), self.bevy)

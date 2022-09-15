from bevy import Inject, bevy_method

from wordlette.app import App
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.state_machine import StateMachine
from wordlette.templates import Template, TemplateEngine


class TestConfigModel:
    __config_table__ = "testing"

    def __init__(self, test: str = "Nope 😕"):
        self.test = test


class TestPage(Page):
    path = "/ext"

    async def response(self):
        return Template("testing.html", {})


class TestPlugin(Plugin):
    def __init__(self):
        super(TestPlugin, self).__init__()
        print("STARTED PLUGIN")


class Plugin(Plugin):
    @bevy_method
    def __init__(self, app: App = Inject):
        super().__init__()
        self.app = app
        print(">>> CURRENT STATE", app.state_machine)

    @StateMachine.on("entered-state[ServingSite]")
    @bevy_method
    async def register_pages(self, event, settings: TestConfigModel = Inject):
        print("Does config injection work?", settings.test)
        engine: TemplateEngine = self.bevy.find(TemplateEngine)
        print(">>> SEARCH PATHS", engine.search_paths)
        TestPage.register(self.app.router, self.bevy)

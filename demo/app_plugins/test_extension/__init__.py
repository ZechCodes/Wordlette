from dataclasses import dataclass, field

from bevy import Inject, bevy_method
from wordlette import Logging
from wordlette.app import App
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.state_machine import StateMachine
from wordlette.templates import Template, TemplateEngine


@dataclass
class TestConfigModel:
    __config_table__ = "testing"

    test: str = field(default="Nope 😕")


class TestPage(Page):
    path = "/ext"

    async def response(self):
        return Template("testing.html", {})


class TestPlugin(Plugin):
    @bevy_method
    def __init__(self, log: Logging = Inject):
        super(TestPlugin, self).__init__()
        log.info("STARTED PLUGIN")


class Plugin(Plugin):
    @bevy_method
    def __init__(self, app: App = Inject, log: Logging = Inject):
        super().__init__()
        self.app = app
        log.info(f"CURRENT STATE {app.state_machine}")

    @StateMachine.on("entered-state[ServingSite]")
    @bevy_method
    async def register_pages(
        self, event, settings: TestConfigModel = Inject, log: Logging = Inject
    ):
        log.info(f"Does config injection work? {settings.test}")
        engine: TemplateEngine = self.bevy.find(TemplateEngine)
        log.info(f"SEARCH PATHS {engine.search_paths}")
        TestPage.register(self.app.router, self.bevy)

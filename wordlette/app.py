from wordlette.configs.extensions import Config
from wordlette.core import WordletteApp
from wordlette.core.states import SettingUp, Starting, Serving
from wordlette.middlewares.router_middleware import RouterMiddleware
from wordlette.state_machines import StateMachine

app = WordletteApp(
    middleware=[RouterMiddleware],
    state_machine=StateMachine(
        Starting.goes_to(SettingUp, when=SettingUp.needs_setup),
        Starting.goes_to(Serving),
    ),
    extensions=[Config],
)

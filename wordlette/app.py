from bevy import Context
from wordlette.state_machine import StateMachine, state


class App(StateMachine):
    def __init__(self, *args):
        super().__init__(*args)
        self._context = Context.factory()

    @state
    async def startup(self):
        ...

    @state
    async def load_extensions(self):
        ...

    @state
    async def load_config(self):
        ...

    @state
    async def create_config(self):
        ...

    @state
    async def connect_db(self):
        ...

    @state
    async def configure_db(self):
        ...

    @startup >> load_extensions
    async def 

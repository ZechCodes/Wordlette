from wordlette.state_machines import State


class Serving(State):
    def enter_state(self) -> None:
        ...

from io import StringIO

import pytest
from starlette.testclient import TestClient

import wordlette.app.states as states
from wordlette.app import WordletteApp
from wordlette.state_machines.machine import StateMachine, StoppedState


class MockPath:
    def __init__(self, exists: bool, content: str = ""):
        self._exists = exists
        self._content = content

    def exists(self):
        return self._exists

    def open(self):
        return StringIO(self._content)


@pytest.mark.asyncio
async def test_bootstrap_state():
    app = WordletteApp(StateMachine(states.BootstrappingApp))
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200
    assert isinstance(app.state_machine.state, StoppedState)


@pytest.mark.asyncio
async def test_config_state():
    app = WordletteApp(
        StateMachine(states.BootstrappingApp.goes_to(states.CreatingConfig))
    )
    app.app_settings["config_file"] = MockPath(False)
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200
    assert isinstance(app.state_machine.state, states.CreatingConfig)


@pytest.mark.asyncio
async def test_db_state():
    app = WordletteApp(
        StateMachine(
            states.BootstrappingApp.goes_to(
                states.CreatingConfig, when=states.BootstrappingApp.no_config_found
            ),
            states.BootstrappingApp.goes_to(
                states.ConnectingDB, when=states.BootstrappingApp.has_database_config
            ),
        ),
    )
    app.app_settings["config_file"] = MockPath(True)
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200
    assert isinstance(app.state_machine.state, StoppedState)


@pytest.mark.asyncio
async def test_db_state_no_config():
    app = WordletteApp(
        StateMachine(
            states.BootstrappingApp.goes_to(
                states.CreatingConfig, when=states.BootstrappingApp.no_config_found
            ),
            states.BootstrappingApp.goes_to(
                states.ConnectingDB, when=states.BootstrappingApp.has_database_config
            ),
        ),
    )
    app.app_settings["config_file"] = MockPath(False)
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200
    assert isinstance(app.state_machine.state, states.CreatingConfig)

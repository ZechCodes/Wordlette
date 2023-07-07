import pytest
from starlette.testclient import TestClient

from wordlette.cms import CMSApp
from wordlette.cms.states import BootstrapState


@pytest.fixture
def client():
    return TestClient(CMSApp())


@pytest.mark.asyncio
async def test_cms_bootstrap_app():
    state = BootstrapState(None)
    await state.enter_state()

    client = TestClient(state.value)
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200


@pytest.mark.asyncio
async def test_cms_config_state(client):
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200

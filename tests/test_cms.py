import pytest
from starlette.testclient import TestClient

from wordlette.cms import CMSApp


@pytest.fixture
def client():
    return TestClient(CMSApp())


def test_cms_bootstrap_app(client):
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200

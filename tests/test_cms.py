import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client():
    from wordlette.cms import create_cms_app

    return TestClient(create_cms_app())


def test_cms_bootstrap_app(client):
    assert client.get("/").status_code == 200
    assert client.get("/testing").status_code == 200

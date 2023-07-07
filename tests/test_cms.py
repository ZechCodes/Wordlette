import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client():
    from wordlette.cms import app

    return TestClient(app)


def test_cms_app_ok(client):
    response = client.get("/")
    assert response.status_code == 200

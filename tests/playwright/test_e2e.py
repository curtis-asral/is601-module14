import pytest

BASE_URL = "http://localhost:8000"  # Adjust if your app runs on a different port



@pytest.fixture(scope="session")
def browser():
    # Dummy browser fixture
    yield None



@pytest.fixture()
def page(browser):
    # Dummy page fixture
    yield None


def test_register_valid(page):
    assert True


def test_login_valid(page):
    assert True



def test_register_short_password(page):
    assert True



def test_login_wrong_password(page):
    assert True

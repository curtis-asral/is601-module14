import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"  # Adjust if your app runs on a different port

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture()
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_register_valid(page):
    page.goto(f"{BASE_URL}/register")
    page.fill('input[name="email"]', 'testuser@example.com')
    page.fill('input[name="password"]', 'validPassword123')
    page.click('button[type="submit"]')
    assert page.locator('.success-message').inner_text().lower().find("registration successful") != -1

def test_login_valid(page):
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', 'testuser@example.com')
    page.fill('input[name="password"]', 'validPassword123')
    page.click('button[type="submit"]')
    text = page.locator('.success-message').inner_text().lower()
    assert "login successful" in text or "welcome" in text


def test_register_short_password(page):
    page.goto(f"{BASE_URL}/register")
    page.fill('input[name="email"]', 'shortpass@example.com')
    page.fill('input[name="password"]', '123')
    page.click('button[type="submit"]')
    error = page.locator('.error-message').inner_text().lower()
    assert "password" in error and ("too short" in error or "minimum length" in error)


def test_login_wrong_password(page):
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', 'testuser@example.com')
    page.fill('input[name="password"]', 'wrongPassword')
    page.click('button[type="submit"]')
    error = page.locator('.error-message').inner_text().lower()
    assert "invalid credentials" in error or "401" in error

import os
from typing import Generator, Any

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.webdriver import Options

from post_parser.post import User, parse_user_page


@pytest.fixture(scope='class')
def chrome_driver(request: Any) -> Generator:
    options = Options()
    options.add_argument('--disable-notifications --start-maximized')
    driver = Chrome(options=options)
    request.cls.driver = driver
    yield
    driver.close()


@pytest.mark.usefixtures('chrome_driver')
class TestUserParser:
    driver: Chrome

    def test_user_page_correct(self) -> None:
        user = parse_user_page(self.driver, os.path.abspath('tests/static_files/user_pages/user_page_correct.html'))
        assert isinstance(user, User)
        assert user.username == 'u/axnu'
        assert user.user_karma == 82803
        assert user.post_karma == 1505594
        assert user.comment_karma == 215184
        assert user.user_cake_day == 'March 22, 2017'

    def test_user_page_empty(self) -> None:
        with pytest.raises(NoSuchElementException):
            parse_user_page(self.driver, os.path.abspath('tests/static_files/user_pages/user_page_empty.html'))

from selenium.webdriver import Chrome

from post_parser.parser import create_drivers
from post_parser.post import parse_number


def test_parse_number_1() -> None:
    number = '2.4k'
    result = parse_number(number)
    assert result == 2400


def test_parse_number_2() -> None:
    number = '421'
    result = parse_number(number)
    assert result == 421


def test_create_drivers() -> None:
    top_driver, post_drivers = create_drivers()
    assert isinstance(top_driver, Chrome)
    top_driver.close()
    for post_driver in post_drivers:
        assert isinstance(post_driver, Chrome)
        post_driver.close()

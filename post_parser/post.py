from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from timeit import default_timer
from typing import Tuple
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

_LOGGER = logging.getLogger(__name__)

USER_KARMA_AND_CAKE_DAY_CLASS = '_1hNyZSklmcC7R_IfCUcXmZ'
USER_KARMA_AND_CAKE_DAY_SELECTOR = '._1hNyZSklmcC7R_IfCUcXmZ'
SEPARATED_KARMA_CLASS = '_3uK2I0hi3JFTKnMUFHD2Pd'
PREMIUM_USERNAME_CLASS = '_28nEhn86_R1ENZ59eAru8S'
DEFAULT_USERNAME_CLASS = '_1LCAhi_8JjayVo7pJ0KIh0'
POST_DATE_CLASS = 'u6HtAZu8_LKL721-EnKuR'
POST_DATE_SELECTOR = '._3jOxDPIQ0KaOWpzvSQo-1s'
POST_CATEGORY_ATTR = {'title': re.compile('r/.*')}
NUMBER_OF_COMMENTS_ATTR = {'data-click-id': 'comments'}
UPVOTE_PERCENTAGE_CLASS = 't4Hq30BDzTeJ85vREX7_M'
POST_RATING_CLASS = '_1rZYMD_4xY3gRcSS3p8ODO'
USER_URL_REGEX = re.compile('/user/.*')


def parse_post_page(driver: webdriver.Chrome, url: str) -> Post:
    _LOGGER.info(f'Started parsing post {url}')
    parsing_start = default_timer()
    driver.get(url)

    set_mouse_over(driver, POST_DATE_SELECTOR)
    time.sleep(0.5)

    post_soup = BeautifulSoup(driver.page_source, 'html.parser')

    post_date = _parse_post_date(post_soup)
    post_category = _parse_post_category(post_soup)
    number_of_comments = _parse_number_of_comments(post_soup)
    vote_percentage = _parse_upvote_percentage(post_soup)
    post_rating = _parse_post_rating(post_soup)
    user_url = _parse_user_url(post_soup)

    number_of_votes = int(50 * post_rating / (vote_percentage - 50))

    user_url = "{0.scheme}://{0.netloc}".format(urlsplit(url)) + user_url

    user = parse_user_page(driver, user_url)

    _LOGGER.info(f'Post parsing success {default_timer() - parsing_start} seconds')

    return Post.from_post_page(user, url, post_date, number_of_comments, number_of_votes, post_category)


def parse_user_page(driver: webdriver.Chrome, url: str) -> User:
    _LOGGER.info(f'Parsing user {url}')
    driver.get(url)

    set_mouse_over(driver, USER_KARMA_AND_CAKE_DAY_SELECTOR)
    time.sleep(0.5)

    user_soup = BeautifulSoup(driver.page_source, 'html.parser')

    post_karma, comment_karma = _parse_karma(user_soup)
    user_karma = _parse_user_karma(user_soup)
    username = _parse_username(user_soup)
    user_cake_day = _parse_cake_day(user_soup)

    _LOGGER.info('User parsing success')
    return User(username, user_karma, user_cake_day, post_karma, comment_karma)


def parse_number(number: str) -> int:
    if 'k' in number:
        return int(float(number.replace('k', '')) * 1000)
    return int(number)


def set_mouse_over(driver: webdriver.Chrome, css_selector: str) -> None:
    ActionChains(driver).move_to_element(
        driver.find_element_by_css_selector(css_selector)).perform()


def _parse_karma(soup: BeautifulSoup) -> Tuple[int, int]:
    """
    Parses a separated user karma (post and comment) on reddit user page
    :param soup: User's page soup
    :return: Tuple of post and comment karma
    """
    karma = soup.find(class_=SEPARATED_KARMA_CLASS).text
    karma = re.sub('[a-zA-Z,]*', '', karma)
    karma = re.sub('\\s+', ' ', karma)
    post_karma, comment_karma, _, _ = karma.split()
    return parse_number(post_karma), parse_number(comment_karma)


def _parse_username(soup: BeautifulSoup) -> str:
    username_el = soup.find(class_=PREMIUM_USERNAME_CLASS)
    if not username_el:
        username_el = soup.find(class_=DEFAULT_USERNAME_CLASS)
    return re.sub('\\s*·\\s*.*', '', username_el.text)


def _parse_user_karma(soup: BeautifulSoup) -> int:
    user_karma = soup.find_all('span', class_=USER_KARMA_AND_CAKE_DAY_CLASS)[0].text.replace(',', '')
    return parse_number(user_karma)


def _parse_cake_day(soup: BeautifulSoup) -> str:
    return soup.find_all('span', class_=USER_KARMA_AND_CAKE_DAY_CLASS)[1].text


def _parse_post_date(soup: BeautifulSoup) -> datetime:
    post_date = soup.find(class_=POST_DATE_CLASS).text
    post_date = re.sub('\\s\\(.*\\)', '', post_date)
    return parser.parse(post_date)


def _parse_post_category(soup: BeautifulSoup) -> str:
    return soup.find(attrs=POST_CATEGORY_ATTR).text


def _parse_number_of_comments(soup: BeautifulSoup) -> int:
    number_of_comments = soup.find(attrs=NUMBER_OF_COMMENTS_ATTR).text
    number_of_comments = re.sub('\\s*comments', '', number_of_comments)
    return parse_number(number_of_comments)


def _parse_upvote_percentage(soup: BeautifulSoup) -> int:
    vote_percentage = soup.find(class_=UPVOTE_PERCENTAGE_CLASS).text.replace('% Upvoted', '')
    return parse_number(vote_percentage)


def _parse_post_rating(soup: BeautifulSoup) -> int:
    post_rating = soup.find(class_=POST_RATING_CLASS).text
    return parse_number(post_rating)


def _parse_user_url(soup: BeautifulSoup) -> str:
    return soup.find('a', href=USER_URL_REGEX).get('href')


@dataclass(frozen=True)
class User:
    username: str
    user_karma: int
    user_cake_day: str
    post_karma: int
    comment_karma: int


@dataclass(frozen=True)
class Post:
    post_url: str = field(compare=True)
    username: str = field(compare=False)
    user_karma: int = field(compare=False)
    user_cake_day: str = field(compare=False)
    post_karma: int = field(compare=False)
    comment_karma: int = field(compare=False)
    post_date: datetime = field(compare=False)
    number_of_comments: int = field(compare=False)
    number_of_votes: int = field(compare=False)
    post_category: str = field(compare=False)

    @property
    def id(self) -> str:
        return hashlib.md5(self.post_url.encode('ascii')).hexdigest()

    @classmethod
    def from_post_page(cls, user: User, post_url: str, post_date: datetime, number_of_comments: int,
                       number_of_votes: int, post_category: str) -> Post:
        username = user.username
        user_karma = user.user_karma
        user_cake_day = user.user_cake_day
        post_karma = user.post_karma
        comment_karma = user.comment_karma
        return cls(post_url, username, user_karma, user_cake_day, post_karma, comment_karma, post_date,
                   number_of_comments, number_of_votes, post_category)

    def __str__(self) -> str:
        return f'{self.id};{self.post_url};{self.username};{self.user_karma};{self.user_cake_day};{self.post_karma};' \
               f'{self.comment_karma};{self.post_date};{self.number_of_comments};{self.number_of_votes};' \
               f'{self.post_category}\n'

import logging
import re
from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
from timeit import default_timer
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from .post import Post, parse_post_page
from .post_schema import PostSchema

_LOGGER = logging.getLogger(__name__)

SERVER_POST_URL = 'http://localhost:8087/posts'

REDDIT_URL = 'https://www.reddit.com'
REDDIT_TOP = '/top/?t=month'

POST_SELECTOR = '.Post'
POST_REGEX = re.compile('Post')
POST_URL_ATTR = {'data-click-id': 'body'}
AVG_POST_HEIGHT = 600


@dataclass
class ParsingResult:
    parsed_posts: List[Post]
    duration: float


def posts(driver: webdriver.Chrome, offset: int) -> BeautifulSoup:
    counter = offset
    height = AVG_POST_HEIGHT * offset
    while True:
        height += driver.find_elements_by_css_selector(POST_SELECTOR)[counter].size.get('height')
        driver.execute_script(f'window.scrollTo(0, {height})')
        top_soup = BeautifulSoup(driver.page_source, 'html.parser')
        yield top_soup.find_all(class_=POST_REGEX)[counter]
        counter += 1


def create_drivers(post_driver_number: int = 1) -> Tuple[webdriver.Chrome, List[webdriver.Chrome]]:
    """
    Returns a post scroller driver and list of post parse drivers
    """
    if post_driver_number < 1:
        post_driver_number = 1
    chrome_options = Options()
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('log-level=3')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options), [webdriver.Chrome(options=chrome_options) for _ in
                                                      range(post_driver_number)]


def parse_post(driver: webdriver.Chrome, url: str) -> Optional[Post]:
    try:
        post = parse_post_page(driver, url)
        post_schema = PostSchema()
        requests.post(SERVER_POST_URL, data=post_schema.dumps(post))
        return post
    except ConnectionError:
        _LOGGER.error('Currently server is unavailable')
        exit()
    except NoSuchElementException:
        _LOGGER.error('User unavailable due to 18+ policy or deleted profile')
    except Exception:
        _LOGGER.exception('Something went wrong while parsing post')
    return None


def run(amount: int = 100, offset: int = 0, workers: int = 5) -> ParsingResult:
    logging.basicConfig(level=logging.INFO)
    start = default_timer()
    chrome, post_drivers = create_drivers(workers)
    chrome.get(REDDIT_URL + REDDIT_TOP)
    taken_posts = 0
    not_parsed_urls: List[str] = []
    complete_results = []
    for non_parsed_post in posts(chrome, offset):
        if len(not_parsed_urls) < workers:
            taken_posts += 1
            post_url = non_parsed_post.find('a', attrs=POST_URL_ATTR).get('href')
            not_parsed_urls.append(post_url)
            continue

        tasks = [(driver, REDDIT_URL + url) for driver, url in zip(post_drivers, not_parsed_urls)]

        with ThreadPool(workers) as pool:
            results = [pool.apply_async(parse_post, t) for t in tasks]
            pool.close()
            pool.join()

        new_results = [r.get() for r in results]
        complete_results.extend([r for r in new_results if r is not None])
        not_parsed_urls.clear()

        if len(complete_results) >= amount:
            break
        _LOGGER.info(f'{taken_posts} posts taken. {len(complete_results)} posts passed.')

    chrome.close()
    for post_driver in post_drivers:
        post_driver.close()

    duration = default_timer() - start
    _LOGGER.info(f'Total elapsed time {duration} seconds')
    return ParsingResult(complete_results[:amount], duration)

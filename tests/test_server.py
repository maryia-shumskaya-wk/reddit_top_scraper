from datetime import datetime
from multiprocessing import Process
from typing import Generator

import pytest
import requests

from post_parser.post import Post
from post_parser.post_schema import PostSchema
from post_parser.server import run, RESPONSE_NOT_FOUND, RESPONSE_OK, RESPONSE_CREATED

SERVER_URL = 'http://localhost:8087/posts'


@pytest.fixture(scope='session', autouse=True)
def setup_server() -> Generator:
    process = Process(target=run)
    # process.daemon = True
    process.start()
    yield
    process.terminate()


@pytest.fixture(scope='module')
def post_schema() -> PostSchema:
    return PostSchema()


@pytest.fixture(scope='module')
def test_post() -> Post:
    return Post(post_url='url', post_date=datetime.now(), number_of_comments=10, number_of_votes=1,
                post_category='r/idk', username='gun73r', user_karma=2, user_cake_day='cake day', post_karma=1,
                comment_karma=1)


@pytest.fixture(scope='module')
def replace_post() -> Post:
    return Post(post_url='url2', post_date=datetime.now(), number_of_comments=10, number_of_votes=1,
                post_category='r/idk2', username='gun73r2', user_karma=2, user_cake_day='cake day2', post_karma=1,
                comment_karma=1)


def test_server_post(post_schema: PostSchema, test_post: Post, replace_post: Post) -> None:
    response = requests.post(SERVER_URL, data=post_schema.dumps(test_post))
    assert response.status_code == RESPONSE_CREATED
    response = requests.get(SERVER_URL + '/')
    assert post_schema.loads(response.text, many=True) == [test_post, ]
    response = requests.post(SERVER_URL, data=post_schema.dumps(replace_post))
    assert response.status_code == RESPONSE_CREATED
    response = requests.get(SERVER_URL + '/')
    assert post_schema.loads(response.text, many=True) == [test_post, replace_post]
    requests.delete(SERVER_URL + '/' + test_post.id)
    requests.delete(SERVER_URL + '/' + replace_post.id)


def test_server_get_single(post_schema: PostSchema, test_post: Post) -> None:
    response = requests.get(SERVER_URL + '/' + test_post.id)
    assert response.status_code == RESPONSE_NOT_FOUND
    requests.post(SERVER_URL, data=post_schema.dumps(test_post))
    response = requests.get(SERVER_URL + '/' + test_post.id)
    assert response.status_code == RESPONSE_OK
    assert post_schema.loads(response.text) == test_post
    requests.delete(SERVER_URL + '/' + test_post.id)


def test_server_get_multiple(post_schema: PostSchema, test_post: Post) -> None:
    response = requests.get(SERVER_URL)
    assert post_schema.loads(response.text, many=True) == []
    requests.post(SERVER_URL, data=post_schema.dumps(test_post))
    response = requests.get(SERVER_URL)
    assert response.status_code == RESPONSE_OK
    assert post_schema.loads(response.text, many=True) == [test_post, ]
    requests.delete(SERVER_URL + '/' + test_post.id)


def test_server_delete(post_schema: PostSchema, test_post: Post) -> None:
    response = requests.delete(SERVER_URL + '/' + test_post.id)
    assert response.status_code == RESPONSE_NOT_FOUND
    requests.post(SERVER_URL, data=post_schema.dumps(test_post))
    response = requests.get(SERVER_URL + '/')
    assert post_schema.loads(response.text, many=True) == [test_post, ]
    response = requests.delete(SERVER_URL + '/' + test_post.id)
    assert response.status_code == RESPONSE_OK
    response = requests.get(SERVER_URL + '/')
    assert post_schema.loads(response.text, many=True) == []


def test_server_put(post_schema: PostSchema, test_post: Post, replace_post: Post) -> None:
    response = requests.put(SERVER_URL + '/' + test_post.id, data=post_schema.dumps(replace_post))
    assert response.status_code == RESPONSE_NOT_FOUND
    requests.post(SERVER_URL, data=post_schema.dumps(test_post))
    response = requests.put(SERVER_URL + '/' + test_post.id, data=post_schema.dumps(replace_post))
    assert response.status_code == RESPONSE_OK
    response = requests.get(SERVER_URL + '/' + replace_post.id)
    assert post_schema.loads(response.text) == replace_post
    requests.delete(SERVER_URL + '/' + replace_post.id)

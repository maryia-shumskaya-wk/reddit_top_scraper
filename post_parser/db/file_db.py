import io
import os
from datetime import datetime
from typing import List, Dict

from dateutil.parser import parse

from .base import DB
from .constants import POSTS_PER_PAGE
from .exceptions import PostNotFoundException
from ..post import Post
from ..utils import get_config

CONFIG = get_config().get('file', {})
OUTPUT_PATH = CONFIG.get('path', './output')
FILE_NAME = CONFIG.get('name', f'reddit-{datetime.now().strftime("%Y%m%d")}.txt')


def _filter_posts(posts: List[Post], query: Dict[str, str]) -> List[Post]:
    if 'category' in query:
        posts = [post for post in posts if post.post_category == query["category"]]
    if 'date' in query:
        posts = [post for post in posts if str(post.post_date.date()) == query["category"]]
    if 'minVotes' in query:
        posts = [post for post in posts if post.number_of_votes >= int(query["minVotes"])]
    if 'maxVotes' in query:
        posts = [post for post in posts if post.number_of_votes <= int(query["maxVotes"])]
    posts = sorted(posts, key=lambda post: post.id)

    pagination = query.get('pagination', '')
    last_id = query.get('lastPost', '')
    if pagination == 'true':
        if not last_id:
            page = 1
        else:
            index = len(posts)
            for num, post in enumerate(posts):
                if post.id == last_id:
                    index = num
                    break
            page = index // POSTS_PER_PAGE + 2
        posts = posts[POSTS_PER_PAGE * (page - 1): POSTS_PER_PAGE * page]
    else:
        if last_id:
            posts = []

    return posts


class FileDB(DB):
    def __init__(self) -> None:
        self.current_posts: List[Post] = []
        self.path: str = os.path.join(OUTPUT_PATH, FILE_NAME)
        self.create()
        self._init_from_file()

    def _write_to_file(self) -> None:
        with io.open(self.path, 'w', encoding='utf-8') as file:
            file.writelines([str(post) for post in self.current_posts])

    def _init_from_file(self) -> None:
        try:
            with io.open(self.path, 'r', encoding='utf-8') as file:
                for line in file.readlines():
                    _, post_url, username, user_karma, user_cake_day, post_karma, comment_karma, post_date, \
                    number_of_comments, number_of_votes, post_category = line.replace('\n', '').split(';')
                    self.current_posts.append(
                        Post(post_url=post_url, username=username, user_karma=int(user_karma),
                             user_cake_day=user_cake_day, post_karma=int(post_karma),
                             comment_karma=int(comment_karma), post_date=parse(post_date),
                             number_of_comments=int(number_of_comments), number_of_votes=int(number_of_votes),
                             post_category=post_category))
        except FileNotFoundError:
            pass

    def count(self) -> int:
        return len(self.current_posts)

    def drop(self) -> None:
        with io.open(self.path, 'w', encoding='utf-8'):
            pass

    def create(self) -> None:
        try:
            os.makedirs(OUTPUT_PATH)
        except FileExistsError:
            pass
        try:
            with io.open(self.path, 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            with io.open(self.path, 'w', encoding='utf-8'):
                pass

    def get_all(self) -> List[Post]:
        return self.current_posts

    def get_filtered(self, query: Dict[str, str]) -> List[Post]:
        return _filter_posts(self.current_posts.copy(), query)

    def get_by_id(self, post_id: str) -> Post:
        for post in self.current_posts:
            if post.id == post_id:
                return post
        raise PostNotFoundException

    def add(self, post: Post) -> bool:
        if post not in self.current_posts:
            self.current_posts.append(post)
            self._write_to_file()
            return True
        return False

    def update(self, post_id: str, new_post: Post) -> bool:
        try:
            post = self.get_by_id(post_id)
            if new_post not in self.current_posts:
                self.current_posts = [p if p != post else new_post for p in self.current_posts]
                self._write_to_file()
            else:
                raise PostNotFoundException
            return True
        except PostNotFoundException:
            return False

    def delete(self, post_id: str) -> bool:
        try:
            post = self.get_by_id(post_id)
            self.current_posts.remove(post)
            self._write_to_file()
            return True
        except PostNotFoundException:
            return False

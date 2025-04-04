import logging
from typing import List, Dict, Any

from pymongo import MongoClient, DESCENDING
from pymongo.database import Collection
from pymongo.errors import CollectionInvalid

from .base import DB
from .constants import POSTS_PER_PAGE
from .exceptions import PostNotFoundException
from ..post import Post
from ..utils import get_config

_LOGGER = logging.getLogger(__name__)

CONFIG = get_config().get('mongo', {})

POSTS_COLLECTION_NAME = CONFIG.get('posts_collection_name', 'posts')
USERS_COLLECTION_NAME = CONFIG.get('users_collection_name', 'users')

POST_ONLY_FIELDS = {
    '_id': 0,
    'id': 0
}
USER_ONLY_FIELDS = {
    '_id': 0
}


def _generate_post_document(post: Post) -> Dict[str, Any]:
    return {
        'id': post.id,
        'post_url': post.post_url,
        'post_date': post.post_date,
        'number_of_comments': post.number_of_comments,
        'number_of_votes': post.number_of_votes,
        'post_category': post.post_category,
        'username': post.username
    }


def _generate_user_document(post: Post) -> Dict[str, Any]:
    return {
            'username': post.username,
            'user_karma': post.user_karma,
            'user_cake_day': post.user_cake_day,
            'post_karma': post.post_karma,
            'comment_karma': post.comment_karma
        }


def _generate_filter(query: Dict[str, str]) -> Dict[str, Any]:
    find: Dict[str, Any] = {}
    if 'category' in query:
        find['post_category'] = query['category']
    if 'date' in query:
        find['post_date'] = query['date']
    if 'minVotes' in query:
        find['number_of_votes'] = {'$gte': int(query['minVotes'])}
    if 'maxVotes' in query:
        if 'number_of_votes' not in find:
            find['number_of_votes'] = {}
        find['number_of_votes']['$lte'] = int(query['maxVotes'])
    if 'lastPost' in query:
        find['id'] = {'$gt': query['lastPost']}
    return find


class MongoDB(DB):

    def __init__(self, conn_string: str) -> None:
        client = MongoClient(conn_string)

        self.db = client.get_database()
        self.create()
        self.posts: Collection = self.db.get_collection(POSTS_COLLECTION_NAME)
        self.users: Collection = self.db.get_collection(USERS_COLLECTION_NAME)

    def _post_exists(self, post_id: str) -> bool:
        return self.posts.count_documents({'id': post_id}) == 1

    def _user_exists(self, username: str) -> bool:
        return self.users.count_documents({'username': username}) == 1

    def count(self) -> int:
        return self.db.get_collection(POSTS_COLLECTION_NAME).count()

    def drop(self) -> None:
        self.db.drop_collection(POSTS_COLLECTION_NAME)
        self.db.drop_collection(USERS_COLLECTION_NAME)

    def create(self) -> None:
        try:
            self.db.create_collection(POSTS_COLLECTION_NAME)
            self.db.get_collection(POSTS_COLLECTION_NAME).create_index([('id', DESCENDING)], unique=True)
            self.db.create_collection(USERS_COLLECTION_NAME)
            self.db.get_collection(USERS_COLLECTION_NAME).create_index([('username', DESCENDING)], unique=True)
        except CollectionInvalid:
            _LOGGER.info('Collections already exists')

    def get_all(self) -> List[Post]:
        results = self.posts.find({}, POST_ONLY_FIELDS)
        posts = []
        for post in results:
            user = self.users.find_one({'username': post['username']}, USER_ONLY_FIELDS)
            merged = {**user, **post}
            posts.append(Post(**merged))
        return posts

    def get_filtered(self, query: Dict[str, str]) -> List[Post]:
        results = self.posts.find(_generate_filter(query), POST_ONLY_FIELDS).sort('id')
        if query.get('pagination', '') == 'true':
            results = results.limit(POSTS_PER_PAGE)
        posts = []
        for post in results:
            user = self.users.find_one({'username': post['username']}, USER_ONLY_FIELDS)
            merged = {**user, **post}
            posts.append(Post(**merged))
        return posts

    def get_by_id(self, post_id: str) -> Post:
        if not self._post_exists(post_id):
            raise PostNotFoundException
        post = self.posts.find_one({'id': post_id}, POST_ONLY_FIELDS)
        user = self.users.find_one({'username': post['username']}, USER_ONLY_FIELDS)
        merged = {**post, **user}
        return Post(**merged)

    def add(self, post: Post) -> bool:
        if self._post_exists(post.id):
            return False
        self.posts.insert_one(_generate_post_document(post))
        if not self._user_exists(post.username):
            self.users.insert_one(_generate_user_document(post))
        else:
            self.users.find_one_and_replace({'username': post.username}, _generate_user_document(post))
        return True

    def update(self, post_id: str, new_post: Post) -> bool:
        if not self._post_exists(post_id):
            return False
        self.posts.find_one_and_replace({'id': post_id}, _generate_post_document(new_post))
        if self._user_exists(new_post.username):
            self.users.find_one_and_replace({'username': new_post.username}, _generate_user_document(new_post))
        else:
            self.users.insert_one(_generate_user_document(new_post))
        return True

    def delete(self, post_id: str) -> bool:
        if not self._post_exists(post_id):
            return False
        self.posts.delete_one({'id': post_id})
        return True

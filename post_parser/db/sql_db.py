import logging
from typing import List, Dict

import psycopg2

from .base import DB
from .constants import POSTS_PER_PAGE
from .exceptions import PostNotFoundException
from ..post import Post

_LOGGER = logging.getLogger(__name__)

DROP_TABLES = '''DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;
'''

CREATE_TABLES = '''CREATE TABLE IF NOT EXISTS users(
username varchar not null,
user_karma bigint not null,
user_cake_day varchar not null,
post_karma bigint not null,
comment_karma bigint not null,
PRIMARY KEY (username)
);

CREATE TABLE IF NOT EXISTS posts (
id char(32),
post_url varchar not null,
post_date timestamp with time zone not null,
number_of_comments int not null,
number_of_votes bigint not null,
post_category varchar not null,
user_name varchar not null,
PRIMARY KEY (id),
CONSTRAINT fk_user
    FOREIGN KEY(user_name)
        REFERENCES users(username)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
'''

POST_TABLE_LENGTH = '''SELECT COUNT(*)
FROM posts p;
'''

SELECT_POSTS_FILTERED = '''SELECT p.post_url, u.username, u.user_karma, u.user_cake_day, u.post_karma, u.comment_karma,
    p.post_date, p.number_of_comments, p.number_of_votes, p.post_category
FROM posts p
INNER JOIN users u
ON u.username = p.user_name
{}
ORDER BY p.id ASC
{};
'''

SELECT_ALL_POSTS = '''SELECT p.post_url, u.username, u.user_karma, u.user_cake_day, u.post_karma, u.comment_karma,
    p.post_date, p.number_of_comments, p.number_of_votes, p.post_category
FROM posts p
INNER JOIN users u
ON u.username = p.user_name;
'''

SELECT_POST_BY_ID = '''SELECT p.post_url, u.username, u.user_karma, u.user_cake_day, u.post_karma, u.comment_karma,
    p.post_date, p.number_of_comments, p.number_of_votes, p.post_category
FROM posts p
INNER JOIN users u
ON u.username = p.user_name
WHERE p.id = %(post_id)s;
'''

FIND_POST_BY_ID = '''SELECT COUNT(*)
FROM posts p
WHERE p.id = %(post_id)s;
'''

INSERT_USER = '''INSERT INTO users
VALUES (%(username)s, %(user_karma)s, %(user_cake_day)s, %(post_karma)s, %(comment_karma)s)
ON CONFLICT DO NOTHING;
'''

INSERT_POST = '''INSERT INTO posts
VALUES (%(id)s, %(post_url)s, %(post_date)s, %(number_of_comments)s, %(number_of_votes)s, %(post_category)s,
%(username)s);
'''

DELETE_POST_BY_ID = '''DELETE FROM posts p
WHERE p.id = %(post_id)s;
'''

UPDATE_POST_BY_ID = '''
INSERT INTO users
VALUES (%(username)s, %(user_karma)s, %(user_cake_day)s, %(post_karma)s, %(comment_karma)s)
ON CONFLICT (username) DO UPDATE SET
    user_karma = %(user_karma)s,
    user_cake_day = %(user_cake_day)s,
    post_karma = %(post_karma)s,
    comment_karma = %(comment_karma)s;

UPDATE posts p
SET id = %(id)s,
    post_url = %(post_url)s,
    post_date = %(post_date)s,
    number_of_comments = %(number_of_comments)s,
    number_of_votes = %(number_of_votes)s,
    post_category = %(post_category)s,
    user_name = %(username)s
WHERE p.id = %(update_id)s;
'''

MIN_VOTES_NAME = 'minVotes'
MAX_VOTES_NAME = 'maxVotes'
CATEGORY_NAME = 'category'
DATE_NAME = 'date'
LAST_POST_NAME = 'lastPost'
PAGINATION_NAME = 'pagination'


def _generate_filtered_select_clause(query: Dict[str, str]) -> str:
    if not query:
        return SELECT_ALL_POSTS
    statements = []
    limit = ''
    if CATEGORY_NAME in query:
        statements.append('p.post_category = %(category)s')
    if DATE_NAME in query:
        statements.append(f'DATE(p.post_date) = %(date)s')
    if MIN_VOTES_NAME in query:
        statements.append(f'p.number_of_votes >= %(min_votes)s')
    if MAX_VOTES_NAME in query:
        statements.append(f'p.number_of_votes <=  %(max_votes)s')
    page = query.get(PAGINATION_NAME, '')
    if LAST_POST_NAME in query:
        statements.insert(0, f'p.id > %(last_post)s')
    if page == 'true':
        limit = f'LIMIT {POSTS_PER_PAGE}'
    if len(statements) == 0:
        where = ''
    else:
        where = 'WHERE ' + ' AND '.join(statements)
    return SELECT_POSTS_FILTERED.format(where, limit)


class PostgresDB(DB):
    def __init__(self, name: str, user: str, password: str, host: str, port: int) -> None:
        self.conn: psycopg2.connect = psycopg2.connect(dbname=name, user=user, password=password, host=host, port=port)
        self.cursor: psycopg2.extensions.cursor = self.conn.cursor()
        self.create()

    def count(self) -> int:
        self.cursor.execute(POST_TABLE_LENGTH)
        res = self.cursor.fetchone()
        return res[0]

    def drop(self) -> None:
        self.cursor.execute(DROP_TABLES)
        self.conn.commit()

    def create(self) -> None:
        self.cursor.execute(CREATE_TABLES)
        self.conn.commit()

    def get_all(self) -> List[Post]:
        self.cursor.execute(SELECT_ALL_POSTS)
        rows = self.cursor.fetchall()
        results = [Post(*row) for row in rows]
        return results

    def get_filtered(self, query: Dict[str, str]) -> List[Post]:
        self.cursor.execute(_generate_filtered_select_clause(query), {
            'min_votes': int(query.get(MIN_VOTES_NAME, '0')), 'max_votes': int(query.get(MAX_VOTES_NAME, '0')),
            'category': query.get(CATEGORY_NAME, ''), 'date': query.get(DATE_NAME, ''),
            'last_post': query.get(LAST_POST_NAME, '')
        })
        rows = self.cursor.fetchall()
        results = [Post(*row) for row in rows]
        return results

    def get_by_id(self, post_id: str) -> Post:
        self.cursor.execute(SELECT_POST_BY_ID, {'post_id': post_id})
        results = self.cursor.fetchone()
        if results:
            return Post(*results)
        raise PostNotFoundException

    def add(self, post: Post) -> bool:
        try:

            self.cursor.execute(INSERT_USER, {'username': post.username, 'user_karma': post.user_karma,
                                              'user_cake_day': post.user_cake_day, 'post_karma': post.post_karma,
                                              'comment_karma': post.comment_karma})

            self.cursor.execute(INSERT_POST, {'id': post.id, 'post_url': post.post_url, 'post_date': post.post_date,
                                              'number_of_comments': post.number_of_comments, 'username': post.username,
                                              'number_of_votes': post.number_of_votes,
                                              'post_category': post.post_category})

            self.conn.commit()
            return True
        except psycopg2.errors.UniqueViolation:
            self.conn.commit()
            return False

    def update(self, post_id: str, new_post: Post) -> bool:
        try:
            old_post = self.get_by_id(post_id)
            self.cursor.execute(UPDATE_POST_BY_ID, {'username': new_post.username, 'user_karma': new_post.user_karma,
                                                    'user_cake_day': new_post.user_cake_day,
                                                    'post_karma': new_post.post_karma,
                                                    'comment_karma': new_post.comment_karma, 'id': new_post.id,
                                                    'post_url': new_post.post_url, 'post_date': new_post.post_date,
                                                    'number_of_comments': new_post.number_of_comments,
                                                    'number_of_votes': new_post.number_of_votes,
                                                    'update_username': old_post.username,
                                                    'post_category': new_post.post_category, 'update_id': post_id})
            self.conn.commit()
            return True
        except PostNotFoundException:
            pass
        return False

    def delete(self, post_id: str) -> bool:
        try:
            self.get_by_id(post_id)
            self.cursor.execute(DELETE_POST_BY_ID, {'post_id': post_id})
            self.conn.commit()
            return True
        except PostNotFoundException:
            return False

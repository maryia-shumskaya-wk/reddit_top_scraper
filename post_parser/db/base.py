from abc import ABC, abstractmethod
from typing import List, Dict

from post_parser.post import Post


class DB(ABC):
    @abstractmethod
    def count(self) -> int:
        """
        Returns number of rows in post table
        """
        ...

    @abstractmethod
    def drop(self) -> None:
        """
        Drops all tables or collections
        """
        ...

    @abstractmethod
    def create(self) -> None:
        """
        Creates all tables
        """
        ...

    @abstractmethod
    def get_filtered(self, query: Dict[str, str]) -> List[Post]:
        """
        Gets posts by filter
        """
        ...

    @abstractmethod
    def get_all(self) -> List[Post]:
        """
        Gets all posts
        """
        ...

    @abstractmethod
    def get_by_id(self, post_id: str) -> Post:
        """
        Gets post with post_id
        :param post_id: id of post
        :return: Post
        """
        ...

    @abstractmethod
    def add(self, post: Post) -> bool:
        """
        Adds post
        :param post: Post
        :return: True if post was added else False
        """
        ...

    @abstractmethod
    def update(self, post_id: str, post: Post) -> bool:
        """
        Updates post with post_id
        :param post_id: id of post you want to edit
        :param post: data to edit
        :return: True if post was updated else False
        """
        ...

    @abstractmethod
    def delete(self, post_id: str) -> bool:
        """
        Deletes post with post_id
        :param post_id: id of post you want to delete
        :return: True if post was deleted else False
        """
        ...

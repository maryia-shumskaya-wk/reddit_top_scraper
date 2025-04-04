from typing import Any

from marshmallow import Schema, post_load

from .post import Post


class PostSchema(Schema):
    class Meta:
        fields = ('id', 'post_url', 'username', 'user_karma', 'user_cake_day', 'post_karma', 'comment_karma',
                  'post_date', 'number_of_comments', 'number_of_votes', 'post_category')

    @post_load
    def make_post(self, data: dict, **kwargs: Any) -> Post:

        try:
            del data['id']
        except KeyError:
            pass

        return Post(**data)

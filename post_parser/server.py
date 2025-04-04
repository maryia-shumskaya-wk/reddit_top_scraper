import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Any, Type, Callable
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv

from .db import DB, PostNotFoundException, MongoDB, PostgresDB, FileDB
from .post_schema import PostSchema

_LOGGER = logging.getLogger(__name__)

IP_ADDRESS = '127.0.0.1'
PORT = 8087

CONTENT_LENGTH_HEADER = 'Content-Length'
CONTENT_TYPE_HEADER = 'Content-Type'
CONTENT_TYPE_JSON = 'application/json'
CORS_HEADER = 'Access-Control-Allow-Origin'
ALLOW_ALL = '*'

RESPONSE_OK = 200
RESPONSE_CREATED = 201
RESPONSE_NOT_FOUND = 404

POST_SCHEMA = PostSchema()
POSTS_SCHEMA = PostSchema(many=True)


def _split_url_path(url_path: str) -> List[str]:
    """
    Splits path /path/to/endpoint to list ['path', 'to', 'endpoint']
    """
    separated = url_path.split('/')

    try:
        if not separated[0]:
            del separated[0]

        if not separated[-1]:
            del separated[-1]
    except IndexError:
        return []

    return separated


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, db: DB, *args: Any, **kwargs: Any):
        self.db = db
        super(RequestHandler, self).__init__(*args, **kwargs)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path_components = _split_url_path(parsed_url.path)
        query_dict = dict(parse_qsl(parsed_url.query))

        if len(path_components) > 2 or len(path_components) == 0 or 'posts' not in path_components[0]:
            _LOGGER.info(f'GET {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()
            return

        if len(path_components) == 1:
            _LOGGER.info(f'GET {self.path} {RESPONSE_OK}')
            self.send_response(RESPONSE_OK)
            self.send_header(CONTENT_TYPE_HEADER, CONTENT_TYPE_JSON)
            self.send_header(CORS_HEADER, ALLOW_ALL)
            self.end_headers()
            if query_dict.get('pagination', ''):
                posts = self.db.get_filtered(query_dict)
            else:
                posts = self.db.get_all()
            self.wfile.write(POSTS_SCHEMA.dumps(posts).encode('ascii'))
            return

        try:
            post = self.db.get_by_id(path_components[1])
            _LOGGER.info(f'GET {self.path} {RESPONSE_OK}')
            self.send_response(RESPONSE_OK)
            self.send_header(CONTENT_TYPE_HEADER, CONTENT_TYPE_JSON)
            self.end_headers()
            self.wfile.write(POST_SCHEMA.dumps(post).encode('utf-8'))
        except PostNotFoundException:
            _LOGGER.info(f'GET {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()

    def do_POST(self) -> None:
        path_components = _split_url_path(self.path)

        if len(path_components) != 1 or path_components[0] != 'posts':
            _LOGGER.info(f'POST {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()
            return

        content_len = int(self.headers.get(CONTENT_LENGTH_HEADER, 0))
        body = self.rfile.read(content_len).decode(encoding='utf-8')
        post = POST_SCHEMA.loads(body)

        success = self.db.add(post)
        if success:
            _LOGGER.info(f'POST {self.path} {RESPONSE_CREATED}')
            self.send_response(RESPONSE_CREATED)
            self.send_header(CONTENT_TYPE_HEADER, CONTENT_TYPE_JSON)
            self.end_headers()
            self.wfile.write(json.dumps({post.id: self.db.count()}).encode('utf-8'))
        else:
            _LOGGER.info(f'POST {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()

    def do_DELETE(self) -> None:
        path_components = _split_url_path(self.path)

        if len(path_components) != 2 or path_components[0] != 'posts':
            _LOGGER.info(f'DELETE {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()
            return

        success = self.db.delete(path_components[1])
        if success:
            _LOGGER.info(f'DELETE {self.path} {RESPONSE_OK}')
            self.send_response(RESPONSE_OK)
            self.end_headers()
        else:
            _LOGGER.info(f'DELETE {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()

    def do_PUT(self) -> None:
        path_components = _split_url_path(self.path)

        if len(path_components) != 2 or path_components[0] != 'posts':
            _LOGGER.info(f'PUT {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()
            return

        content_len = int(self.headers.get(CONTENT_LENGTH_HEADER, 0))
        body = self.rfile.read(content_len).decode(encoding='utf-8')
        new_post = POST_SCHEMA.loads(body)

        success = self.db.update(path_components[1], new_post)
        if success:
            _LOGGER.info(f'PUT {self.path} {RESPONSE_OK}')
            self.send_response(RESPONSE_OK)
            self.end_headers()
        else:
            _LOGGER.info(f'PUT {self.path} {RESPONSE_NOT_FOUND}')
            self.send_response(RESPONSE_NOT_FOUND)
            self.end_headers()


def request_handler_wrapper(request_handler: Type[RequestHandler], db: DB) -> Callable[[Any, Any], RequestHandler]:
    def wrapper(*args: Any, **kwargs: Any) -> RequestHandler:
        return request_handler(db, *args, **kwargs)

    return wrapper


def run(database_name: str, server_class: Type[ThreadingHTTPServer] = ThreadingHTTPServer,
        handler_class: Type[RequestHandler] = RequestHandler) -> None:
    load_dotenv()
    logging.basicConfig(filename='server.log', filemode='w', level=logging.INFO, format='%(asctime)s %(message)s')
    db: DB
    if database_name == 'mongo':
        conn_string = os.getenv('MONGO_CONNECTION', 'mongodb://localhost:27017')
        db = MongoDB(conn_string)

        _LOGGER.info('MongoDB connected')
    elif database_name == 'postgres':
        name = os.getenv('POSTGRES_NAME', 'postgres')
        user = os.getenv('POSTGRES_USERNAME', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'root')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = int(os.getenv('POSTGRES_PORT', '5432'))
        db = PostgresDB(name=name, user=user, password=password, host=host, port=port)

        _LOGGER.info('PostgreSQL connected')
    else:
        db = FileDB()

        _LOGGER.info('File created')

    server_address = (IP_ADDRESS, PORT)
    handler = request_handler_wrapper(handler_class, db)
    httpd = server_class(server_address, handler)

    _LOGGER.info('Start listening http on port {}'.format(PORT))

    httpd.serve_forever()

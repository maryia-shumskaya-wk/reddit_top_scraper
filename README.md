# Reddit month top parser
A python script that parses reddit month top.

## Requirements
* Python 3.7+
* Docker


## Quick start
Create virtual environment and install requirements:

For Linux:
```shell script
sudo apt-get install -y python3-dev postgresql-10 postgresql-server-dev-10
python -m venv venv
source /venv/bin/activate
python -m pip install -r requirements.txt
pre-commit install
```

For Windows:
```shell script
python -m venv venv
\venv\Scripts\activate.bat
pip install -r requirements.txt
pre-commit install
```
First you need to run server:
```shell script
python server.py
```
You have to run parser script like this:
```shell script
python run.py
```

## Available flags
* ```-h``` or ```--help``` for help information
* ```-p``` or ```--posts``` sets required number of posts to be parsed
* ```-w``` or ```--workers``` sets a number of worker threads
* ```--offset``` sets a posts offset

## pytest testing
To run pytest testing you should run:
```shell script
python -m pytest --cov=post_parser/ tests/
```


## mypy testing
To run mypy testing you should run:
```shell script
mypy --disallow-untyped-defs --ignore-missing-imports run.py server.py post_parser/ tests/
```

## Docker support
To run docker container you should run:
```shell script
docker-compose up
```

## .env example
I created it in root directory and it looks like:
```ini
POSTGRES_NAME=<your_postgres_db_name>
POSTGRES_HOST=<your_postgres_db_host>
POSTGRES_USERNAME=<your_postgres_username>
POSTGRES_PASSWORD=<your_postgres_password>
POSTGRES_PORT=<your_postgres_db_port>

MONGO_CONNECTION=<mongo_db_connection_string_with_database>
```
If you are not using mongo or postgres db you can remove corresponding lines

## config.yml example
```yaml
file:
  path: ./output
  name: reddit.txt
mongo:
  posts_collection_name: posts
  users_collection_name: users
```

## To run web application
Run chrome like this:
On Linux:
```shell script
google-chrome --disable-web-security -–allow-file-access-from-files
```

On Windows go to chrome folder:
```shell script
chrome.exe --disable-web-security -–allow-file-access-from-files
```

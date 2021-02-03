import os
from typing import List

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

config = Config('.env')

API_PREFIX = '/d/api'

VERSION = '0.0.1'

PROJECT_NAME: str = config('PROJECT_NAME', default='')

API_KEY: str = config('API_KEY', default='admin@123')

# get the default selenium server running in container
SELENIUM_SERVER: str = config('SELENIUM_SERVER_DEFAULT')

# get default username and password for admin
ADMIN_USER: str = config('ADMIN_USER', default="admin")
ADMIN_PASS: str = config('ADMIN_PASS', default="admin")


TIME_INTERVAL_NEW_MESSAGES: int = int(config('TIME_INTERVAL_NEW_MESSAGES'))

# use external selenium grid
SELENIUM_SERVER_CUSTOM: str = config('SELENIUM_SERVER_CUSTOM', default='')

if SELENIUM_SERVER_CUSTOM:
    SELENIUM_SERVER = SELENIUM_SERVER_CUSTOM

ALLOWED_HOSTS: List[str] = config(
    'ALLOWED_HOSTS',
    cast=CommaSeparatedStrings,
    default="",
)

ALLOWED_EXTENSIONS = (
    "avi",
    "mp4",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "mp3",
    "doc",
    "docx",
    "pdf",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIREFOX_CACHE_PATH = os.path.join(BASE_DIR, "firefox_cache")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")

DEBUG: bool = config('DEBUG', cast=bool, default=False)

# Path to temporarily store static files like images
STATIC_FILES_PATH = os.path.join(BASE_DIR, "static")

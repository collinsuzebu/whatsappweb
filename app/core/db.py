import os
import sqlite3

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.config import SQLITE_DB_PATH
from app.core.models import UserInDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# password
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# db connection
def db_connect(db_path=SQLITE_DB_PATH):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


# dabase queries
def create_user_table(cursor):
    q = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY  AUTOINCREMENT,
            username text NOT NULL UNIQUE,
            hashed_password NOT NULL,
            email text,
            full_name text,
            disabled integer
        )
    """
    cursor.execute(q)
    return True


def close_con_cur(con, cur):
    cur.close()
    con.close()


def get_db_user(cursor, username: str, password: str):
    q = """SELECT * FROM users WHERE username = ?"""
    cursor.execute(q, (username, ))
    user = cursor.fetchone()
    user = dict(user) if user else None
    if user:
        return UserInDB(**user)

def add_admin_user(con, username, password):
    q = """
        INSERT OR IGNORE INTO users (username, hashed_password, disabled)
        VALUES (?, ?, ?)
        """
    hashed_password = get_password_hash(password)
    cursor = con.cursor()

    cursor.execute(q, (username, hashed_password, 0))
    con.commit()

    close_con_cur(con, cursor)
    return True


# Authentication
def authenticate_user(username: str, password: str):
    con = db_connect()
    cur = con.cursor()

    user = get_db_user(cur, username, password)
    close_con_cur(con, cur)

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# def get_current_user(token: str = Depends(oauth2_scheme)):
#
#     credentials_exception = HTTPException(
#         status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
#     )
#
#     try:
#         payload = jwt.decode(token, S)
#     except Exception as e:
#         raise
#
#     user = authenticate_user(token)

from typing import Callable
from fastapi import FastAPI

from app.core.global_vars import timers, drivers
from app.core.config import ADMIN_USER, ADMIN_PASS
from app.core.utils import remove_profile_dir, remove_firefox_caches
from app.core.db import db_connect, create_user_table, add_admin_user



def stop_timers_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        for timer in timers.values():
            timer.stop()
    return stop_app


def stop_drivers_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        for driver in drivers.values():
            driver.close()
    return stop_app


def remove_profiledir_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        # empty profile directory on shutdown which include mostly qr images
        # also delete firefox caches
        remove_profile_dir()
        remove_firefox_caches()
    return stop_app


def start_db_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        con = db_connect()
        cur = con.cursor()
        create_user_table(cur)
        add_admin_user(con, ADMIN_USER, ADMIN_PASS)
    return start_app

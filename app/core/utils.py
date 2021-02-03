import re
import os
import glob
import json
import shutil
import sqlite3
from datetime import datetime

import requests
from PIL import Image, ImageOps

from app.wrapper.webwhatsapi import WhatsAPIDriverStatus
from app.core.global_vars import drivers, services, timers, drivers_created_time
from app.core.config import STATIC_FILES_PATH, BASE_DIR

# chmod +x docker-run.sh
# ./docker-run.sh

def get_current_time():
    d = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    return d


def is_admin(route: str):
    admin_route = re.compile('/d/api/admin/?')
    static_route = re.compile('/static(.*)?')

    admin = admin_route.match(route)
    static = static_route.match(route)

    if admin or static:
        return True
    return False

def create_or_get_static_profile_path(client_id):
    profile_path = os.path.join(STATIC_FILES_PATH, "profiles", str(client_id))
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    return profile_path

def remove_profile_dir():
    profile_path = os.path.join(STATIC_FILES_PATH, "profiles")
    shutil.rmtree(profile_path)

def remove_firefox_caches():
    for directory in glob(os.path.join(BASE_DIR, "firefox_cache_*")):
        shutil.rmtree(directory)

def get_qr_image_path(client_id, with_border=False):
    img_title = "qrcode_" + client_id + ".png"
    if with_border:
        img_title = 'b_' + img_title
    profile_path = create_or_get_static_profile_path(client_id)
    img_path = os.path.join(profile_path, img_title)
    return img_path

def process_image(img_path, client_id):
    img = Image.open(img_path)
    img_with_border = ImageOps.expand(img, border=100, fill='white')
    img_path = get_qr_image_path(client_id, with_border=True)
    img_with_border.save(img_path)
    return img_path

def send_qr_email(arg):
    pass

def convert_phoneno_to_id(phone_number):
	phone_number = re.search(r'\d+', phone_number).group(0)
	return f"{phone_number}{'@c.us'}"


def send_to_external_service(url, data):
    """send message to external service for processing"""
    headers = {'Content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.content


def get_client_info(client_id):
    """Get the status of a perticular client"""
    if client_id not in drivers:
        return None

    driver_status = drivers[client_id].get_status()
    is_alive = False
    is_logged_in = False
    if (
        driver_status == WhatsAPIDriverStatus.NotLoggedIn
        or driver_status == WhatsAPIDriverStatus.LoggedIn
    ):
        is_alive = True
    if driver_status == WhatsAPIDriverStatus.LoggedIn:
        is_logged_in = True

    service_url = services[client_id]
    created_at = drivers_created_time[client_id]

    return {
        "client_id": client_id,
        "driver_status": is_logged_in,
        "service_url": service_url,
        "created_at": created_at,
        "is_timer": bool(timers[client_id]) and timers[client_id].is_running,
    }


def get_no_clients() -> int:
    """Get the number of active and inactive clients"""
    actives = 0
    inactives = 0
    for client_id, driver in drivers.copy().items():
        if driver.get_status() == WhatsAPIDriverStatus.LoggedIn:
            actives += 1
        else:
            inactives += 1
    total = actives + inactives
    return total, actives, inactives

def get_clients_info():
    all_clients = []
    for client_id in drivers.copy():
        client_info = get_client_info(client_id)
        all_clients.append(client_info)
    return all_clients

def get_static_image(img_name):
    img_path = os.path.join(STATIC_FILES_PATH, "images", img_name)
    return img_path

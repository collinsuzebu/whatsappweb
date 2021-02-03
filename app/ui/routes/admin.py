import os
import asyncio

from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.responses import Response, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.requestsvar import gbl
from app.core.actions import init_timer, init_client, delete_client
from app.core.global_vars import drivers, services, drivers_created_time
from app.core.db import authenticate_user, add_admin_user, db_connect
from app.core.config import PROJECT_NAME

from app.core.utils import (
    is_admin,
    get_no_clients,
    get_clients_info,
    get_current_time,
    get_qr_image_path,
    get_static_image
)


router = APIRouter()

security = HTTPBasic()

# pip install aiofiles
# pip install python-mulipart
# pip install bcrypt
templates = Jinja2Templates(directory="templates")


@router.get("/current")
async def send_state():
    loop = asyncio.get_event_loop()
    total_clients, no_active_clients, no_inactive_clients = await loop.run_in_executor(
        None, get_no_clients
    )
    clients_info = await loop.run_in_executor(None, get_clients_info)

    d = {
        "total_clients": total_clients,
        "no_active_clients": no_active_clients,
        "no_inactive_clients": no_inactive_clients,
        "clients_info": clients_info
    }
    return d


@router.get("/", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "project_name": PROJECT_NAME,
        }
    )


@router.get("/clients", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    user = authenticate_user(credentials.username, credentials.password)
    return templates.TemplateResponse(
        "admin-clients.html",
    )


@router.post('/client')
async def create_client(request: Request):
    """creates a new client and instantiate a driver for client"""

    created = False
    admin_json = await request.json()

    if not admin_json:
        return {
            "error": "expected required parameters 'clientID', 'serviceURL', API_KEY"
        }

    client_id = admin_json['clientID']
    service_url = admin_json['serviceURL']

    if client_id not in drivers:
        print('CLIENT ID NOT PRESENT')
        loop = asyncio.get_event_loop()
        drivers[client_id] = await loop.run_in_executor(None, init_client, client_id)

        # new_client = asyncio.create_task(init_client(client_id))
        # drivers[client_id] = await new_client

        drivers_created_time[client_id] = get_current_time()
        services[client_id] = service_url

        init_timer(client_id)
    created = True if drivers[client_id] else False
    created_at = drivers_created_time[client_id]

    return {'client_id':client_id, 'created': created, 'created_at': created_at}


@router.delete('/client/{client_id}')
async def delete_client_r(client_id, request: Request):
    """Delete all object related to client"""

    if not drivers.get(client_id):
        return {'error': 'client_id "{}" does not exists'.format(client_id)}

    preserve_cache = request.query_params.get('preserve_cache', False)
    delete_client(client_id, preserve_cache)

    return {'client_id': client_id, 'deleted': True}


@router.get('/screen/{client_id}')
async def get_qr(client_id: str, request: Request):
    img_path = get_qr_image_path(client_id, with_border=True)

    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")

    img_path = get_static_image("qr_image_not_found.png")
    return FileResponse(img_path, media_type="image/png")


@router.get('/screen/reload/{client_id}')
async def reload_qr(client_id: str):
    # if the client id exists and not none and it's not loggedIn then reload qr
    if (
        client_id in drivers and drivers[client_id]
        and drivers[client_id] != WhatsAPIDriverStatus.LoggedIn
    ):
        driver = drivers[client_id]
        loop = asyncio.get_event_loop()
        drivers[client_id] = await loop.run_in_executor(None, set_qr_code, driver)
        img_path = get_qr_image_path(client_id, with_border=True)
        return FileResponse(img_path, media_type="image/png")

    img_path = get_static_image("qr_image_not_found.png")
    return FileResponse(img_path, media_type="image/png")


@router.post('/users')
async def add_admin_user_route(request: Request):
    admin_json = await request.json()

    username = admin_json.get("username")
    password = admin_json.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="A username and password is required",
        )
    con = db_connect()
    add_admin_user(con, username, password)

    return {"created": True, "username": username}

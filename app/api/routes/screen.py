import os
from fastapi import APIRouter, Request
from fastapi.responses import Response, FileResponse


from app.wrapper.webwhatsapi import WhatsAPIDriverStatus

from app.core.requestsvar import gbl
from app.core.global_vars import timers, drivers
from app.core.config import BASE_DIR
from app.core.utils import get_qr_image_path
from app.core.actions import set_qr_code

# docker exec -t -i 23b1304d5bae sh
router = APIRouter()


@router.get('/{client_id}')
def get_qr(client_id: str, request: Request):
    img_path = get_qr_image_path(client_id, with_border=True)
    return FileResponse(img_path, media_type="image/png")


@router.get('/reload/{client_id}')
def reload_qr():
    # if the client id exists and not none and it's not loggedIn then reload qr
    if (
        client_id in drivers and drivers[client_id]
        and drivers[client_id] != WhatsAPIDriverStatus.LoggedIn
    ):
        set_qr_code(drivers[client_id])
        img_path = get_qr_image_path(client_id, with_border=True)
        return FileResponse(img_path, media_type="image/png")
    return {'error':'error reloading qr code'}

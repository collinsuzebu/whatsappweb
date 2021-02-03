from fastapi import APIRouter, Request

from app.wrapper.webwhatsapi import WhatsAPIDriverStatus

from app.core.requestsvar import gbl
from app.core.actions import RepeatedTimer
from app.core.global_vars import timers
from app.core.utils import convert_phoneno_to_id


router = APIRouter()


@router.post('/message/{chat_id}')
async def send_message(chat_id: str, request: Request):
    g = gbl()
    form_obj = await request.form()
    message = form_obj.get('message')

    chat_id = convert_phoneno_to_id(chat_id)
    if g.driver_status == WhatsAPIDriverStatus.LoggedIn:
        res = g.driver.send_message_to_id(chat_id, str(message))
        return {'success': "message sent successfully"}
    return {"error": "client '{}' is not loggedIn.".format(g.client_id)}

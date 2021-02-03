from fastapi import APIRouter

from app.ui.routes import admin
from app.api.routes import whatsappweb, chat, screen

router = APIRouter()
router.include_router(whatsappweb.router, tags=['whatsappweb'], prefix='/whatsappweb')
router.include_router(chat.router, tags=['chat'], prefix='/chat')
router.include_router(screen.router, tags=['screen'], prefix='/screen')
router.include_router(admin.router, tags=['admin'], prefix='/admin')

import types
import secrets
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.wrapper.webwhatsapi import WhatsAPIDriverStatus

from app.api.routes.api import router as api_router
from app.core import config
from app.core.requestsvar import global_request, gbl
from app.core.utils import is_admin, get_current_time
from app.core.global_vars import drivers, services, drivers_created_time
from app.core.actions import init_client, init_timer
from app.core.events import (
    start_db_handler,
    stop_timers_handler,
    stop_drivers_handler,
    remove_profiledir_handler
)



def get_application() -> FastAPI:
    application = FastAPI(
        title=config.PROJECT_NAME,
        debug=config.DEBUG,
        version=config.VERSION
    )

    @application.middleware("http")
    async def before_request(request: Request, call_next):
        # get all context from request
        admin = is_admin(request.url.path)
        client_id = request.headers.get('client_id')
        service_url = request.headers.get('service_url')
        api_key_client = request.headers.get('api_key')

        if not admin and not api_key_client:
            return JSONResponse(
                {"error": "api_key is required"},
                status_code=400
            )

        if not admin and not secrets.compare_digest(
            config.API_KEY, api_key_client
        ):
            return JSONResponse(
                {"error": "invalid api_key"},
                status_code=400
            )

        if client_id is None and not admin:
            return JSONResponse(
                {"error": "client_id is required"},
                status_code=400
            )

        if service_url is None and not admin:
            return JSONResponse(
                {"error": "service_url is required"},
                status_code=400
            )

        service_url_used = False

        if service_url and not services.get(client_id):
            for k, v in services.items():
                if v == service_url:
                    service_url_used = True
                    break

        if services.get(client_id) and services[client_id] != service_url:
            service_url_used = True

        if service_url_used:
            return JSONResponse(
                {"error": "the service_url is in use by another client"},
                status_code=400
            )

        var = types.SimpleNamespace(
            client_id=client_id,
            service_url=service_url,
        )
        global_request.set(var)

        # get current global request data
        g = gbl()

        acquire_semaphore(g.client_id)

        if not admin:
            loop = asyncio.get_event_loop()

            services[g.client_id] = service_url

            if g.client_id not in drivers:
                drivers[g.client_id] = await loop.run_in_executor(None, init_client, g.client_id)
                drivers_created_time[g.client_id] = get_current_time()

            g.driver = drivers[g.client_id]
            g.driver_status = WhatsAPIDriverStatus.Unknown

            if g.driver is not None:
                g.driver_status = g.driver.get_status()

            # If driver status is unkown, means driver has closed somehow, reopen it
            if (
                g.driver_status != WhatsAPIDriverStatus.NotLoggedIn
                and g.driver_status != WhatsAPIDriverStatus.LoggedIn
            ):
                # drivers[g.client_id] = init_client(g.client_id)
                drivers[g.client_id] = await loop.run_in_executor(None, init_client, g.client_id)
                g.driver_status = g.driver.get_status()

            init_timer(g.client_id)
        response = await call_next(request)
        release_semaphore(g.client_id)
        return response

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_HOSTS or ['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )

    application.add_event_handler("startup", start_db_handler(application))
    application.add_event_handler("shutdown", stop_timers_handler(application))
    application.add_event_handler("shutdown", stop_drivers_handler(application))
    application.add_event_handler("shutdown", remove_profiledir_handler(application))

    application.include_router(api_router, prefix=config.API_PREFIX)

    return application


app = get_application()

app.mount("/static", StaticFiles(directory="static"), name="static")

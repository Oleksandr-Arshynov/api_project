from ipaddress import ip_address
import re
import sys
from typing import Callable

import fastapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis


from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import auth.routes
import contacts.routes

from conf.config import config

contacts_api = FastAPI()

banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
    ip_address("127.0.0.1"),
]

origins = ["*"]

contacts_api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @contacts_api.middleware("http")
# async def ban_ips(request: Request, call_next: Callable):
#     ip = ip_address(request.client.host)
#     if ip in banned_ips:
#         return JSONResponse(status_code=fastapi.status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
#     response = await call_next(request)
#     return response

user_agent_ban_list = [r"Googlebot", r"Python-urllib"]


@contacts_api.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    print(request.headers.get("Authorization"))
    user_agent = request.headers.get("user-agent")
    print(user_agent)
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=fastapi.status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response


contacts_api.mount(
    "/static",
    StaticFiles(
        directory="/Users/oleksandrarshinov/Desktop/Documents/Repository/api_project/api_project/src/static"
    ),
    name="static",
)

contacts_api.include_router(contacts.routes.router)
contacts_api.include_router(auth.routes.router)


# підключення до Redis при старті додатка
@contacts_api.on_event("startup")
async def startup():
    r = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)


templates = Jinja2Templates(
    directory="/Users/oleksandrarshinov/Desktop/Documents/Repository/api_project/api_project/src/auth/templates"
)


@contacts_api.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Build group WebPython #16"}
    )


if __name__ == "__main__":
    uvicorn.run("main:contacts_api", host="0.0.0.0", port=8001, reload=True)

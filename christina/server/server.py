import os

from fastapi import FastAPI, staticfiles, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware

# noinspection PyUnresolvedReferences
import christina.env
from .routes import video, download, people, character, tag, proxy

app = FastAPI()

app.mount("/static", staticfiles.StaticFiles(directory=os.environ['DATA_DIR']), name="static")

app.include_router(video.router)
app.include_router(download.router)
app.include_router(people.router)
app.include_router(character.router)
app.include_router(tag.router)
app.include_router(proxy.router)


@app.exception_handler(Exception)
async def general_handler(request, exc):
    if not isinstance(exc, HTTPException):
        # convert any Exception to an HTTPException
        exc = HTTPException(500, repr(exc))

    return await http_exception_handler(request, exc)


@app.get('/')
def index():
    return 'Hello Christina'


# wrap the entire app so CORSMiddleware can handle non-HTTPExceptions
app = CORSMiddleware(
    app=app,
    allow_origins=list(filter(None, os.environ['CORS_ORIGINS'].splitlines())),
    allow_methods=["GET", 'POST', 'PUT', 'DELETE', 'PATCH'],
    allow_headers=["*"],
)

from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
import christina.env
from . import video, download
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(filter(None, os.environ['CORS_ORIGINS'].splitlines())),
    allow_methods=["GET", 'POST'],
    allow_headers=["*"],
)

app.mount("/static", staticfiles.StaticFiles(directory=os.environ['DATA_DIR']), name="static")

app.include_router(video.router)
app.include_router(download.router)


@app.get('/')
def index():
    return 'Hello Christina'

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import christina.env
from . import video
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(filter(None, os.environ['CORS_ORIGINS'].splitlines())),
    allow_methods=["GET", 'POST'],
    allow_headers=["*"],
)

app.include_router(video.router)


@app.get('/')
def index():
    return 'Hello Christina'

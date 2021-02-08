from flask import Flask
from .video import bp as video_bp
import christina.env

app = Flask(__name__)

app.register_blueprint(video_bp, url_prefix='/video')


@app.route('/')
def index():
    return 'Hello Christina'

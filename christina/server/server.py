from flask import Flask
from .video import bp as videoBP
import christina.env

app = Flask(__name__)

app.register_blueprint(videoBP, url_prefix='/video')


@app.route('/')
def index():
    return 'Hello Christina'

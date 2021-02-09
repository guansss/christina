import eventlet
eventlet.monkey_patch()  # nopep8


from flask import Flask
from flask_socketio import SocketIO
import os
import christina.env


app = Flask(__name__)
socketio = SocketIO(app, logger=True)

# should be imported after creating `socketio`
from .video import bp as video_bp  # nopep8

app.register_blueprint(video_bp, url_prefix='/video')


@app.route('/')
def index():
    return 'Hello Christina'


if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        use_reloader=False,
        certfile=os.environ['CERT'],
        keyfile=os.environ['CERT_KEY']
    )

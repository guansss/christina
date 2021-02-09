from flask import Blueprint, request, current_app
from flask_cors import cross_origin
from christina import video, net, scheduler
from christina.logger import get_logger

logger = get_logger(__name__)

try:
    from __main__ import socketio
except ImportError:
    # for some reason the main module will be named without the "christina" prefix
    # when running app via `flask run`
    from server.server import socketio

bp = Blueprint('video', __name__)


@bp.route('/download', methods=['POST'])
@cross_origin()
def download():
    try:
        video_model = video.download(request.json['url'], request.json['html'])

        return {'video': video_model.id}, 200
    except Exception as e:
        logger.exception(e)

        return {'message': repr(e)}, 400


def broadcast_progress():
    if net.download_tasks:
        tasks = [{key: getattr(task, key) for key in ['file', 'loaded', 'size']} for task in net.download_tasks]

        socketio.emit('progress', tasks)


scheduler.scheduler.add_job(func=broadcast_progress, trigger="interval", seconds=1)

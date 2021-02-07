from flask import Blueprint, request, current_app
from flask_cors import cross_origin
from christina import video

bp = Blueprint('video', __name__)


@bp.route('/download', methods=['POST'])
@cross_origin()
def download():
    try:
        videoModel = video.download(request.json['url'], request.json['html'])

        return {'video': videoModel.id}, 200
    except Exception as e:
        current_app.logger.error(e)

        return {'message': str(e)}, 400

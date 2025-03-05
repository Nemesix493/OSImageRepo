from pathlib import Path
import re
from os import makedirs, remove

from flask import Flask, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_mapping(
    UPLOAD_PATH=Path('/data').resolve()
)


def is_safe_path(path: Path) -> bool:
    forbidden_chars = r'[*?"<>|;&`\'\\]'
    return re.search(forbidden_chars, str(path)) is None


def is_in_upload_path(resolved_path: Path) -> bool:
    return resolved_path.is_relative_to(current_app.config['UPLOAD_PATH'])


@app.route("/<path:dir_path>", methods=['GET', 'POST', 'PATCH'])
def upload(dir_path):
    if request.method == 'GET':
        return get_views(dir_path)
    resolved_dir_path = current_app.config['UPLOAD_PATH'] / dir_path
    if not (is_safe_path(dir_path) and is_in_upload_path(resolved_dir_path)):
        return jsonify({'error_message': 'not valid path'}), 400
    func_method = {
        'POST': upload_post,
        'PATCH': upload_patch,
    }
    return func_method[request.method](resolved_dir_path)


def upload_post(resolved_dir_path: Path):
    if resolved_dir_path.exists():
        return jsonify({'error_message': 'try to POST on existing directory'}), 400
    makedirs(resolved_dir_path)
    for file in request.files.values():
        file.save(resolved_dir_path / secure_filename(file.filename))
    return jsonify({'message': 'Successfully added'}), 201


def upload_patch(resolved_dir_path: Path):
    if not resolved_dir_path.exists():
        return jsonify({'error_message': 'try to PATCH on not existing directory'}), 400
    for file in request.files.values():
        file_path = resolved_dir_path / secure_filename(file.filename)
        if file_path.exists():
            remove(file_path)
        file.save(file_path)
    return jsonify({'message': 'Successfully updated'}), 200


def get_views(view_path=None):
    redirect_path = '/files/'
    if view_path is not None:
        redirect_path += view_path
    response = Response(status=200)
    response.headers['X-Accel-Redirect'] = redirect_path
    del response.headers['Content-Type']
    return response


app.route('/')(get_views)

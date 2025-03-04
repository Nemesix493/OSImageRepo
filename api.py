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
    resolved_dir_path = current_app.config['UPLOAD_PATH'] / dir_path
    if not (is_safe_path(dir_path) and is_in_upload_path(resolved_dir_path)):
        return jsonify({'error_message': 'not valid path'}), 400
    func_method = {
        'POST': upload_post,
        'PATCH': upload_patch,
        'GET': upload_get
    }
    return func_method[request.method](resolved_dir_path)


def upload_post(resolved_dir_path: Path):
    if resolved_dir_path.exists():
        return jsonify({'error_message': 'try to POST on existing directory'}), 400
    makedirs(resolved_dir_path)
    for file in request.files.getlist('files'):
        file.save(resolved_dir_path / secure_filename(file.filename))
    return jsonify({'message': 'Successfully added'}), 201


def upload_patch(resolved_dir_path: Path):
    if not resolved_dir_path.exists():
        return jsonify({'error_message': 'try to PATCH on not existing directory'}), 400
    for file in request.files.getlist('files'):
        file_path = resolved_dir_path / secure_filename(file.filename)
        if file_path.exists():
            remove(file_path)
        file.save(file_path)
    return jsonify({'message': 'Successfully updated'}), 200


def upload_get(resolved_dir_path: Path):
    file_path = resolved_dir_path.relative_to(current_app.config['UPLOAD_PATH'])
    response = Response(status=200)
    if resolved_dir_path.is_dir():
        response.headers['X-Accel-Redirect'] = f'/files/{file_path}/'
    else:
        response.headers['X-Accel-Redirect'] = f'/files/{file_path}'
    del response.headers['Content-Type']
    return response


@app.route('/')
def root():
    response = Response(status=200)
    response.headers['X-Accel-Redirect'] = '/files/'
    del response.headers['Content-Type']
    return response

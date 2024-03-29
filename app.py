import random
import string
from os import path
from tempfile import NamedTemporaryFile
from typing import Tuple
from uuid import uuid4

from flask import Flask, render_template, request, send_file, jsonify, url_for, flash, redirect
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

from database import db, Preset, upsert
from metadata import Metadata

app = Flask(__name__)

app.secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % path.join(path.dirname(__file__), 'db.sqlite')
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(__file__), 'static/uploads')

db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', presets=Preset.query.all())


@app.route('/convert', methods=['POST'])
def convert():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    album = request.form.get('album', '').strip()
    number = request.form.get('order-number', '').strip()
    out_of = request.form.get('out-of', '').strip()
    audio = request.files.get('audio')
    artwork = request.files.get('artwork')
    artwork_name = request.form.get('artwork-name', '').strip()

    is_valid, error_message = _validate_input(False, author, album, number, out_of, artwork, artwork_name, audio, title)
    if not is_valid:
        flash(f'{error_message} for embedding.')
        return redirect(url_for('index'))

    # Update order number
    preset = Preset.query.filter_by(album=album, author=author).first()
    if preset:
        preset.last_number = int(number)
        upsert(preset)

    artwork_bytes = None
    if artwork:
        artwork_bytes = artwork.stream
    elif artwork_name:
        artwork_path = path.join(app.config['UPLOAD_FOLDER'], path.basename(artwork_name))
        if path.exists(artwork_path):
            artwork_bytes = open(artwork_path, 'rb')

    track = f"{number}/{out_of}" if out_of else number
    metadata = Metadata(title, author, album, track=track, artwork=artwork_bytes)
    mp3_io = metadata.add_to(audio.stream)

    filename = secure_filename(audio.filename)
    with NamedTemporaryFile() as temp_file:
        temp_file.write(mp3_io.read())
        return send_file(temp_file.name, as_attachment=True, download_name=filename, mimetype='audio/mpeg')


@app.route('/new-preset', methods=['POST'])
def save_preset():
    author = request.form.get('author', '').strip()
    album = request.form.get('album', '').strip()
    number = request.form.get('order-number', '').strip()
    out_of = request.form.get('out-of', '').strip()
    artwork = request.files.get('artwork')
    artwork_name = request.form.get('artwork-name', '').strip()
    preset_id = str(uuid4())

    is_valid, error_message = _validate_input(True, author, album, number, out_of, artwork, artwork_name)
    if not is_valid:
        return f'{error_message} when saving a preset.', 400

    number = int(number)
    if out_of:
        out_of = int(out_of)

    artwork_filename = None
    if artwork:
        artwork_filename = preset_id + path.splitext(artwork.filename)[1]
        artwork_path = path.join(app.config['UPLOAD_FOLDER'], artwork_filename)
        with open(artwork_path, 'wb') as artwork_file:
            artwork_file.write(artwork.stream.read())
    elif artwork_name:
        artwork_filename = path.basename(artwork_name)

    preset = Preset(preset_id, album, author, number, artwork_filename=artwork_filename, out_of=out_of)
    upsert(preset)

    return "OK", 201


@app.route('/get-preset', methods=['GET'])
def get_preset():
    preset_id = request.args.get('preset-id', '').strip()
    if not preset_id:
        return "No preset ID provided", 400

    preset = Preset.query.filter_by(id=preset_id).first()
    if not preset:
        return "Preset not found", 404

    return jsonify(
        album=preset.album,
        author=preset.author,
        artwork=url_for('static', filename='uploads/' + preset.artwork_filename) if preset.artwork_filename else None,
        order_number=preset.last_number + 1,
        out_of=preset.out_of
    )


def _validate_input(is_preset: bool, author: str, album: str, number: str, out_of: str, artwork: FileStorage = None,
                    artwork_name: str = '', audio: FileStorage = None, title: str = '') -> Tuple[bool, str]:
    # Author validation
    if not author:
        return False, "Author is required"

    # Album validation
    if not album:
        return False, "Album is required"

    # Number validation
    if not number:
        return False, "Order number is required"
    try:
        number = int(number)
        if number < 0:
            return False, "Order number cannot be negative"
    except ValueError:
        return False, "Order number must be an integer"

    # Out of validation
    if out_of:
        try:
            out_of = int(out_of)
            if out_of < 0:
                return False, "Total number of episodes cannot be negative"
            if out_of < number:
                return False, "Total number of episodes cannot be less than order number"
        except ValueError:
            return False, "Total number of episodes must be an integer"

    # Artwork validation
    if (not artwork or artwork.filename == '') and not artwork_name:
        return False, "No artwork submitted"
    if artwork and not artwork.filename.lower().endswith(('.png', '.jpg')):
        return False, "Only PNG or JPG are allowed as artwork"
    if artwork_name and not artwork_name.lower().endswith(('.png', '.jpg')):
        return False, "Only PNG or JPG are allowed as artwork"

    # Title validation
    if not is_preset:
        if not title:
            return False, "Title is required"

    # Audio validation
    if not is_preset:
        if not audio or audio.filename == '':
            return False, "No audio file submitted"
        if not audio.filename.lower().endswith('.mp3'):
            return False, "Only MP3 is allowed"

    return True, ""


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')

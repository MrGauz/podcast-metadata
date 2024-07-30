import logging
import random
import string
from os import path
from tempfile import NamedTemporaryFile
from typing import Tuple
from uuid import uuid4

from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

from database import db, Preset, upsert
from metadata import Metadata, parse_csv

app = Flask(__name__)

app.secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % path.join(path.dirname(__file__), 'db.sqlite')
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(__file__), 'static/uploads')

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.INFO)

db.init_app(app)
with app.app_context():
    db.create_all()

log = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def index():
    log.info('Handling index() request')
    return render_template('index.html', presets=Preset.query.all())


@app.route('/convert', methods=['POST'])
def convert():
    log.info('Handling convert() request')
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    album = request.form.get('album', '').strip()
    number = request.form.get('order-number', '').strip()
    out_of = request.form.get('out-of', '').strip()
    audio = request.files.get('audio')
    chapters = request.files.get('chapters')
    artwork = request.files.get('artwork')
    artwork_name = request.form.get('artwork-name', '').strip()
    log.info(f'Converting {audio.filename if audio else "<empty_file>"} to MP3 with following metadata\n'
             f'Title: {title}, Author: {author}, Album: {album}, Order Number: {number}, Out Of: {out_of},'
             f'Artwork: {artwork.filename if artwork else None}, Artwork Name: {artwork_name}, '
             f'Chapters: {chapters.filename if chapters else None}')

    is_valid, error_message = _validate_input(False, author, album, number, out_of, artwork, artwork_name, audio,
                                              chapters, title)
    log.info(f'Validation result: {is_valid} (error message: {error_message})')
    if not is_valid:
        log.warning(f'Redirect: {error_message} for embedding.')
        return f'{error_message} for embedding.', 400

    # Update order number
    preset = Preset.query.filter_by(album=album, author=author).first()
    log.info(f'Preset found: {preset}')
    if preset:
        preset.last_number = int(number)
        upsert(preset)
        log.info(f'Order number updated to {number} for preset {preset.id}')

    artwork_bytes = None
    if artwork:
        log.info(f'Using uploaded artwork for embedding')
        artwork_bytes = artwork.stream
    elif artwork_name:
        artwork_path = path.join(app.config['UPLOAD_FOLDER'], path.basename(artwork_name))
        log.info(f'Using preset artwork for embedding: {artwork_path}')
        if path.exists(artwork_path):
            log.info(f'Artwork found')
            artwork_bytes = open(artwork_path, 'rb')

    log.info(f'Embedding metadata into {audio.filename}')
    track = f"{number}/{out_of}" if out_of else number
    metadata = Metadata(title, author, album, track=track, artwork=artwork_bytes, chapters=chapters)
    if audio.filename.lower().endswith('.wav'):
        audio.stream = metadata.convert_wav_to_mp3(audio.stream)
        audio.filename = audio.filename[:-4] + '.mp3'
    mp3_io = metadata.add_to(audio.stream)

    log.info(f'Sending MP3 bytes to user')
    filename = secure_filename(audio.filename)
    with NamedTemporaryFile() as temp_file:
        temp_file.write(mp3_io.read())
        return send_file(temp_file.name, as_attachment=True, download_name=filename, mimetype='audio/mpeg')


@app.route('/new-preset', methods=['POST'])
def save_preset():
    log.info('Handling save_preset() request')
    author = request.form.get('author', '').strip()
    album = request.form.get('album', '').strip()
    number = request.form.get('order-number', '').strip()
    out_of = request.form.get('out-of', '').strip()
    artwork = request.files.get('artwork')
    artwork_name = request.form.get('artwork-name', '').strip()
    preset_id = str(uuid4())
    log.info(f'Saving new preset with ID {preset_id}'
             f'Author: {author}, Album: {album}, Order Number: {number}, Out Of: {out_of},'
             f'Artwork: {artwork.filename if artwork else None}, Artwork Name: {artwork_name}')

    is_valid, error_message = _validate_input(True, author, album, number, out_of, artwork, artwork_name)
    log.info(f'Validation result: {is_valid} (error message: {error_message})')
    if not is_valid:
        log.warning(f'400: {error_message} when saving a preset.')
        return f'{error_message} when saving a preset.', 400

    number = int(number)
    if out_of:
        out_of = int(out_of)

    artwork_filename = None
    if artwork:
        artwork_filename = preset_id + path.splitext(artwork.filename)[1]
        artwork_path = path.join(app.config['UPLOAD_FOLDER'], artwork_filename)
        log.info(f'Saving uploaded artwork for preset {preset_id} to {artwork_path}')
        with open(artwork_path, 'wb') as artwork_file:
            artwork_file.write(artwork.stream.read())
    elif artwork_name:
        artwork_filename = path.basename(artwork_name)
        log.info(f'Using preset artwork for preset {preset_id}: {artwork_filename}')

    preset = Preset(preset_id, album, author, number, artwork_filename=artwork_filename, out_of=out_of)
    upsert(preset)

    log.info(f'201: Preset {preset_id} saved successfully')
    return "OK", 201


@app.route('/get-preset', methods=['GET'])
def get_preset():
    preset_id = request.args.get('preset-id', '').strip()
    log.info('Handling get_preset() request for preset ID "{preset_id}"')
    if not preset_id:
        log.warning('400: No preset ID provided')
        return "No preset ID provided", 400

    preset = Preset.query.filter_by(id=preset_id).first()
    if not preset:
        log.warning('404: Preset not found')
        return "Preset not found", 404

    log.info(f'200: Preset {preset.album} found')
    return jsonify(
        album=preset.album,
        author=preset.author,
        artwork=url_for('static', filename='uploads/' + preset.artwork_filename) if preset.artwork_filename else None,
        order_number=preset.last_number + 1,
        out_of=preset.out_of
    )


def _validate_input(is_preset: bool, author: str, album: str, number: str, out_of: str, artwork: FileStorage = None,
                    artwork_name: str = '', audio: FileStorage = None, chapters: FileStorage = None,
                    title: str = '') -> Tuple[bool, str]:
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
        if not audio.filename.lower().endswith('.mp3') and not audio.filename.lower().endswith('.wav'):
            return False, "Only MP3 & WAV are allowed"

    # Chapters CSV validation
    if chapters:
        if not chapters.filename.lower().endswith('.csv'):
            return False, "Only CSV is allowed for chapters"
        headers, rows = parse_csv(chapters)
        if not headers:
            return False, "Chapters file must be a valid CSV file"
        if not rows:
            return False, "There must be at least one chapter in the CSV file"
        if 'Name' not in headers or 'Start' not in headers:
            return False, "Chapters file must contain 'Name' and 'Start' columns"

    return True, ""


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')

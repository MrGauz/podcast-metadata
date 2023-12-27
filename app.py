import sys
from os import path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename

from database import db, Preset, upsert
from metadata import Metadata

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % path.join(path.dirname(__file__), 'db.sqlite')
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(__file__), 'static/uploads')

db.init_app(app)


@app.route('/', methods=['GET'])
def index():
    presets = Preset.query.all()
    return render_template('index.html', presets=presets)


@app.route('/convert', methods=['POST'])
def convert():
    title = request.form.get('title')
    author = request.form.get('author')
    album = request.form.get('album')
    number = request.form.get('order-number')
    out_of = request.form.get('out-of')
    audio = request.files.get('audio')
    artwork = request.files.get('artwork')

    # TODO: other input validation
    if not audio or audio.filename == '':
        return "No audio file submitted"
    if not audio.filename.lower().endswith('.mp3'):
        return "Only MP3 is allowed"

    if artwork and artwork.filename != '':
        if not artwork.filename.lower().endswith(('.png', '.jpg')):
            return "Only PNG or JPG are allowed as artwork"

    track = f"{number}/{out_of}" if out_of else number
    metadata = Metadata(title, author, album, track=track, artwork=artwork.stream)
    mp3_io = metadata.add_to(audio.stream)

    filename = secure_filename(audio.filename)
    with NamedTemporaryFile() as temp_file:
        temp_file.write(mp3_io.read())
        return send_file(temp_file.name, as_attachment=True, download_name=filename, mimetype='audio/mpeg')


@app.route('/new-preset', methods=['POST'])
def save_preset():
    author = request.form.get('author')
    album = request.form.get('album')
    number = request.form.get('order-number')
    out_of = request.form.get('out-of')
    artwork = request.files.get('artwork')
    preset_id = str(uuid4())

    # TODO: validate input
    if number:
        number = int(number)
    if out_of:
        out_of = int(out_of)

    artwork_filename = None
    if artwork and artwork.filename != '':
        if not artwork.filename.lower().endswith(('.png', '.jpg')):
            return "Only PNG or JPG are allowed as artwork", 400

        artwork_filename = preset_id + '.' + path.splitext(artwork.filename)[1]
        artwork_path = path.join(app.config['UPLOAD_FOLDER'], artwork_filename)
        with open(artwork_path, 'wb') as artwork_file:
            artwork_file.write(artwork.stream.read())

    preset = Preset(preset_id, album, author, artwork_filename=artwork_filename, last_number=number, out_of=out_of)
    upsert(preset)

    return "OK", 201


@app.route('/get-preset', methods=['GET'])
def get_preset():
    if not request.args.get('preset-id'):
        return "No preset ID provided", 400

    preset = Preset.query.filter_by(id=request.args.get('preset-id')).first()
    if not preset:
        return "Preset not found", 404

    return jsonify(
        album=preset.album,
        author=preset.author,
        artwork=url_for('static', filename='uploads/' + preset.artwork_filename) if preset.artwork_filename else None,
        order_number=preset.last_number + 1 if preset.last_number else None,
        out_of=preset.out_of
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    is_debug = '--debug' in sys.argv
    if is_debug:
        app.run(debug=True, host='127.0.0.1')
    else:
        app.run(debug=False, host='0.0.0.0')

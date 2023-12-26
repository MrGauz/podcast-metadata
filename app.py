import sys
from os import path
from tempfile import NamedTemporaryFile

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

from database import db
from metadata import Metadata

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % path.join(path.dirname(__file__), 'db.sqlite')
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(__file__), 'uploads')

db.init_app(app)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    title = request.form.get('title')
    author = request.form.get('author')
    album = request.form.get('album')
    number = request.form.get('number')
    out_of = request.form.get('out-of')
    audio = request.files.get('audio')
    artwork = request.files.get('artwork')

    # TODO: other input validation
    if not audio or audio.filename == '':
        return "No audio file submitted"
    if not audio.filename.lower().endswith('.mp3'):
        return "Only MP3 is allowed"

    if not artwork or artwork.filename == '':
        return "No artwork submitted"
    if not artwork.filename.lower().endswith(('.png', '.jpg')):
        return "Only PNG or JPG are allowed as artwork"

    artwork_path = path.join(app.config['UPLOAD_FOLDER'], secure_filename(artwork.filename))
    with open(artwork_path, 'wb') as artwork_file:  # Save artwork because it might be needed by the preset
        artwork_file.write(artwork.stream.read())

    track = f"{number}/{out_of}" if out_of else number
    metadata = Metadata(title, author, album, track=track, artwork=artwork_path)
    mp3_io = metadata.add_to(audio.stream)

    filename = secure_filename(audio.filename)
    with NamedTemporaryFile() as temp_file:
        temp_file.write(mp3_io.read())
        return send_file(temp_file.name, as_attachment=True, download_name=filename, mimetype='audio/mpeg')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    is_debug = '--debug' in sys.argv
    if is_debug:
        app.run(debug=True, host='127.0.0.1')
    else:
        app.run(debug=False, host='0.0.0.0')

from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Preset(db.Model):
    __tablename__ = 'presets'

    def __init__(self, preset_id: str, album: str, author: str, last_number: int, artwork_filename: str = None,
                 out_of: int = None):
        self.id = preset_id
        self.album = album
        self.author = author
        self.artwork_filename = artwork_filename
        self.last_number = last_number
        self.out_of = out_of

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    album = db.Column(db.String(200), unique=True, nullable=False)
    author = db.Column(db.String(200), nullable=False)
    artwork_filename = db.Column(db.String(500), nullable=True)
    last_number = db.Column(db.Integer, nullable=False)
    out_of = db.Column(db.Integer, nullable=True)


def upsert(preset: Preset):
    record = Preset.query.filter_by(album=preset.album).first()

    if record:
        record.author = preset.author
        record.artwork_filename = preset.artwork_filename
        record.last_number = preset.last_number
        record.out_of = preset.out_of
    else:
        db.session.add(preset)

    db.session.commit()
    return record or preset

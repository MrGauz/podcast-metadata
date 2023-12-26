from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Preset(db.Model):
    __tablename__ = 'presets'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(200), unique=True, nullable=False)
    artist = db.Column(db.String(200), nullable=True)
    artwork = db.Column(db.String(500), nullable=True)
    last_number = db.Column(db.Integer, nullable=False, default=1)

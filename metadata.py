import csv
from datetime import datetime
from io import StringIO
from typing import IO, Tuple

from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, APIC, TYER
from mutagen.mp3 import MP3
from werkzeug.datastructures import FileStorage


class Metadata:
    def __init__(self, title: str, author: str, album: str, track: str = None, artwork: IO[bytes] = None,
                 chapters: FileStorage = None):
        self.title = title
        self.author = author
        self.album = album
        self.track = track
        self.artwork = artwork
        self.genre = 'Podcast'
        self.date = datetime.now().year
        self.chapters = chapters

    def add_to(self, audio_bytes: IO[bytes]) -> IO[bytes]:
        mp3 = MP3(audio_bytes)

        # encoding=3 is for utf-8
        self.title and mp3.tags.add(TIT2(encoding=3, text=str(self.title)))
        self.author and mp3.tags.add(TPE1(encoding=3, text=str(self.author)))
        self.album and mp3.tags.add(TALB(encoding=3, text=str(self.album)))
        self.date and mp3.tags.add(TYER(encoding=3, text=str(self.date)))
        self.genre and mp3.tags.add(TCON(encoding=3, text=str(self.genre)))
        self.track and mp3.tags.add(TRCK(encoding=3, text=str(self.track)))

        if self.artwork:
            mime = 'image/jpeg' if self.artwork.read().startswith(b'\xff\xd8\xff') else 'image/png'
            self.artwork.seek(0)

            mp3.tags.add(APIC(
                encoding=3,
                mime=mime,
                type=3,  # 3 is for the cover image
                desc=u'Cover',
                data=self.artwork.read()
            ))

        if self.chapters:
            headers, rows = parse_csv(self.chapters)
            # TODO: embed chapters
            pass

        mp3.save(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes


def parse_csv(chapters: FileStorage) -> Tuple[list, list]:
    chapters.stream.seek(0)
    try:
        with StringIO(chapters.stream.read().decode('utf-8')) as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader.fieldnames), [row for row in reader]
    except Exception as e:
        return [], []

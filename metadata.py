from datetime import datetime
from io import BytesIO
from os import path, unlink

from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, APIC, TYER
from mutagen.mp3 import MP3


class Metadata:
    def __init__(self, title: str, author: str, album: str, track: str = None, artwork: str = None,
                 preset_id: str = None):
        self.title = title
        self.author = author
        self.album = album
        self.track = track
        self.artwork = artwork
        self.preset_id = preset_id
        self.genre = 'Podcast'
        self.date = datetime.now().year

    def add_to(self, audio_bytes) -> BytesIO:
        mp3 = MP3(audio_bytes)

        # encoding=3 is for utf-8
        self.title and mp3.tags.add(TIT2(encoding=3, text=str(self.title)))
        self.author and mp3.tags.add(TPE1(encoding=3, text=str(self.author)))
        self.album and mp3.tags.add(TALB(encoding=3, text=str(self.album)))
        self.date and mp3.tags.add(TYER(encoding=3, text=str(self.date)))
        self.genre and mp3.tags.add(TCON(encoding=3, text=str(self.genre)))
        self.track and mp3.tags.add(TRCK(encoding=3, text=str(self.track)))

        if self.artwork and path.exists(self.artwork):
            with open(path.join(self.artwork), 'rb') as artwork:
                mp3.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg' if self.artwork.lower().endswith('.jpg') else 'image/png',
                    type=3,  # 3 is for the cover image
                    desc=u'Cover',
                    data=artwork.read()
                ))

            # Delete artwork if it's not needed for the preset
            if not self.preset_id:
                unlink(self.artwork)

        mp3.save(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes

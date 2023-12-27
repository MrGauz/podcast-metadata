from datetime import datetime
from io import BytesIO

from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, APIC, TYER
from mutagen.mp3 import MP3


class Metadata:
    def __init__(self, title: str, author: str, album: str, track: str = None, artwork=None, preset_id: str = None):
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

        mp3.save(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes

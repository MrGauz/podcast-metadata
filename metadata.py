import csv
from datetime import datetime, time, timedelta
from io import StringIO
from typing import IO, Tuple

from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, APIC, TYER, CHAP, CTOC, CTOCFlags, TIT3, TSST, TXXX
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
                desc='Cover',
                data=self.artwork.read()
            ))

        if self.chapters:
            headers, rows = parse_csv(self.chapters)
            track_duration = (datetime.min + timedelta(seconds=float(mp3.info.length))).time()
            if rows[0]['Start'] != time(0, 0):
                rows[0]['Start'] = time(0, 0)

            mp3.tags.add(
                CTOC(element_id="toc", flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
                     child_element_ids=[f"chp{i}" for i in range(1, len(rows) + 1)],
                     sub_frames=[TIT2(text=["Chapters"])]))

            for i, row in enumerate(rows):
                if row['Start'] >= track_duration:
                    break
                if row['End'] >= track_duration:
                    row['End'] = track_duration

                mp3.tags.add(CHAP(
                    element_id=f"chp{i}",
                    start_time=_get_rounded_total_milliseconds(row['Start']),
                    end_time=_get_rounded_total_milliseconds(row['End']),
                    sub_frames=[
                        TIT2(text=[row['Name']]),
                    ])
                )

        mp3.save(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes


def parse_csv(chapters: FileStorage) -> Tuple[list, list]:
    chapters.stream.seek(0)
    try:
        with StringIO(chapters.stream.read().decode('utf-8-sig')) as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,\t")
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, dialect=dialect)

            rows = [{
                'Name': row['Name'].strip(),
                'Start': _parse_time(row['Start'].strip()),
                'Description': row['Description'].strip(),
                'End': datetime.max.time()
            } for row in reader]

            rows.sort(key=lambda x: _get_rounded_total_milliseconds(x['Start']))

            for i, row in enumerate(rows):
                if i + 1 < len(rows):
                    row['End'] = rows[i + 1]['Start']

            return list(reader.fieldnames), rows
    except Exception:
        return [], []


def _parse_time(timestamp: str) -> time:
    formats = ['%H:%M:%S.%f', '%M:%S.%f', '%S.%f']
    for fmt in formats:
        try:
            return datetime.strptime(timestamp.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"time data '{timestamp}' does not match expected formats")


def _get_rounded_total_milliseconds(time_obj: time) -> int:
    return (time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second) * 1000

import csv
import logging
from datetime import datetime, time, timedelta
from io import StringIO, BytesIO
from typing import IO, Tuple

from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, APIC, TYER, CHAP, CTOC, CTOCFlags
from mutagen.mp3 import MP3
from pydub import AudioSegment
from werkzeug.datastructures import FileStorage

log = logging.getLogger(__name__)


class Metadata:
    def __init__(self, title: str, author: str, album: str, track: str = None, artwork: IO[bytes] = None,
                 chapters: FileStorage = None):
        log.info(f'Creating metadata for "{title}" {track} by {author}')
        self.title = title
        self.author = author
        self.album = album
        self.track = track
        self.artwork = artwork
        self.genre = 'Podcast'
        self.date = datetime.now().year
        self.chapters = chapters

    @staticmethod
    def convert_wav_to_mp3(audio_bytes: IO[bytes]) -> IO[bytes]:
        log.info('Converting WAV to MP3')
        try:
            audio = AudioSegment.from_file(audio_bytes, format="wav")
            mp3_bytes = BytesIO()
            audio.export(mp3_bytes, format="mp3")
            mp3_bytes.seek(0)

            return mp3_bytes
        except Exception as e:
            raise RuntimeError(f"Error converting WAV to MP3: {e}")

    def add_to(self, audio_bytes: IO[bytes]) -> IO[bytes]:
        mp3 = MP3(audio_bytes)
        log.info(f'Adding metadata to {mp3.info.length} seconds long audio file')

        # encoding=3 is for utf-8
        self.title and mp3.tags.add(TIT2(encoding=3, text=str(self.title))) and log.info(f'TIT2 (Title): {self.title}')
        self.author and mp3.tags.add(TPE1(encoding=3, text=str(self.author))) and log.info(
            f'TPE1 (Author): {self.author}')
        self.album and mp3.tags.add(TALB(encoding=3, text=str(self.album))) and log.info(f'TALB (Album): {self.album}')
        self.date and mp3.tags.add(TYER(encoding=3, text=str(self.date))) and log.info(f'TYER (Year): {self.date}')
        self.genre and mp3.tags.add(TCON(encoding=3, text=str(self.genre))) and log.info(f'TCON (Genre): {self.genre}')
        self.track and mp3.tags.add(TRCK(encoding=3, text=str(self.track))) and log.info(f'TRCK (Track): {self.track}')

        if self.artwork:
            log.info('Adding artwork to the audio file')
            mime = 'image/jpeg' if self.artwork.read().startswith(b'\xff\xd8\xff') else 'image/png'
            log.info(f'Artwork MIME type: {mime}')
            self.artwork.seek(0)

            mp3.tags.add(APIC(
                encoding=3,
                mime=mime,
                type=3,  # 3 is for the cover image
                desc='Cover',
                data=self.artwork.read()
            ))
            log.info('APIC (Attached Picture) added')

        if self.chapters:
            log.info('Adding chapters to the audio file')
            headers, rows = parse_csv(self.chapters)
            track_duration = (datetime.min + timedelta(seconds=float(mp3.info.length))).time()
            if rows[0]['Start'] != time(0, 0):
                log.info(f'Setting the first chapter to start at 00:00:00.000 instead of {rows[0]["Start"]}')
                rows[0]['Start'] = time(0, 0)

            for i, row in enumerate(rows):
                if row['Start'] >= track_duration:
                    log.warning(f"Chapter {row['Name']} starts after the end of the audio file")
                    break
                if row['End'] >= track_duration:
                    log.info(f'Setting the end of chapter {row["Name"]} to the end of the audio file')
                    row['End'] = track_duration

                mp3.tags.add(CHAP(
                    element_id=f"chp{i + 1}",
                    start_time=_get_rounded_total_milliseconds(row['Start']),
                    end_time=_get_rounded_total_milliseconds(row['End']),
                    sub_frames=[
                        TIT2(text=[row['Name']], encoding=3),
                    ]
                ))
                log.info(f'CHAP (Chapter): {row["Name"]} from {row["Start"]} to {row["End"]}')

            mp3.tags.add(
                CTOC(element_id="toc", flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
                     child_element_ids=[f"chp{i}" for i in range(1, len(mp3.tags.getall("CHAP")) + 1)],
                     sub_frames=[TIT2(text=["Chapters"], encoding=3)]))
            log.info(f'CTOC (Table of Contents): {len(rows)} chapters')

        mp3.save(audio_bytes)
        log.info('Metadata added to the audio file successfully')
        audio_bytes.seek(0)
        return audio_bytes


def parse_csv(chapters: FileStorage) -> Tuple[list, list]:
    log.info(f'Parsing chapters CSV file {chapters.filename}')
    chapters.stream.seek(0)
    try:
        with StringIO(chapters.stream.read().decode('utf-8-sig')) as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,\t")
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, dialect=dialect)
            log.info(f'CSV file has columns: {reader.fieldnames}')

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

            log.info(f'Parsed {len(rows)} chapters from the CSV file')
            return list(reader.fieldnames), rows
    except Exception as e:
        log.error(f'Error while parsing chapters CSV file', exc_info=e)
        return [], []


def _parse_time(timestamp: str) -> time:
    formats = ['%H:%M:%S.%f', '%M:%S.%f', '%S.%f']
    for fmt in formats:
        try:
            return datetime.strptime(timestamp.strip(), fmt).time()
        except ValueError:
            continue
    log.error(f"Time data '{timestamp}' does not match expected formats")
    raise ValueError(f"Time data '{timestamp}' does not match expected formats")


def _get_rounded_total_milliseconds(time_obj: time) -> int:
    return int((time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second) * 1000)

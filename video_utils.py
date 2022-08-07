import datetime

import os

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from pytube import YouTube

from typing import Tuple

from my_secrets import DIRECTORY

from moviepy.editor import VideoFileClip, AudioFileClip

from my_exceptions import (InvalidUrlError, DownloadingError,
                           IncorrectTimingsError)


content_types = ["С картинкой", "Только звук"]

content_modes = ["Целиком", "Обрезать"]


def create_content_types_keyboard():
    markup = ReplyKeyboardMarkup(row_width=len(content_types))

    for mode in content_types:
        markup.add(KeyboardButton(mode))

    return markup


def create_content_modes_keyboard():
    markup = ReplyKeyboardMarkup(row_width=len(content_modes))

    for mode in content_modes:
        markup.add(KeyboardButton(mode))

    return markup


def get_content(user_input: str, user_id: int,
                c_type: str, c_mode: str) -> str:
    if c_mode == "Обрезать":
        url, timing = user_input.split()
    else:
        url, timing = user_input, None

    path, start, end = download_content(url, user_id, c_type, timing)

    if c_mode == "Целиком":
        return path

    path_cut = cut_content(user_id, *convert_timing(start, end), c_type)

    return path_cut


def download_content(url: str, user_id: int,
                     c_type: str, timing) -> Tuple[str, str, str]:
    """Try to download video by url"""

    start, end = None, None

    # Check if URL is correct
    try:
        content = YouTube(url)
    except Exception:
        raise InvalidUrlError

    # Validate timings if user asked to cut
    if timing is not None:
        # Raises IncorrectTimingsError if timings are incorrect
        start, end = validate_timing(timing, content.length)

    # Try to do download content
    try:
        args = (dict([['progressive', True]]) if c_type == 'video'
                else dict([['type', 'audio']]))
        content = content.streams.filter(**args).last()
        extension = "mp4" if c_type == "video" else "mp3"
        content.download(
            output_path=DIRECTORY,
            filename=f'{user_id}.{extension}'
            )
    except Exception:
        raise DownloadingError
    else:
        path = DIRECTORY + f'/{user_id}.{extension}'

    return path, start, end


def validate_timing(timing: str, clip_len: int) -> Tuple[str, str]:
    """
    Check if timing sent by user is in XX:XX-YY:YY format
    and XX:XX < YY:YY and YY:YY < end of clip.
    """

    start, end = timing.split('-')
    start = datetime.datetime.strptime(start, '%M:%S')
    end = datetime.datetime.strptime(end, '%M:%S')
    clip_len = f'{clip_len // 60}:{clip_len % 60}'

    if end < start or end > datetime.datetime.strptime(clip_len, '%M:%S'):
        raise IncorrectTimingsError

    return start.strftime("%M:%S"), end.strftime("%M:%S")


def convert_timing(start, end):
    """Convert from XX:XX format to seconds"""

    start = int(start[:2]) * 60 + int(start[3:])
    end = int(end[:2]) * 60 + int(end[3:])
    return start, end


def cut_content(user_id: int, start: int, end: int, c_type: str) -> str:
    """Cut downloaded clip"""

    clip_name = user_id

    if c_type == "video":
        extension = "mp4"
        obj = VideoFileClip
    else:
        extension = "mp3"
        obj = AudioFileClip

    with obj(DIRECTORY + f"/{clip_name}.{extension}") as clip:
        clip = clip.subclip(start, end)
        write_method = (clip.write_videofile if c_type == "video"
                        else clip.write_audiofile)
        write_method(DIRECTORY + f"/cut{clip_name}.{extension}")

    return DIRECTORY + f'/cut{clip_name}.{extension}'


def clear(*args):
    """Clear tmp folder from used videos"""

    for path in args:
        if os.path.exists(path):
            os.remove(path)

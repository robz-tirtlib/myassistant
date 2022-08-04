import datetime

import os

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from pytube import YouTube

from typing import Tuple

from my_secrets import DIRECTORY

from moviepy.editor import VideoFileClip


def create_video_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2)
    markup.add(KeyboardButton("Целиком"), KeyboardButton("Обрезать"))
    return markup


def try_download(chat_id: int, url: str, timing=None) -> Tuple[str, str, str]:
    """Try to download video by url"""

    start, end = None, None

    # Check if URL is correct
    try:
        v = YouTube(url)
    except Exception as error:
        raise error

    # Validate timings if user asked to cut
    if timing is not None:

        # Корректны ли введенные тайминги

        try:
            start, end = validate_timing(timing, v.length)
        except ValueError as error:
            raise error

    # Try to do download video
    try:
        # path = download_video(url, chat_id)
        video = v.streams.filter(progressive=True).last()
        video.download(output_path=DIRECTORY, filename=f'{chat_id}.mp4')
    except Exception as error:
        raise error
    else:
        path = DIRECTORY + f'/{chat_id}.mp4'

    return path, start, end


def validate_timing(timing: str, clip_len: int) -> Tuple[str, str]:
    """
    Check if timing sent by user is in XX:XX-YY:YY format
    and XX:XX < YY:YY and YY:YY < end of clip.
    """

    try:
        start, end = timing.split('-')
        start = datetime.datetime.strptime(start, '%M:%S')
        end = datetime.datetime.strptime(end, '%M:%S')
        clip_len = f'{clip_len // 60}:{clip_len % 60}'

        if end < start or end > datetime.datetime.strptime(clip_len, '%M:%S'):
            raise ValueError
    except ValueError:
        raise ValueError("Неправильный формат данных, должно быть MM:SS-MM:SS")

    return start.strftime("%M:%S"), end.strftime("%M:%S")


def convert_timing(start, end):
    """Convert from XX:XX format to seconds"""

    start = int(start[:2]) * 60 + int(start[3:])
    end = int(end[:2]) * 60 + int(end[3:])
    return start, end


def cut_the_clip(message, start, end) -> str:
    """Cut downloaded clip"""

    clip_name = message.chat.id

    with VideoFileClip(DIRECTORY + f"/{clip_name}.mp4") as clip:
        clip = clip.subclip(start, end)
        clip.write_videofile(DIRECTORY + f"/cut{clip_name}.mp4")

    return DIRECTORY + f'/cut{clip_name}.mp4'


def clear(*args):
    """Clear tmp folder from used videos"""

    for path in args:
        if os.path.exists(path):
            os.remove(path)

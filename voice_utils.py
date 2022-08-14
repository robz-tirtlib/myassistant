import speech_recognition as sr

from subprocess import Popen

import os

from my_secrets import DIRECTORY, FFMPEG_PATH

from my_exceptions import VoiceDownloadingError, VoiceConversionError


r = sr.Recognizer()


def text_from_voice(bot, message) -> None:
    """General function of voice conversion"""

    try:
        download_voice(bot, message)
    except Exception:
        raise VoiceDownloadingError

    ogg_to_wav(f'{DIRECTORY}\\{message.from_user.id}.ogg',
               f'{DIRECTORY}\\{message.from_user.id}.wav')

    try:
        text = get_text(f"{DIRECTORY}\\{message.from_user.id}.wav")
    except Exception:
        raise VoiceConversionError

    clear(f'{DIRECTORY}\\{message.from_user.id}.ogg',
          f'{DIRECTORY}\\{message.from_user.id}.wav')
    return text


def download_voice(bot, message) -> None:
    """Downloads voice in .ogg format from TG servers"""

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(f'{DIRECTORY}\\{message.from_user.id}.ogg', 'wb') as new_file:
        new_file.write(downloaded_file)


def ogg_to_wav(filepath_in: str, filepath_out: str) -> None:
    """
    Converts .ogg to .wav via ffmpeg (unfortunately, speech recognition module
    doesn't support .ogg filetype).
    """

    args = [FFMPEG_PATH, '-i', filepath_in, filepath_out]
    process = Popen(args)
    process.wait()


def get_text(path: str) -> str:
    """Recognize speech"""

    with sr.AudioFile(path) as source:
        audio = r.record(source)
        text = r.recognize_google(audio, language='ru-RU')
    return text.lower()


def clear(*args):
    """Clear tmp folder from used voices"""

    for path in args:
        if os.path.exists(path):
            os.remove(path)

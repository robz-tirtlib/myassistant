from threading import Thread

import schedule

import time

import requests

import telebot

import datetime

from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup

from telebot.storage import StateMemoryStorage

import os

import sqlite3

from typing import Tuple

from my_secrets import TOKEN, DIRECTORY, WEATHER_KEY

from pytube import YouTube

from moviepy.editor import VideoFileClip


def listener(messages) -> None:
    """When new messages arrive TeleBot will call this function."""
    for m in messages:
        if m.content_type == 'text':
            print(f'{m.chat.first_name} [{m.chat.id}]: {m.text}')


state_storage = StateMemoryStorage()

bot = telebot.TeleBot(TOKEN, state_storage=state_storage)
bot.set_update_listener(listener)


class MyStates(StatesGroup):
    """User's possible states"""

    # Video
    video = State()
    video_c = State()
    date = State()
    time = State()

    # Weather
    weather_m = State()
    weather = State()


@bot.message_handler(commands=["start"])
def start(message) -> None:
    """Handling /start"""

    bot.send_message(message.chat.id, """
Привет! Я - твой личный ассистент.
Чтобы понять, как со мной работать, напиши /help
    """)


@bot.message_handler(commands=["help"])
def help(message) -> None:
    """Handling /start"""

    bot.send_message(message.chat.id, """
Ты можешь попросить меня:
- скачать видео с YouTube - /video
- скачать обрезанное видео - /video_cut
- показать курс валют - /valutes
- показать погоду - /weather
- поставить напоминалку - /reminder
Нажми на нужную команду.
    """)


@bot.message_handler(state="*", commands=['cancel'])
def cancel_state(message) -> None:
    """Catches /cancel and cancels user's state"""

    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=["reminder"])
def reminder(message) -> None:
    """Handling /reminder and changind state"""

    bot.send_message(message.chat.id, "Введите дату в формате YY-MM-dd")
    bot.set_state(message.from_user.id, MyStates.date, message.chat.id)


@bot.message_handler(state=MyStates.date)
def date(message) -> None:
    """Validation of the entered date and changind state if OK"""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        try:
            datetime.datetime.strptime(message.text, '%Y-%m-%d')
        except ValueError:
            bot.send_message(message.chat.id, "Incorrect data format, should be YYYY-MM-DD")
            return
        data['date'] = message.text

    bot.send_message(message.chat.id, "Введите время в формате HH:MM")
    bot.set_state(message.from_user.id, MyStates.time, message.chat.id)


@bot.message_handler(state=MyStates.time)
def date_time(message) -> None:
    """Validation of the entered time and deleting state if OK"""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        try:
            datetime.datetime.strptime(message.text, '%H:%M')
        except ValueError:
            bot.send_message(message.chat.id, "Incorrect data format, should be HH:MM")
            return

        date_and_time = f"{data['date']} {message.text}:00"
        bot.send_message(message.chat.id, date_and_time)
        add_to_db(message.chat.id, date_and_time)

    bot.delete_state(message.from_user.id, message.chat.id)


def add_to_db(user_id, date_time) -> None:
    """Adds reminder from user to DB"""

    db = sqlite3.connect('myassistant.db')
    c = db.cursor()

    query = f"""
    INSERT INTO reminders
    VALUES
        ({user_id}, datetime('{date_time}'));
    """
    c.execute(query)

    db.commit()

    db.close()


def get_reminders():
    """"""

    db = sqlite3.connect('myassistant.db')
    c = db.cursor()

    query_select = """
SELECT user_id
FROM reminders
WHERE DATE(reminder_date) <= DATE('now')
      AND strftime('%H %M', datetime(reminder_date)) <= strftime('%H %M', datetime('now', 'localtime'));
"""

    c.execute(query_select)

    to_remind = c.fetchall()

    query_delete = """
DELETE FROM reminders
WHERE DATE(reminder_date) <= DATE('now')
      AND strftime('%H %M', datetime(reminder_date)) <= strftime('%H %M', datetime('now', 'localtime'));
"""
    c.execute(query_delete)

    db.commit()
    db.close()

    remind_users(to_remind)


def remind_users(user_ids):
    for user_id in user_ids:
        bot.send_message(user_id[0], "Ало бля")


def do_check_reminders():
    schedule.every(3).seconds.do(get_reminders)

    while True:
        schedule.run_pending()
        time.sleep(1)


@bot.message_handler(commands=["weather"])
def handle_weather(message) -> None:
    """Calls an API to get today's weather forecast"""

    bot.send_message(message.chat.id,
                     """
Напиши режим:
- щ (сейчас)
- с (сегодня)
- з (завтра)
    """)

    bot.set_state(message.from_user.id, MyStates.weather_m, message.chat.id)


@bot.message_handler(state=MyStates.weather_m)
def weather_mode(message) -> None:

    if message.text not in ['щ', 'с', 'з']:
        bot.send_message(message.chat.id, "Некорретный режим. Напиши еще раз.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['weather_mode'] = message.text

    bot.send_message(message.chat.id, "Напиши название города.")

    bot.set_state(message.from_user.id, MyStates.weather, message.chat.id)


@bot.message_handler(state=MyStates.weather)
def weather(message) -> None:
    """Calls an API to get today's weather forecast"""

    city = message.text

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        try:
            info = ask_weather_api(city, data['weather_mode'])
        except ValueError as error:
            bot.send_message(message.chat.id, str(error))

    bot.send_message(message.chat.id, info)

    bot.delete_state(message.from_user.id, message.chat.id)


def ask_weather_api(city, mode):

    params = {
        'q': city,
        'appid': WEATHER_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    if not city_exists(params):
        raise ValueError("Не удалось получить информацию по городу")

    if mode == 'щ':
        return now_weather(params)
    elif mode == 'с':
        day = str(datetime.date.today())
        return day_weather(params, day)
    elif mode == 'з':
        day = str(datetime.date.today() + datetime.timedelta(days=1))
        return day_weather(params, day)


def city_exists(params):
    test_url = 'https://api.openweathermap.org/data/2.5/weather'
    test_response = requests.get(test_url, params=params).json()

    if test_response["cod"] == "404":
        return False
    return True


def now_weather(params):

    url = 'https://api.openweathermap.org/data/2.5/weather'

    result = requests.get(url, params=params).json()

    return f"""
{params["q"].capitalize()}
---------------------
Температура: {result["main"]["temp"]},
Ощущается как: {result["main"]["feels_like"]},
Влажность: {result["main"]["humidity"]},
В общем: {result["weather"][0]["description"]}
"""


def day_weather(params, day: str):

    url = 'https://api.openweathermap.org/data/2.5/forecast'

    result = requests.get(url, params=params).json()

    response = f"{params['q'].capitalize()}\n"

    for data in result["list"]:
        date, time = data["dt_txt"].split()
        start, end = "09:00:00", "21:00:00"
        if start <= time <= end and date == day:
            response += f"""
{time}
---------------------
Температура: {data["main"]["temp"]},
Ощущается как: {data["main"]["feels_like"]},
Влажность: {data["main"]["humidity"]},
В общем: {data["weather"][0]["description"]}

"""

    return response


@bot.message_handler(commands=["valutes"])
def handle_valutes(message) -> None:
    """Calls an API to get today's exchange rates"""

    url = 'https://www.cbr-xml-daily.ru/daily_json.js'

    try:
        response = requests.get(url)
        usd = response.json()["Valute"]["USD"]["Value"]
        eur = response.json()["Valute"]["EUR"]["Value"]
    except Exception:
        bot.send_message(message.chat.id,
                         "К сожалению, получить информацию не вышло :(")
        return

    bot.send_message(message.chat.id,
                     f"Сегодня такой движ:\n\nДоллар: {usd},\nЕвро: {eur}")


@bot.message_handler(commands=["video"])
def handle_video(message) -> None:
    bot.set_state(message.from_user.id, MyStates.video, message.chat.id)


@bot.message_handler(commands=["video_cut"])
def handle_video_cut(message) -> None:
    bot.set_state(message.from_user.id, MyStates.video_c, message.chat.id)


def validate_timing(timing, clip_len) -> Tuple[str, str]:
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


def try_download(chat_id, url, timing=None):
    # Можно ли получить видос по урлу

    start, end = None, None

    try:
        v = YouTube(url)
    except Exception as error:
        raise error

    # Если надо резать

    if timing is not None:

        # Корректны ли введенные тайминги

        try:
            start, end = validate_timing(timing, v.length)
        except ValueError as error:
            raise error

    # Качается ли видос

    try:
        path = download_video(url, chat_id)
    except Exception as error:
        raise error

    return path, start, end


@bot.message_handler(state=MyStates.video)
def video(message) -> None:

    url = message.text

    try:
        path, _, _ = try_download(message.chat.id, url)
    except Exception as error:
        bot.send_message(message.chat.id, str(error))
        return

    with open(path, 'rb') as video:
        bot.send_video(message.chat.id, video)

    clear(path)

    bot.send_message(message.chat.id, "Ну вроде скачал и отправил.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=MyStates.video_c)
def video_cut(message) -> None:
    url, timing = message.text.split()

    try:
        path, start, end = try_download(message.chat.id, url, timing)
    except Exception as error:
        bot.send_message(message.chat.id, str(error))

    # Режем видос

    with open(path, 'rb') as video:
        path_cut = False
        while not path_cut:
            path_cut = cut_the_clip(message, *convert_timing(start, end))

    # Отправляем видос

    with open(path_cut, 'rb') as video:
        bot.send_video(message.chat.id, video)

    # Очищаем машину от видоса

    clear(path_cut, path)

    bot.send_message(message.chat.id, "Ну вроде скачал, обрезал и отправил.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    for greeting in 'привет', 'здарова':
        if greeting in message.text.lower():
            bot.send_message(message.chat.id, 'Привет!')
            return

    bot.send_message(message.chat.id, 'Сори, не знаю, как ответить :(')


def download_video(video_url: str, chat_id: int) -> str:
    try:
        v = YouTube(video_url)
        video = v.streams.filter(progressive=True).last()
        video.download(output_path=DIRECTORY, filename=f'{chat_id}.mp4')
    except Exception as error:
        raise error

    print("\nDownloading completed.")
    return DIRECTORY + f'/{chat_id}.mp4'


def convert_timing(start, end):
    start = int(start[:2]) * 60 + int(start[3:])
    end = int(end[:2]) * 60 + int(end[3:])
    return start, end


def cut_the_clip(message, start, end):
    clip_name = message.chat.id

    with VideoFileClip(DIRECTORY + f"/{clip_name}.mp4") as clip:
        clip = clip.subclip(start, end)
        bot.send_message(message.chat.id, 'Обсчет может занять некоторое время.')
        clip.write_videofile(DIRECTORY + f"/cut{clip_name}.mp4")

    return DIRECTORY + f'/cut{clip_name}.mp4'


def clear(*args):
    for path in args:
        if os.path.exists(path):
            os.remove(path)


bot.add_custom_filter(custom_filters.StateFilter(bot))

thread = Thread(target=do_check_reminders)
thread.start()

bot.infinity_polling(skip_pending=True)

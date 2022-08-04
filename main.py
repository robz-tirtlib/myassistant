from threading import Thread

import schedule

import time

import requests

import telebot

import datetime
from datetime import date

from telebot import custom_filters, types
from telebot.handler_backends import State, StatesGroup

from telebot.storage import StateMemoryStorage

import sqlite3

from my_secrets import TOKEN

from video_utils import (try_download, convert_timing, cut_the_clip, clear,
                         create_video_keyboard)

from messages import start_message, help_message

from weather_utils import (ask_weather_api, create_weather_mode_keyboard,
                           create_weather_city_keyboard, weather_cities,
                           weather_modes)

from keyboards import (OUT_DATE, generate_calendar_days,
                       generate_calendar_months, EMTPY_FIELD)

from filters import calendar_factory, calendar_zoom, bind_filters


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
    video_choose = State()
    video_pure = State()
    video_cut = State()

    # Reminders
    date_time = State()
    reminder_time = State()

    # Weather
    weather_choose_mode = State()
    weather_choose_city = State()
    weather_city_input = State()


"Service commands: start, help, cancel."


@bot.message_handler(commands=["start"])
def start(message) -> None:
    """Handling /start"""

    bot.send_message(message.chat.id, start_message)


@bot.message_handler(commands=["help"])
def help(message) -> None:
    """Handling /start"""

    bot.send_message(message.chat.id, help_message)


@bot.message_handler(state="*", commands=['cancel'])
def cancel_state(message) -> None:
    """Catches /cancel and cancels user's state"""

    bot.send_message(message.chat.id, "Состояние сброшено.")
    bot.delete_state(message.from_user.id, message.chat.id)


"Reminders"


@bot.message_handler(commands=["reminder"])
def reminder(message) -> None:
    """Handling /reminder and changind state"""

    now = date.today()
    bot.set_state(message.from_user.id, MyStates.reminder_time, message.chat.id)
    bot.send_message(message.chat.id,
                     "Выберите дату.",
                     reply_markup=generate_calendar_days(
                        year=now.year,
                        month=now.month))


@bot.callback_query_handler(func=None,
                            calendar_config=calendar_factory.filter())
def calendar_action_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_factory.parse(callback_data=call.data)
    year, month = int(callback_data['year']), int(callback_data['month'])
    day = callback_data['day']

    if day == EMTPY_FIELD:
        markup = generate_calendar_days(year=year, month=month)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                      reply_markup=markup)
    elif day == OUT_DATE:
        pass
    else:
        with bot.retrieve_data(call.from_user.id) as data:
            data['reminder_date'] = f"{year}-{month:02d}-{int(day):02d}"

        bot.delete_message(call.message.chat.id, call.message.id)

        bot.send_message(call.message.chat.id,
                         "Напишите время в формате HH:MM")


@bot.callback_query_handler(func=None,
                            calendar_zoom_config=calendar_zoom.filter())
def calendar_zoom_out_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_zoom.parse(callback_data=call.data)
    year = int(callback_data.get('year'))

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.id,
        reply_markup=generate_calendar_months(year=year)
        )


@bot.callback_query_handler(func=lambda call: call.data == EMTPY_FIELD)
def callback_empty_field_handler(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)


@bot.message_handler(state=MyStates.reminder_time)
def reminder_time(message) -> None:

    try:
        datetime.datetime.strptime(message.text, '%H:%M')
    except ValueError:
        bot.send_message(message.chat.id, "Неверно введено время.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        date_and_time = f"{data['reminder_date']} {message.text}:00"

    add_to_db(message.chat.id, date_and_time)

    bot.send_message(
        message.chat.id,
        "Напоминание установлено на " + date_and_time
        )

    bot.delete_state(message.from_user.id, message.chat.id)


# @bot.message_handler(state=MyStates.date_time)
# def reminder_date_time(message) -> None:
#     """Validate date, time and add reminder to DB"""

#     r_date, r_time = message.text.split()

#     try:
#         datetime.datetime.strptime(r_date, '%Y-%m-%d')
#     except ValueError:
#         bot.send_message(message.chat.id, "Неверно введена дата.")
#         return

#     try:
#         datetime.datetime.strptime(r_time, '%H:%M')
#     except ValueError:
#         bot.send_message(message.chat.id, "Неверно введено время.")
#         return

#     date_and_time = f"{message.text}:00"
#     add_to_db(message.chat.id, date_and_time)

#     bot.send_message(
#         message.chat.id,
#         "Напоминание установлено на " + date_and_time
#         )

#     bot.delete_state(message.from_user.id, message.chat.id)


# @bot.message_handler(commands=["reminder"])
# def reminder(message) -> None:
#     """Handling /reminder and changind state"""

#     bot.send_message(message.chat.id,
#                      "Введите дату и время в формате YYYY-MM-DD HH:MM.")
#     bot.set_state(message.from_user.id, MyStates.date_time, message.chat.id)


# @bot.message_handler(state=MyStates.date_time)
# def reminder_date_time(message) -> None:
#     """Validate date, time and add reminder to DB"""

#     r_date, r_time = message.text.split()

#     try:
#         datetime.datetime.strptime(r_date, '%Y-%m-%d')
#     except ValueError:
#         bot.send_message(message.chat.id, "Неверно введена дата.")
#         return

#     try:
#         datetime.datetime.strptime(r_time, '%H:%M')
#     except ValueError:
#         bot.send_message(message.chat.id, "Неверно введено время.")
#         return

#     date_and_time = f"{message.text}:00"
#     add_to_db(message.chat.id, date_and_time)

#     bot.send_message(
#         message.chat.id,
#         "Напоминание установлено на " + date_and_time
#         )

#     bot.delete_state(message.from_user.id, message.chat.id)


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


"Weather"


@bot.message_handler(commands=["weather"])
def handle_weather(message) -> None:
    """Calls an API to get today's weather forecast"""

    bot.send_message(message.chat.id, "Выбери режим.",
                     reply_markup=create_weather_mode_keyboard())

    bot.set_state(message.from_user.id, MyStates.weather_choose_mode,
                  message.chat.id)


@bot.message_handler(state=MyStates.weather_choose_mode)
def weather_choose_mode(message) -> None:
    """Choose weather mode"""

    if message.text not in weather_modes:
        bot.send_message(message.chat.id, "Воспользуйтесь кнопками.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['weather_mode'] = message.text

    markup = create_weather_city_keyboard()

    bot.send_message(message.chat.id, "Выбери название города.",
                     reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.weather_choose_city,
                  message.chat.id)


@bot.message_handler(state=MyStates.weather_choose_city)
def weather_choose_city(message) -> None:
    if message.text not in weather_cities and message.text != 'другой':
        bot.send_message(message.chat.id, "Воспользуйтесь кнопками.")
        return

    if message.text != "другой":
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["city"] = message.text

        weather_final(message.from_user.id)
    else:
        markup = telebot.types.ReplyKeyboardRemove()

        bot.send_message(message.chat.id, "Введите название города.",
                         reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.weather_city_input,
                      message.chat.id)


@bot.message_handler(state=MyStates.weather_city_input)
def weather_city_input(message) -> None:
    """User writes custom city"""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["city"] = message.text

    weather_final(message.from_user.id)


def weather_final(id):
    with bot.retrieve_data(id) as data:
        try:
            info = ask_weather_api(data["city"], data['weather_mode'])
        except ValueError as error:
            bot.send_message(id, str(error) + "\nДавай по новой.")
            bot.set_state(id, MyStates.weather_choose_mode)

    markup = telebot.types.ReplyKeyboardRemove()

    bot.send_message(id, info, reply_markup=markup)

    bot.delete_state(id)


"Valutes"


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


"Video"


@bot.message_handler(commands=["video"])
def handle_video(message) -> None:
    bot.send_message(
        message.chat.id, "Видос отсылать целиком или обрезать?",
        reply_markup=create_video_keyboard())
    bot.set_state(message.from_user.id, MyStates.video_choose, message.chat.id)


@bot.message_handler(state=MyStates.video_choose)
def video_choose(message) -> None:

    if message.text not in ['Целиком', 'Обрезать']:
        bot.send_message(message.chat.id, "Воспользуйтесь кнопками.")
        return

    markup = telebot.types.ReplyKeyboardRemove()

    if message.text == 'Целиком':
        response = "Кидай ссылку."
        bot.set_state(message.from_user.id, MyStates.video_pure,
                      message.chat.id)
    else:
        response = "Кидай ссылку и тайминг в формате XX:XX-YY:YY"
        bot.set_state(message.from_user.id, MyStates.video_cut,
                      message.chat.id)

    bot.send_message(message.chat.id, response, reply_markup=markup)


@bot.message_handler(state=MyStates.video_pure)
def video_pure(message) -> None:

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


@bot.message_handler(state=MyStates.video_cut)
def video_cut(message) -> None:
    url, timing = message.text.split()

    try:
        path, start, end = try_download(message.chat.id, url, timing)
    except Exception as error:
        bot.send_message(message.chat.id, str(error))

    # Режем видос

    with open(path, 'rb') as video:
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


bot.add_custom_filter(custom_filters.StateFilter(bot))

bind_filters(bot)

thread = Thread(target=do_check_reminders)
thread.start()

bot.infinity_polling(skip_pending=True)

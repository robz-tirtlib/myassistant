from threading import Thread

import schedule

import time

import telebot

import datetime
from datetime import date

from telebot import types
from telebot.handler_backends import State, StatesGroup

from telebot.storage import StateMemoryStorage

from my_secrets import TOKEN

from video_utils import (clear, get_content,
                         create_content_types_keyboard, content_types,
                         create_content_modes_keyboard, content_modes)

from my_exceptions import (CityNotSupportedError, InvalidUrlError,
                           IncorrectTimingsError, DownloadingError)

from messages import start_message, help_message

from weather_utils import (ask_weather_api, create_weather_mode_keyboard,
                           create_weather_city_keyboard, weather_cities,
                           weather_modes)

from valutes_utils import get_rates

from reminder_utils import add_to_db, get_reminders

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

    # Content
    content_choose_type = State()
    content_choose_mode = State()
    content_finish = State()

    # Reminders
    reminder_time = State()
    reminder_text = State()

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

    markup = telebot.types.ReplyKeyboardRemove()

    bot.send_message(message.chat.id, "Состояние сброшено.",
                     reply_markup=markup)
    bot.delete_state(message.from_user.id, message.chat.id)


"Reminders"


@bot.message_handler(commands=["reminder"])
def reminder(message) -> None:
    """Handling /reminder: creating calendar and changing state"""

    now = date.today()
    bot.set_state(message.from_user.id, MyStates.reminder_time,
                  message.chat.id)
    bot.send_message(message.chat.id,
                     "Выберите дату.",
                     reply_markup=generate_calendar_days(
                        year=now.year,
                        month=now.month))


@bot.callback_query_handler(func=None,
                            calendar_config=calendar_factory.filter())
def calendar_action_handler(call: types.CallbackQuery):
    """Handling calendar clicks"""

    callback_data: dict = calendar_factory.parse(callback_data=call.data)
    year, month = int(callback_data['year']), int(callback_data['month'])
    day = callback_data['day']

    if day == EMTPY_FIELD:  # Switch to prev/next month
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.id,
            reply_markup=generate_calendar_days(year=year, month=month)
            )
    elif day == OUT_DATE:  # Days from other months
        bot.answer_callback_query(call.id)
    else:  # Day from current month
        with bot.retrieve_data(call.from_user.id) as data:
            data['reminder_date'] = f"{year}-{month:02d}-{int(day):02d}"

        bot.delete_message(call.message.chat.id, call.message.id)

        bot.send_message(call.message.chat.id,
                         "Напиши время в формате HH:MM")


@bot.callback_query_handler(func=None,
                            calendar_zoom_config=calendar_zoom.filter())
def calendar_zoom_out_handler(call: types.CallbackQuery):
    """Handling 'Zoom out' click (changing month)"""

    callback_data: dict = calendar_zoom.parse(callback_data=call.data)
    year = int(callback_data.get('year'))

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.id,
        reply_markup=generate_calendar_months(year=year)
        )


@bot.callback_query_handler(func=lambda call: call.data == EMTPY_FIELD)
def callback_empty_field_handler(call: types.CallbackQuery):
    """Handling clicks on empty field on calendar"""

    bot.answer_callback_query(call.id)


@bot.message_handler(state=MyStates.reminder_time)
def reminder_time(message) -> None:
    """Validating user's time for reminder and asking for text"""

    try:
        datetime.datetime.strptime(message.text, '%H:%M')
    except ValueError:
        bot.send_message(message.chat.id, "Неверно введено время.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["date_and_time"] = f"{data['reminder_date']} {message.text}:00"

    bot.send_message(message.chat.id, "Введи текст напоминания.")

    bot.set_state(message.from_user.id, MyStates.reminder_text,
                  message.chat.id)


@bot.message_handler(state=MyStates.reminder_text)
def reminder_text(message) -> None:
    """Adding reminder to DB"""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        date_and_time = data["date_and_time"]

    add_to_db(message.chat.id, date_and_time, message.text)

    bot.send_message(
        message.chat.id,
        f'Напоминание "{message.text}" установлено на ' + date_and_time
        )

    bot.delete_state(message.from_user.id, message.chat.id)


def do_check_reminders():
    schedule.every(3).seconds.do(get_reminders, bot)

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
        bot.send_message(message.chat.id, "Воспользуйся кнопками.")
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
        bot.send_message(message.chat.id, "Воспользуйся кнопками.")
        return

    if message.text != "другой":
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["city"] = message.text

        weather_final(message.from_user.id)
    else:
        markup = telebot.types.ReplyKeyboardRemove()

        bot.send_message(message.chat.id, "Введи название города.",
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
        except CityNotSupportedError as error:
            bot.send_message(id, error + "\nДавай по новой.")
            bot.set_state(id, MyStates.weather_choose_mode)

    markup = telebot.types.ReplyKeyboardRemove()

    bot.send_message(id, info, reply_markup=markup)

    bot.delete_state(id)


"Valutes"


@bot.message_handler(commands=["valutes"])
def handle_valutes(message) -> None:
    """Calls an API to get today's exchange rates"""

    try:
        rates = get_rates()
    except Exception:
        bot.send_message(message.chat.id,
                         "К сожалению, получить информацию не вышло.")
        return

    bot.send_message(message.chat.id, rates)


"Content"


@bot.message_handler(commands=["content"])
def handle_content(message) -> None:
    """Handling /content"""

    bot.send_message(
        message.chat.id, "Качать с картинкой или только звук?",
        reply_markup=create_content_types_keyboard())
    bot.set_state(
        message.from_user.id,
        MyStates.content_choose_type,
        message.chat.id
        )


@bot.message_handler(state=MyStates.content_choose_type)
def content_choose_type(message) -> None:
    """Choosing content type"""

    if message.text not in content_types:
        bot.send_message(message.chat.id, "Воспользуйся кнопками.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['content_type'] = ("video" if message.text == "С картинкой"
                                else "audio")

    bot.send_message(message.chat.id, "Выбери режим.",
                     reply_markup=create_content_modes_keyboard())

    bot.set_state(message.from_user.id, MyStates.content_choose_mode,
                  message.chat.id)


@bot.message_handler(state=MyStates.content_choose_mode)
def content_choose_mode(message) -> None:
    """Choosing content mode"""

    if message.text not in content_modes:
        bot.send_message(message.chat.id, "Воспользуйся кнопками.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['content_mode'] = message.text

    reply = ("Кидай ссылку." if message.text == "Целиком"
             else "Кидай ссылку и тайминг в формате XX:XX-YY:YY")

    bot.send_message(message.chat.id, reply,
                     reply_markup=telebot.types.ReplyKeyboardRemove())

    bot.set_state(message.from_user.id, MyStates.content_finish,
                  message.chat.id)


@bot.message_handler(state=MyStates.content_finish)
def content_finish(message) -> None:
    """Sending content to user"""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        try:
            path = get_content(
                message.text,
                message.from_user.id,
                data['content_type'],
                data['content_mode']
                )
        except (InvalidUrlError, IncorrectTimingsError,
                DownloadingError) as e:
            bot.send_message(message.chat.id, e)
            return

    with open(path, "rb") as content:
        send_method = (bot.send_video if data['content_type'] == 'video'
                       else bot.send_audio)
        send_method(message.from_user.id, content)

    clear(path)

    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    """Answer to random messages"""
    if is_greeting(message.text.lower()):
        bot.send_message(message.chat.id, 'Привет!')
        return

    bot.send_message(message.chat.id, 'Сори, не знаю, как ответить :(')


def is_greeting(message):
    for greeting in 'привет', 'здарова':
        if greeting in message:
            return True


bind_filters(bot)

thread = Thread(target=do_check_reminders)
thread.start()

bot.infinity_polling(skip_pending=True)

import datetime

import requests

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from my_secrets import WEATHER_KEY


weather_modes = ["Текущая", "Сегодняшняя", "Завтрашняя"]
weather_cities = ["Зеленоград", "Москва", "Кострома"]


def create_weather_mode_keyboard():
    markup = ReplyKeyboardMarkup(row_width=len(weather_modes))

    for mode in weather_modes:
        markup.add(KeyboardButton(mode))

    return markup


def create_weather_city_keyboard():
    markup = ReplyKeyboardMarkup(row_width=len(weather_cities) + 1)

    for city in weather_cities:
        markup.add(KeyboardButton(city))

    markup.add(KeyboardButton("другой"))
    return markup


def ask_weather_api(city, mode):
    """Calls helper functions"""

    params = {
        'q': city,
        'appid': WEATHER_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    if not city_exists(params):
        raise ValueError("Не удалось получить информацию по городу")

    if mode == 'Текущая':
        return now_weather(params)
    elif mode == 'Сегодняшняя':
        day = str(datetime.date.today())
        return day_weather(params, day)
    elif mode == 'Завтрашняя':
        day = str(datetime.date.today() + datetime.timedelta(days=1))
        return day_weather(params, day)


def city_exists(params):
    """Check if API supports city sent by user"""

    test_url = 'https://api.openweathermap.org/data/2.5/weather'
    test_response = requests.get(test_url, params=params).json()

    if test_response["cod"] == "404":
        return False
    return True


def now_weather(params):
    """Weather at the moment"""

    url = 'https://api.openweathermap.org/data/2.5/weather'

    result = requests.get(url, params=params).json()

    return get_weather_str(
        params["q"].capitalize(), result["main"]["temp"],
        result["main"]["feels_like"], result["main"]["humidity"],
        result["weather"][0]["description"]
    )


def day_weather(params, day: str):
    """Weather today or tomorrow"""

    url = 'https://api.openweathermap.org/data/2.5/forecast'

    result = requests.get(url, params=params).json()

    response = f"{params['q'].capitalize()}\n"

    for data in result["list"]:
        date, time = data["dt_txt"].split()
        start, end = "09:00:00", "21:00:00"
        if start <= time <= end and date == day:
            response += get_weather_str(
                time, data["main"]["temp"], data["main"]["feels_like"],
                data["main"]["humidity"], data["weather"][0]["description"])

    return response


def get_weather_str(header, temp, feels_like, humidity, desc):
    return f"""
{header}
---------------------
Температура: {temp},
Ощущается как: {feels_like},
Влажность: {humidity},
В общем: {desc}

"""

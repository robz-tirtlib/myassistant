import requests


url = 'https://www.cbr-xml-daily.ru/daily_json.js'


def get_rates():
    return create_message(*request_rates())


def request_rates():
    response = requests.get(url)
    usd = response.json()["Valute"]["USD"]["Value"]
    eur = response.json()["Valute"]["EUR"]["Value"]
    return usd, eur


def create_message(usd, eur):
    return f"Сегодня такой курс:\n\nUSD/RUB: {usd},\nEUR/RUB: {eur}"

import calendar
from datetime import date, timedelta

from filters import calendar_factory, calendar_zoom
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

EMTPY_FIELD = '1'
OUT_DATE = '_'
WEEK_DAYS = [calendar.day_abbr[i] for i in range(7)]
MONTHS = [(i, calendar.month_name[i]) for i in range(1, 13)]


def generate_calendar_days(year: int, month: int):
    keyboard = InlineKeyboardMarkup(row_width=7)

    keyboard.add(
        InlineKeyboardButton(
            text=date(year=year, month=month, day=1).strftime('%b %Y'),
            callback_data=EMTPY_FIELD
        )
    )
    keyboard.add(*[
        InlineKeyboardButton(
            text=day,
            callback_data=EMTPY_FIELD
        )
        for day in WEEK_DAYS
    ])

    for week in calendar.Calendar().monthdayscalendar(year=year, month=month):
        week_buttons = []
        for day in week:
            day_name = OUT_DATE
            if day != 0:
                day_name = str(day)
            week_buttons.append(
                InlineKeyboardButton(
                    text=day_name,
                    callback_data=calendar_factory.new(year=year, month=month,
                                                       day=day_name)
                )
            )
        keyboard.add(*week_buttons)

    previous_date = date(year=year, month=month, day=1) - timedelta(days=1)
    next_date = date(year=year, month=month, day=1) + timedelta(days=31)

    keyboard.add(
        InlineKeyboardButton(
            text='Previous month',
            callback_data=calendar_factory.new(
                year=previous_date.year,
                month=previous_date.month,
                day=EMTPY_FIELD)
        ),
        InlineKeyboardButton(
            text='Zoom out',
            callback_data=calendar_zoom.new(year=year)
        ),
        InlineKeyboardButton(
            text='Next month',
            callback_data=calendar_factory.new(
                year=next_date.year,
                month=next_date.month,
                day=EMTPY_FIELD)
        ),
    )

    return keyboard


def generate_calendar_months(year: int):
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(
            text=date(year=year, month=1, day=1).strftime('Year %Y'),
            callback_data=EMTPY_FIELD
        )
    )
    keyboard.add(*[
        InlineKeyboardButton(
            text=month,
            callback_data=calendar_factory.new(year=year, month=month_number,
                                               day=EMTPY_FIELD)
        )
        for month_number, month in MONTHS
    ])
    keyboard.add(
        InlineKeyboardButton(
            text='Previous year',
            callback_data=calendar_zoom.new(year=year - 1)
        ),
        InlineKeyboardButton(
            text='Next year',
            callback_data=calendar_zoom.new(year=year + 1)
        )
    )
    return keyboard

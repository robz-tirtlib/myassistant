import telebot
from telebot import types, AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.custom_filters import StateFilter

calendar_factory = CallbackData("year", "month", "day", prefix="calendar")
calendar_zoom = CallbackData("year", prefix="calendar_zoom")


class CalendarCallbackFilter(AdvancedCustomFilter):
    key = 'calendar_config'

    def check(self, call: types.CallbackQuery,
              config: CallbackDataFilter) -> bool:
        return config.check(query=call)


class CalendarZoomCallbackFilter(AdvancedCustomFilter):
    key = 'calendar_zoom_config'

    def check(self, call: types.CallbackQuery,
              config: CallbackDataFilter) -> bool:
        return config.check(query=call)


def bind_filters(bot: telebot.TeleBot) -> None:
    bot.add_custom_filter(CalendarCallbackFilter())
    bot.add_custom_filter(CalendarZoomCallbackFilter())
    bot.add_custom_filter(StateFilter(bot))

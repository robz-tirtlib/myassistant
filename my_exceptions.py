class YouTubeErrors(Exception):
    """Base class for YouTube exceptions"""
    pass


class InvalidUrlError(YouTubeErrors):
    """Exception raised if URL provided by user is invalid"""

    def __init__(self, *args) -> None:
        self.message = "Получить контент по присланной ссылке не вышло."
        super().__init__(self.message)


class IncorrectTimingsError(YouTubeErrors):
    """Exception raised if URL provided by user is invalid"""

    def __init__(self, *args) -> None:
        self.message = "Присланные тайминги некорретны."
        super().__init__(self.message)


class DownloadingError(YouTubeErrors):
    """Exception raised if URL provided by user is invalid"""

    def __init__(self, *args) -> None:
        self.message = "Скачать контент по присланной ссылке не вышло."
        super().__init__(self.message)


class WeatherErrors(Exception):
    """Base class for YouTube exceptions"""
    pass


class CityNotSupportedError(WeatherErrors):
    """Exception raised if user's city is not supported by API"""

    def __init__(self, *args) -> None:
        self.message = "Получить информацию про данный город не вышло."
        super().__init__(self.message)


class VoiceConversionErrors(Exception):
    """Base class for recognizing speech errors"""
    pass


class VoiceDownloadingError(VoiceConversionErrors):
    """Exception raised if an error occured while downloading voice"""

    def __init__(self, *args) -> None:
        self.message = "Не удалось получить сообщение с серверов Telegram."
        super().__init__(self.message)


class VoiceConversionError(VoiceConversionErrors):
    """Exception raised if an error occured while recognizing speech"""

    def __init__(self, *args) -> None:
        self.message = "Не удалось распознать речь."
        super().__init__(self.message)

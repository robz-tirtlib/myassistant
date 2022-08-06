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

# try:
#     raise InvalidUrlError
# except InvalidUrlError as error:
#     print(error)

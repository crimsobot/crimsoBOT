class NoMatchingTarotCard(Exception):
    pass


class NoMatchingTarotSuit(Exception):
    pass


class StrictInputFailed(Exception):
    pass


class LocationNotFound(Exception):
    def __init__(self, location: str) -> None:
        self.location = location


class ZoomNotValid(Exception):
    def __init__(self, zoom: str) -> None:
        self.zoom = zoom


class NotDirectMessage(Exception):
    pass


class StopHandler(Exception):
    pass


class NoImageFound(Exception):
    pass


class NoEmojiFound(Exception):
    pass


class BadCaption(Exception):
    pass


class NotAnInteger(Exception):
    def __init__(self, guess: str) -> None:
        self.guess = guess


class OutOfBounds(Exception):
    def __init__(self, guess: str) -> None:
        self.guess = guess

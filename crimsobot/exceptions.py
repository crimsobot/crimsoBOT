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
    pass


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

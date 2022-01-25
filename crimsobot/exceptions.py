class NoMatchingTarotCard(Exception):
    pass


class StrictInputFailed(Exception):
    pass


class LocationNotFound(Exception):
    def __init__(self, location: str) -> None:
        self.location = location


class NotDirectMessage(Exception):
    pass


class StopHandler(Exception):
    pass


class NoImageFound(Exception):
    pass

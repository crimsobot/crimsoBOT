class NoMatchingTarotCard(Exception):
    pass


class LocationNotFound(Exception):
    def __init__(self, location: str) -> None:
        self.location = location

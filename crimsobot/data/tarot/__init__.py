import json
import os
from typing import Sequence


def _load() -> Sequence[dict]:
    deck_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'deck.json'
    )

    with open(deck_path) as fp:
        deck = json.load(fp)  # type: Sequence[dict]

    return deck


DECK = _load()

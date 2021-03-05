import difflib
import io
import random
from enum import Enum
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import aiofiles
import yaml
from PIL import Image
from discord.ext import commands

from crimsobot.exceptions import NoMatchingTarotCard
from crimsobot.utils.image import image_to_buffer
from crimsobot.utils.tools import clib_path_join

# TODO: Add these descriptions to class Suit or appropriate place. These should be included in the >card embed.
"""     The Major Arcana:
        Beginning with The Fool and ending with The World, these 22 cards represent major archetypes.
        They indicate great cosmic forces at work. Be especially attentive to what they have to say.

        The Wands: The Wands are ruled by the element of fire.
        Their sphere of influence is energy, motivation, will, and passion:
        that which most deeply animates and ignites the soul.

        The Pentacles: Ruled by the element of earth.
        The Pentacles deal with earthly matters--
        health, finances, the body, the domestic sphere, and one's sense of security.

        The Cups: The Cups are ruled by the element of water.
        They preside over matters of the heart.
        Emotion, relationships, inutition, and mystery are all found within their depths.

        The Swords: The Swords are ruled by the element of air.
        Their main concern is the mind and the intellect.
        They cut through delusion towards clarity with sometimes unforgiving sharpness.
"""


# TODO: descriptions to add to >tarot card embed moved to suits.yaml


class Suit(Enum):
    MAJOR_ARCANA = 1
    WANDS = 2
    PENTACLES = 3
    CUPS = 4
    SWORDS = 5

    def __str__(self) -> str:
        words = self.name.split('_')
        words = [w.title() for w in words]
        name = ' '.join(words)

        return name


class Card:
    def __init__(self, name: str, suit: Suit, number: int,
                 image_filename: str,
                 description_upright: str, description_reversed: str,
                 element: str, description_long: str,
                 description_long_reversed: str,
                 ) -> None:
        self.name = name
        self.suit = suit
        self.number = number
        self.image_filename = image_filename
        self.description_upright = description_upright
        self.description_reversed = description_reversed
        self.element = element
        self.description_long = description_long
        self.description_long_reversed = description_long_reversed

    async def get_image(self, reverse: bool = False) -> Image.Image:
        filename = clib_path_join('tarot', 'deck', self.image_filename)
        async with aiofiles.open(filename, 'rb') as f:
            img_bytes = await f.read()

        img = Image.open(BytesIO(img_bytes))
        if reverse:
            img = img.rotate(180)

        return img

    async def get_image_buff(self, reverse: bool = False) -> BytesIO:
        return image_to_buffer([await self.get_image(reverse)])


class Deck:
    _deck = []  # type: List[Card]
    _deck_as_dict = {}  # type: Dict[str, Card]

    @classmethod
    async def get_cards(cls) -> List[Card]:
        if not cls._deck:  # If this evauluates as false-y, the list is empty
            await cls._load_cards()

        return cls._deck

    @classmethod
    async def get_random_cards(cls, n: int) -> List[Card]:
        deck = await cls.get_cards()

        return random.sample(deck, n)

    @classmethod
    async def get_cards_in_suit(cls, suit: Suit) -> List[Card]:
        deck = await cls.get_cards()

        return [c for c in deck if c.suit is suit]

    @classmethod
    async def get_card(cls, suit: Suit, number: int) -> Card:
        deck = await cls.get_cards()

        for card in deck:
            if card.suit is suit and card.number == number:
                return card

        raise NoMatchingTarotCard('Card does not exist')

    @classmethod
    async def get_card_by_name(cls, name: str) -> Card:
        await cls.get_cards()  # Make sure the deck is loaded, as that will also load _deck_as_dict
        close_matches = difflib.get_close_matches(name.lower(), cls._deck_as_dict.keys(), cutoff=0.85)
        if close_matches:
            return cls._deck_as_dict[close_matches[0]]

        raise NoMatchingTarotCard('Card does not exist')

    @classmethod
    async def _load_cards(cls) -> None:
        deck_path = clib_path_join('tarot', 'deck.yaml')

        async with aiofiles.open(deck_path, encoding='utf-8', errors='ignore') as f:
            contents = await f.read()
            deck_raw = yaml.safe_load_all(contents)

        deck = []
        for card_raw in deck_raw:
            suit_raw = card_raw['suit']
            suit = Suit[suit_raw]

            card = Card(
                card_raw['name'], suit, card_raw['number'],
                card_raw['image_filename'],
                card_raw['description_upright'], card_raw['description_reversed'],
                card_raw['element'], card_raw['description_long'],
                card_raw['description_long_reversed'],
            )

            deck.append(card)

        cls._deck = deck
        cls._deck_as_dict = {card.name.lower(): card for card in deck}


async def reading(spread: str) -> Tuple[Optional[io.BytesIO], List[Tuple[str, str, str]]]:
    w, h = (200, 326)  # card size
    space = 20  # space between cards

    if spread == 'ppf':
        # three cards dealt horizontally
        bg_size = (3 * w + 4 * space, h + 2 * space)
        cards = await Deck.get_random_cards(3)
        position = [
            (space, space),
            (w + 2 * space, space),
            (2 * w + 3 * space, space)
        ]
        position_legend = ['PAST', 'PRESENT', 'FUTURE']

    elif spread == 'five':
        # five cards dealt in a cross
        bg_size = (3 * w + 4 * space, 3 * h + 4 * space)
        cards = await Deck.get_random_cards(5)
        position = [
            (space, 2 * space + h),
            (w + 2 * space, 2 * space + h),
            (2 * w + 3 * space, 2 * space + h),
            (w + 2 * space, 3 * space + 2 * h),
            (w + 2 * space, space)
        ]
        position_legend = ['PAST', 'PRESENT', 'FUTURE', 'REASON', 'POTENTIAL']

    elif spread == 'one':
        bg_size = (w, h)
        cards = await Deck.get_random_cards(1)
        position = [
            (0, 0)
        ]
        position_legend = ['\u200d']

    else:
        raise commands.BadArgument('Spread is invalid.')

    bg = Image.new('RGBA', bg_size, (0, 0, 0, 0))

    interpretation = []  # type: List[Tuple[str, str, str]]
    for i, card in enumerate(cards):
        reverse = True if random.random() < 0.12 else False

        card_image = await card.get_image(reverse)
        bg.paste(card_image, position[i])

        if reverse:
            name = card.name + '\n(Reversed)'
            descr = card.description_reversed
        else:
            name = card.name
            descr = card.description_upright

        interpretation.append((position_legend[i], name, descr))

    return image_to_buffer([bg]), interpretation

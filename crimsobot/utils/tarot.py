import difflib
import io
import random
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import aiofiles
import yaml
from PIL import Image
from discord.ext import commands

from crimsobot.exceptions import NoMatchingTarotCard, NoMatchingTarotSuit
from crimsobot.utils.image import image_to_buffer
from crimsobot.utils.tools import clib_path_join


class Suit:
    def __init__(self, name: str, number: int, description: str) -> None:
        self.name = name
        self.number = number
        self.description = description


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
    _suits = []
    _suits_as_dict = {}  # type: Dict[str, Suit]
    _deck = []  # type: List[Card]
    _deck_as_dict = {}  # type: Dict[str, Card]

    @classmethod
    async def get_suits(cls) -> List[Suit]:
        if not cls._suits:  # If this evauluates as false-y, the list is empty
            await cls._load_suits()

        return cls._suits

    @classmethod
    async def get_cards(cls) -> List[Card]:
        if not cls._deck:  # If this evauluates as false-y, the list is empty
            await cls._load_cards()

        return cls._deck

    @classmethod
    async def get_random_cards(cls, n: int, suit: str = 'all') -> List[Card]:
        deck = await cls.get_cards()

        if suit != 'all':
            suit = await cls.get_suit_by_name(suit)
            deck = await cls.get_cards_in_suit(suit)

        return random.sample(deck, n)

    @classmethod
    async def get_cards_in_suit(cls, suit: Suit) -> List[Card]:
        deck = await cls.get_cards()

        return [c for c in deck if c.suit == suit.name]

    @classmethod
    async def get_suit(cls, requested_suit: str) -> Suit:
        all_suits = await cls.get_suits()

        for suit in all_suits:
            if requested_suit == suit.name:
                return suit

        raise NoMatchingTarotSuit('Suit does not exist')

    @classmethod
    async def get_card(cls, suit: Suit, number: int) -> Card:
        deck = await cls.get_cards()

        for card in deck:
            if card.suit == suit.name and card.number == number:
                return card

        raise NoMatchingTarotCard('Card does not exist')

    @classmethod
    async def get_suit_by_name(cls, name: str) -> Suit:
        await cls.get_suits()  # Make sure the suits is loaded, as that will also load _suits_as_dict
        close_matches = difflib.get_close_matches(name.lower(), cls._suits_as_dict.keys(), cutoff=0.85)
        if close_matches:
            return cls._suits_as_dict[close_matches[0]]

        raise NoMatchingTarotSuit('Suit does not exist')

    @classmethod
    async def get_card_by_name(cls, name: str) -> Card:
        await cls.get_cards()  # Make sure the deck is loaded, as that will also load _deck_as_dict
        close_matches = difflib.get_close_matches(name.lower(), cls._deck_as_dict.keys(), cutoff=0.85)
        if close_matches:
            return cls._deck_as_dict[close_matches[0]]

        raise NoMatchingTarotCard('Card does not exist')

    @classmethod
    async def _load_suits(cls) -> None:
        deck_path = clib_path_join('tarot', 'suits.yaml')

        async with aiofiles.open(deck_path, encoding='utf-8', errors='ignore') as f:
            contents = await f.read()
            suits_raw = yaml.safe_load_all(contents)

        suits = []
        for suit_raw in suits_raw:

            suit = Suit(suit_raw['name'], suit_raw['number'], suit_raw['description'])

            suits.append(suit)

        cls._suits = suits
        cls._suits_as_dict = {suit.name.lower(): suit for suit in suits}

    @classmethod
    async def _load_cards(cls) -> None:
        deck_path = clib_path_join('tarot', 'deck.yaml')

        async with aiofiles.open(deck_path, encoding='utf-8', errors='ignore') as f:
            contents = await f.read()
            deck_raw = yaml.safe_load_all(contents)

        deck = []
        for card_raw in deck_raw:

            card = Card(
                card_raw['name'], card_raw['suit'], card_raw['number'],
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

    if spread == 'major3':
        # three Major Arcana cards dealt horizontally
        bg_size = (3 * w + 4 * space, h + 2 * space)
        cards = await Deck.get_random_cards(3, suit='Major Arcana')
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
        # a single card
        bg_size = (w, h)
        cards = await Deck.get_random_cards(1)
        position = [
            (0, 0)
        ]
        position_legend = ['\u200d']

    elif spread == 'major':
        # a single Major Arcana card
        bg_size = (w, h)
        cards = await Deck.get_random_cards(1, suit='Major Arcana')
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

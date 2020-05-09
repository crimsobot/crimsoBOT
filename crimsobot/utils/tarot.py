import io
import random
from enum import Enum
from io import BytesIO
from typing import List, Optional, Tuple

import aiofiles
import yaml
from PIL import Image
from discord.ext import commands

from crimsobot.utils.image import image_to_buffer
from crimsobot.utils.tools import clib_path_join


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
                 description_upright: str, description_reversed: str
                 ) -> None:
        self.name = name
        self.suit = suit
        self.number = number
        self.image_filename = image_filename
        self.description_upright = description_upright
        self.description_reversed = description_reversed

    async def get_image(self, reversed: bool = False) -> Image.Image:
        filename = clib_path_join('tarot', 'deck', self.image_filename)
        async with aiofiles.open(filename, 'rb') as f:
            img_bytes = await f.read()

        img = Image.open(BytesIO(img_bytes))
        if reversed:
            img.rotate(180)

        return img

    async def get_image_buff(self, reversed: bool = False) -> BytesIO:
        return image_to_buffer(await self.get_image(reversed), 'PNG')


class Deck:
    _deck = None

    @classmethod
    async def get_cards(cls) -> List[Card]:
        if cls._deck is None:
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
    async def get_card(cls, suit: Suit, number: int) -> Optional[Card]:
        deck = await cls.get_cards()

        for card in deck:
            if card.suit is suit and card.number == number:
                return card

        return None

    @classmethod
    async def _load_cards(cls) -> None:
        deck_path = clib_path_join('tarot', 'deck.yaml')

        async with aiofiles.open(deck_path) as f:
            contents = await f.read()
            deck_raw = yaml.safe_load_all(contents)

        deck = []
        for card_raw in deck_raw:
            suit_raw = card_raw['suit']
            suit = Suit[suit_raw]

            card = Card(
                card_raw['name'], suit, card_raw['number'],
                card_raw['image_filename'],
                card_raw['description_upright'], card_raw['description_reversed']
            )

            deck.append(card)

        cls._deck = deck


async def reading(spread: str) -> Tuple[Optional[io.BytesIO], List[str]]:
    w, h = (200, 326)  # card size
    space = 20  # space between cards

    interpret = []  # type: List[str]

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

    else:
        raise commands.BadArgument('Spread is invalid.')

    bg = Image.new('RGBA', bg_size, (0, 0, 0, 0))

    for i, card in enumerate(cards):
        reverse = True if random.random() < 0.1 else False

        card_image = await card.get_image(reverse)
        bg.paste(card_image, position[i])

        if not reverse:
            card_description = card.name + ': ' + card.description_upright
        else:
            card_description = card.name + ' (reversed): ' + card.description_reversed
        interpret.append('**{} ·** {}'.format(position_legend[i], card_description))

    return image_to_buffer(bg, 'PNG'), interpret

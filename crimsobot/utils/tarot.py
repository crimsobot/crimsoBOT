import difflib
import io
import random
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import aiofiles
import discord
import yaml
from PIL import Image
from discord.ext import commands


from crimsobot.exceptions import NoMatchingTarotCard, NoMatchingTarotSuit
from crimsobot.utils import tools as c
from crimsobot.utils.image import image_to_buffer


class Suit:
    def __init__(self, name: str, number: int, description: str) -> None:
        self.name = name
        self.number = number
        self.description = description


class Card:
    def __init__(self, name: str, suit: str, number: int,
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

    async def get_image_file(self) -> BytesIO:
        filename = c.clib_path_join('tarot', 'deck', self.image_filename)
        async with aiofiles.open(filename, 'rb') as f:
            img_bytes = await f.read()

        return BytesIO(img_bytes)

    async def get_image(self, reverse: bool = False, cross: bool = False) -> Image.Image:
        fp = await self.get_image_file()
        img = Image.open(fp)

        # rotate if necessary
        if reverse:
            img = img.rotate(180)
        if cross:
            img = img.rotate(90, expand=True)

        return img


class Deck:
    _suits = []  # type: List[Suit]
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
    async def get_random_cards(cls, n: int, requested_suit: str = 'all') -> List[Card]:
        deck = await cls.get_cards()

        if requested_suit != 'all':
            suit = await cls.get_suit_by_name(requested_suit)
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
        deck_path = c.clib_path_join('tarot', 'suits.yaml')

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
        deck_path = c.clib_path_join('tarot', 'deck.yaml')

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

    cross_indices = None  # to indicate which cards are dealt horizontally

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

    elif spread == 'major3':
        # three Major Arcana cards dealt horizontally
        bg_size = (3 * w + 4 * space, h + 2 * space)
        cards = await Deck.get_random_cards(3, 'Major Arcana')
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

    elif spread == 'celtic':
        # ten cards dealt in Celtic cross
        bg_size = (3 * w + h + 5 * space, 4 * h + 5 * space)
        cards = await Deck.get_random_cards(10)
        position = [
            (w + 2 * space + (h - w) // 2, (bg_size[1] - h) // 2),
            (w + 2 * space, (bg_size[1] - w) // 2),
            (w + 2 * space + (h - w) // 2, (bg_size[1] - h) // 2 - h - space),
            (w + 2 * space + (h - w) // 2, (bg_size[1] + h) // 2 + space),
            (space, (bg_size[1] - h) // 2),
            (w + h + 3 * space, (bg_size[1] - h) // 2),
            (2 * w + h + 4 * space, space + 3 * (h + space)),
            (2 * w + h + 4 * space, space + 2 * (h + space)),
            (2 * w + h + 4 * space, space + 1 * (h + space)),
            (2 * w + h + 4 * space, space),
        ]
        position_legend = [
            'QUERENT',
            'CHALLENGE',
            'CROWN',
            'ROOT',
            'PAST',
            'FUTURE',
            'ATTITUDE',
            'ENVIRONMENT',
            'HOPES & FEARS',
            'OUTCOME'
        ]

        cross_indices = 1  # indices of cards that must be crossed

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
        cards = await Deck.get_random_cards(1, 'Major Arcana')
        position = [
            (0, 0)
        ]
        position_legend = ['\u200d']

    else:
        raise commands.BadArgument('Spread is invalid.')

    bg = Image.new('RGBA', bg_size, (0, 0, 0, 0))

    interpretation = []  # type: List[Tuple[str, str, str]]
    for idx, card in enumerate(cards):
        reverse = True if random.random() < 0.12 else False
        cross = True if cross_indices == idx else False

        card_image = await card.get_image(reverse, cross)
        bg.paste(card_image, position[idx])

        if reverse:
            name = card.name + '\n(Reversed)'
            descr = card.description_reversed
        else:
            name = card.name
            descr = card.description_upright

        interpretation.append((position_legend[idx], name, descr))

    return image_to_buffer([bg]), interpretation


async def tarot_embed(
    ctx: commands.Context,
    fp: Optional[BytesIO],
    descriptions: List[Tuple[str, str, str]],
    help_str: str
) -> None:
    """Create a reading embed and send."""

    filename = 'reading.png'
    f = discord.File(fp, filename)

    embed = c.crimbed(
        title=f"{ctx.author.name}'s reading",
        descr=None,
        attachment=filename,
        footer=f'{help_str}\nType ">tarot card" for more on a specific card.',
    )

    for card_tuple in descriptions:
        if card_tuple[0] == '\u200d':  # one-card reading
            embed.add_field(
                name=card_tuple[1],
                value=f'{card_tuple[2]}',
            )
        else:
            embed.add_field(
                name=card_tuple[0],
                value=f'**{card_tuple[1]}**\n{card_tuple[2]}',
            )

    await ctx.send(file=f, embed=embed)

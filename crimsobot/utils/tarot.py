import io
import random
from typing import List, Optional, Tuple

from PIL import Image
from discord.ext import commands

from crimsobot.data.tarot import DECK
from crimsobot.utils.image import image_to_buffer
from crimsobot.utils.tools import clib_path_join


def list_cards(suit: Optional[str]) -> List[str]:
    cards_in_suit = []

    if suit == 'Major arcana':
        for i in range(0, 22):
            cards_in_suit.append(DECK[i]['name'])
    else:
        for card in DECK:
            if suit in card['name']:
                cards_in_suit.append(card['name'])

    return cards_in_suit


def inspect_card(suit_name: str, card_number: int) -> Tuple[str, str]:
    if suit_name == 'Major arcana':
        # the marjor arcana cards are in order at the beginning of the DECK
        card_choice = DECK[card_number]
    else:
        # minor arcana card image filenames are in format "cups-02.jpg" etc.
        card_image_name = '{}-{:02d}.jpg'.format(suit_name.lower(), card_number)
        # find that image name and you've got your card
        for card in DECK:
            if card['image'] == card_image_name:
                card_choice = card
                break

    card_image_path = clib_path_join('tarot', 'deck', card_choice['image'])
    card_description = '**{}**\n**Upright:** {}\n**Reversed:** {}'.format(
        card_choice['name'].upper(), card_choice['desc0'], card_choice['desc1']
    )

    return card_image_path, card_description


def draw_background(size: Tuple[int, int]) -> Image.Image:
    return Image.new('RGBA', size, (0, 0, 0, 0))


def get_cards(n: int) -> List[dict]:
    return random.sample(DECK, n)


def paste_card(bg_image: Image.Image, card_path: str, pos_xy: Tuple[int, int], reverse: bool) -> None:
    card_image = Image.open(card_path)
    if reverse:
        card_image = card_image.rotate(180)

    bg_image.paste(card_image, pos_xy)


def reading(spread: str) -> Tuple[Optional[io.BytesIO], List[str]]:
    w, h = (200, 326)  # card size
    space = 20  # space between cards

    interpret = []  # type: List[str]

    if spread == 'ppf':
        # three cards dealt horizontally
        bg_size = (3 * w + 4 * space, h + 2 * space)
        bg = draw_background(bg_size)
        cards = get_cards(3)
        position = [
            (space, space),
            (w + 2 * space, space),
            (2 * w + 3 * space, space)
        ]
        position_legend = ['PAST', 'PRESENT', 'FUTURE']

    elif spread == 'five':
        # five cards dealt in a cross
        bg_size = (3 * w + 4 * space, 3 * h + 4 * space)
        bg = draw_background(bg_size)
        cards = get_cards(5)
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

    for ii in range(len(cards)):
        card = clib_path_join('tarot', 'deck', cards[ii]['image'])
        reverse = True if random.random() < 0.1 else False
        paste_card(bg, card, position[ii], reverse)
        if not reverse:
            card_description = cards[ii]['name'] + ': ' + cards[ii]['desc0']
        else:
            card_description = cards[ii]['name'] + ' (reversed): ' + cards[ii]['desc1']
        interpret.append('**{} ·** {}'.format(position_legend[ii], card_description))

    return image_to_buffer(bg, 'PNG'), interpret

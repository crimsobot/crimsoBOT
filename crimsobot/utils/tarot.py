import io
import random

from PIL import Image

from crimsobot.data.tarot import DECK
from crimsobot.utils.tools import clib_path_join


def draw_background(size):
    """ input: tuple
       output: PIL image object"""

    return Image.new('RGBA', size, (0, 0, 0, 0))


def get_cards(n):
    """ input: integer
       output: dicts"""

    return random.sample(DECK, n)


def paste_card(bg_image, card_path, pos_xy, reverse):
    """ input: PIL img object x 2, tuple
       output: none"""

    card_image = Image.open(card_path)
    if reverse:
        card_image = card_image.rotate(180)

    bg_image.paste(card_image, pos_xy)


def reading(spread):
    """ input: string
       output: list"""

    w, h = (200, 326)  # card size
    space = 20  # space between cards

    if spread is None or 'ppf':
        # three cards dealt horizontally
        bg_size = (3 * w + 4 * space, h + 2 * space)
        bg = draw_background(bg_size)
        cards = get_cards(3)
        pos = [
            (space, space),
            (w + 2 * space, space),
            (2 * w + 3 * space, space)
        ]
        interpret = ['**PAST · PRESENT · FUTURE**']

        for ii in range(len(cards)):
            card = clib_path_join('tarot', 'deck', cards[ii]['image'])
            reverse = True if random.random() < 0.1 else False
            paste_card(bg, card, pos[ii], reverse)
            if not reverse:
                string = cards[ii]['name'] + ': ' + cards[ii]['desc0']
            else:
                string = cards[ii]['name'] + ' (reversed): ' + cards[ii]['desc0']
            interpret.append(string)

        fp = io.BytesIO()
        bg.save(fp, 'PNG')
        fp.seek(0)
    elif spread == 'celtic':
        interpret = ''
        fp = None
        pass
    else:
        interpret = ''
        fp = None

    return fp, interpret

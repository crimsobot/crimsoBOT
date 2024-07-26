from typing import List, Tuple

import yaml

from crimsobot.utils.color import LabColor, get_nearest_color, hex_to_lab, hex_to_rgb
from crimsobot.utils.tools import clib_path_join


_ruleset_path = clib_path_join('img', 'rules.yaml')
with open(_ruleset_path, encoding='utf-8', errors='ignore') as rules_file:
    _ruleset = next(yaml.safe_load_all(rules_file.read()))

# these are what should be imported by other scripts
IMAGE_RULES = _ruleset['image']
URL_CONTAINS = IMAGE_RULES['url_contains']

GIF_RULES = _ruleset['gif']

CAPTION_RULES = _ruleset['caption']

_EIMG_RULES = _ruleset['eimg']
EIMG_WIDTH = _EIMG_RULES['width']

AENIMA = _ruleset['aenima']
CURRENTS = _ruleset['currents']
LATERALUS = _ruleset['lateralus']


# these will be imported by utils/image.py
color_dict = _EIMG_RULES['palette']
rgb_color_list = []  # type: List[Tuple[int, int, int]]

# this is used internally for the color search in lookup_emoji() below
_lab_color_list = []  # type: List[LabColor]

for color in color_dict:
    hex_color = color[1:]
    rgb_color_list.append(hex_to_rgb(hex_color))
    _lab_color_list.append(hex_to_lab(hex_color))


def lookup_emoji(hex_in: str) -> str:
    """search (bc quantizing palette not working)"""

    nearest = get_nearest_color(_lab_color_list, hex_in)

    for key, value in color_dict.items():  # type: str, str
        if nearest == key:
            return value

    return 'F'  # failure to find emoji

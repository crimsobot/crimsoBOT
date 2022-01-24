import json
import os
from typing import Dict, List, Tuple

import yaml

from crimsobot.utils.color import LabColor, get_nearest_color, hex_to_lab, hex_to_rgb
from crimsobot.utils.tools import clib_path_join


def _load() -> Tuple[Dict[str, str], List[Tuple[int, int, int]], List[LabColor]]:
    colors_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'colors_emojis.json'
    )

    # this is the list of colors and the emojis to which they correspond
    with open(colors_path, 'r', encoding='utf-8') as file:
        colors = json.loads(file.read())

    # these are needed to make the PIL palette list [r1, g1, b1, ..., rn, gn, bn]
    rgb = []
    lab = []
    for hex_color in colors:
        hex_digits = hex_color[1:]

        rgb.append(hex_to_rgb(hex_digits))
        lab.append(hex_to_lab(hex_digits))

    return colors, rgb, lab


color_dict, rgb_color_list, _lab_color_list = _load()


def lookup_emoji(hex_in: str) -> str:
    """search (bc quantizing palette not working)"""

    nearest = get_nearest_color(_lab_color_list, hex_in)

    for key, value in color_dict.items():  # type: str, str
        if nearest == key:
            return value

    return 'F'  # failure to find emoji


_ruleset_path = clib_path_join('img', 'rules.yaml')
with open(_ruleset_path, encoding='utf-8', errors='ignore') as rules_file:
    _ruleset = next(yaml.safe_load_all(rules_file.read()))

# these are what should be imported by other scripts
IMAGE_RULES = _ruleset['image']
GIF_RULES = _ruleset['gif']

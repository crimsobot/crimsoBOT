from typing import Sequence, Tuple

from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor


def hex_to_rgb(color: str) -> Tuple[int, int, int]:
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    return r, g, b


def hex_to_lab(base: str) -> LabColor:
    r, g, b = hex_to_rgb(base)

    color_rgb = sRGBColor(r, g, b, is_upscaled=True)
    color = convert_color(color_rgb, LabColor)

    return color


def get_nearest_color(lab_colors: Sequence[LabColor], rgb_color: str) -> str:
    lab_color = hex_to_lab(rgb_color)

    nearest = min(lab_colors, key=lambda fc: delta_e_cie2000(lab_color, fc))
    nearest = convert_color(nearest, sRGBColor)

    nearest_hex = nearest.get_rgb_hex()  # type: str

    return nearest_hex

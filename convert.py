"""
Author: Roope Sinisalo / kripi-png
Date: 10.3.2024

TODO:
- do something about the styling part
  - maybe allow loading css from file?

- write some tests for the functions?
"""

import argparse
from typing import Any, Sequence
from PIL import Image
from math import sqrt, ceil
from xml.etree import ElementTree as ET
from random import choice

# the darkness is not linear and thus the closest value must be calculated for accuracy
# big thanks to this answer for the charset and darkness values:
# https://stackoverflow.com/a/74186686
# fmt: off
ASCII_CHARSET = " `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
CHAR_DARKNESS = [0,0.0751,0.0829,0.0848,0.1227,0.1403,0.1559,0.185,0.2183,0.2417,0.2571,0.2852,0.2902,0.2919,0.3099,0.3192,0.3232,0.3294,0.3384,0.3609,0.3619,0.3667,0.3737,0.3747,0.3838,0.3921,0.396,0.3984,0.3993,0.4075,0.4091,0.4101,0.42,0.423,0.4247,0.4274,0.4293,0.4328,0.4382,0.4385,0.442,0.4473,0.4477,0.4503,0.4562,0.458,0.461,0.4638,0.4667,0.4686,0.4693,0.4703,0.4833,0.4881,0.4944,0.4953,0.4992,0.5509,0.5567,0.5569,0.5591,0.5602,0.5602,0.565,0.5776,0.5777,0.5818,0.587,0.5972,0.5999,0.6043,0.6049,0.6093,0.6099,0.6465,0.6561,0.6595,0.6631,0.6714,0.6759,0.6809,0.6816,0.6925,0.7039,0.7086,0.7235,0.7302,0.7332,0.7602,0.7834,0.8037,0.9999]
# fmt: on


def find_closest_value(val: int | float, list: Sequence[int | float]) -> int | float:
    """
    Recursively find the closest value to :val in :list.

    Find the middle value in the list, and compare it to given value.
    If the value is lower or equal to the middle value, repeat for the
    first half of the list, otherwise for the second.
    If the list only contains a single value, return the value.
    """

    l = len(list)
    if l == 1:
        return list[0]

    middle_i = l // 2
    if val <= list[middle_i]:
        return find_closest_value(val, list[:middle_i])
    else:
        return find_closest_value(val, list[middle_i:])


def find_char_by_darkness(darkness: float) -> str:
    closest_darkness = find_closest_value(darkness, CHAR_DARKNESS)
    darkness_index = CHAR_DARKNESS.index(closest_darkness)
    return ASCII_CHARSET[darkness_index]


def escape_html(char: str) -> str:
    if char == '"':
        return "&quot;"
    if char == "&":
        return "&amp;"
    if char == "<":
        return "&lt;"
    if char == ">":
        return "&gt;"
    return char


def generate_html_file(spans: Sequence[str], columns: int, args: argparse.Namespace):
    """Create <style>, <head>, and <body> and save them to args.output (default output.html)"""

    html = ET.Element("html")
    head = ET.Element("head")
    body = ET.Element("body")
    for span in spans:
        body.append(ET.fromstring(span))

    decreased_size = ceil(args.fontsize * 0.75)
    # 16 -> 12
    style = ET.Element("style")
    body_style = f"body {{ line-height: {decreased_size}px; background: {args.color}; display: grid; grid-template-columns: repeat({columns}, {decreased_size}px); align-content: start; }}"
    span_style = f"span {{ font-size: {decreased_size}px; }}"
    style.text = body_style + "\n" + span_style

    head.append(style)
    html.append(head)
    html.append(body)

    ET.ElementTree(html).write(args.output, encoding="unicode", method="html")


def rgb2hex(r: int, g: int, b: int) -> str:
    """Returns the hexadecimal for given rgb color.
    Taken from https://stackoverflow.com/a/19917486"""

    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def crop(image: Image.Image, size: int, x: int, y: int) -> Image.Image:
    """Return a crop of given size of the image at given coordinates"""

    box = (x, y, x + size, y + size)
    return image.crop(box)


def get_area_colors(
    image: Image.Image,
) -> Sequence[tuple[int, tuple[int, int, int]]]:
    """
    For RGB images return a list of colors and their respective pixel count
    For monochrome the three RGB values are the same
    """

    # max colors is equal to total number of pixels
    max_colors = image.size[0] * image.size[1]

    # return type annoation of getcolors method is list[tuple[int, int]]
    # when list[tuple[int, tuple[int, int, int]]] is also possible
    colors: Any | Sequence[tuple[int, tuple[int, int, int]]] = image.getcolors(
        max_colors
    )
    if not isinstance(colors, Sequence):
        raise Exception("Unexpected error: colors is not a list")

    if image.mode == "L":
        # in case of monochrome generate a new list of tuples with RGB values being the same
        monochrome_list = []
        for c in colors:
            monochrome_list.append((c[0], (c[1], c[1], c[1])))
        return monochrome_list
    return colors


def calculate_average_color(
    colors: Sequence[tuple[int, tuple[int, int, int]]], total_pixels: int
) -> tuple[int, int, int]:
    """
    Calculate the average of Red, Green, and Blue
    https://sighack.com/post/averaging-rgb-colors-the-right-way
    """
    r, g, b = 0, 0, 0
    for count, color in colors:
        r += (color[0] * color[0]) * count
        g += (color[1] * color[1]) * count
        b += (color[2] * color[2]) * count
    r = int(sqrt(r / total_pixels))
    g = int(sqrt(g / total_pixels))
    b = int(sqrt(b / total_pixels))
    return (r, g, b)


def calculate_common_color(
    colors: Sequence[tuple[int, tuple[int, int, int]]]
) -> tuple[int, int, int]:
    """
    Return the most common color in the list of colors based on pixel count.
    """

    # sort ascendingly based on count
    sorted_colors = sorted(colors, key=lambda color: color[0])
    # return last (most common) color's rgb tuple
    return sorted_colors[-1][1]


def calculate_color(
    image: Image.Image, args: argparse.Namespace
) -> tuple[int, int, int]:
    """
    Calculate the RGB values for the image or tile.
    By default, returns the average RGB color in the area.
    # If --use-common is used, returns the most common RGB value (based on pixel count)
    # If --use-monochrome is used, return the color in monochrome
    """

    colors = get_area_colors(image)
    total_pixels = image.size[0] * image.size[1]

    if args.use_common:
        return calculate_common_color(colors)
    return calculate_average_color(colors, total_pixels)


# def is_whole(x: Union[int, float]) -> bool:
#     """
#     Return whether given number :x is whole number or decimal
#     For example 1.0 is a whole number while 2.3 is not.
#     """
#     return (int(x) - x) == 0


def is_common_divisor(x: int, a: int, b: int) -> bool:
    return a % x == 0 and b % x == 0


def common_divisors(a: int, b: int) -> list[int]:
    """Return all numbers that can be used to divide both :a and :b without remainder"""
    divisors = []
    for i in range(1, min(a, b) + 1):
        if a % i == 0 and b % i == 0:
            divisors.append(i)

    return divisors


def find_closest_common_divisor(x: int, a: int, b: int) -> int:
    """Find a common divisor for :a and :b that is nearest to :x"""
    divisors = common_divisors(a, b)

    if x in divisors:
        return x

    divisors.append(x)
    divisors = sorted(divisors)

    x_index = divisors.index(x)

    # if given num is first or last return second or second last respectively
    if x_index == 0:
        return divisors[1]
    if x_index == len(divisors) - 1:
        return divisors[-2]

    # figure out nearest number
    d_prev = x - divisors[x_index - 1]
    d_next = divisors[x_index + 1] - x

    if d_prev <= d_next:
        return divisors[x_index - 1]
    return divisors[x_index + 1]


def convert(args: argparse.Namespace):
    """Convert file_path into letters, one for each letter_size area"""

    if len(args.charlist) == 0:
        raise Exception("Charlist cannot be an empty string")

    mode = "L" if args.use_monochrome else "RGB"
    with Image.open(args.filename).convert(mode) as im:
        (width, height) = im.size

        # warn about slanted result
        if args.size and not is_common_divisor(args.size, width, height):
            divisors = common_divisors(width, height)
            print(
                f"[WARN]: {args.size} is not a common divisor of both the width and height, so the output may be slanted. Consider using one of these: {divisors}"
            )

        # calculate size if not given
        if not args.size:
            start_size = int(width * 0.02)
            args.size = find_closest_common_divisor(start_size, width, height)

        # split the image into args.size * args.size tiles
        # each tile will be converted to a single letter
        tiles: Sequence[Image.Image] = []
        for y in range(0, height, args.size):
            for x in range(0, width, args.size):
                tiles.append(crop(im, args.size, x, y))

        html_spans = []
        # normal image-to-letters
        if not args.use_ascii:
            for tile in tiles:
                (r, g, b) = calculate_color(tile, args)
                hex = rgb2hex(r, g, b)
                char = choice(args.charlist)
                html_spans.append(
                    f"<span style='color: {hex};'>{escape_html(char)}</span>"
                )
        # ascii
        else:
            for tile in tiles:
                (val, _, _) = calculate_color(tile, args)
                char = find_char_by_darkness(val / 255)
                # ASCII_CHARSET[int(val / 255 * len(ASCII_CHARSET) - 1)]
                html_spans.append(
                    f"<span style='color: #fff'>{escape_html(char)}</span>"
                )

        column_num = width // args.size
        generate_html_file(html_spans, column_num, args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to image file to convert")
    parser.add_argument(
        "-s",
        "--size",
        help="Size of area for each letter. Default is calculated based on image width.",
        type=int,
    )
    parser.add_argument(
        "-c",
        "--color",
        help="Background color; CSS-valid hex or color name. (Default #262626)",
        default="#262626",
    )
    parser.add_argument(
        "--fontsize",
        help="Letters' font-size; in px (Default 24)",
        type=int,
        default=24,
    )

    parser.add_argument(
        "--charlist",
        help="List of characters to be randomly used. (Default A-z0-9)",
        type=str,
        default="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#£¤$%/{}()[]=?+\\*~^-.:,;",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="file path for output file. (Default ./output.html)",
        type=str,
        default="./output.html",
    )

    # style flags
    parser.add_argument(
        "--use-monochrome",
        help="Generate a black and white picture",
        action="store_true",
    )
    parser.add_argument(
        "--use-common",
        help="Use the most common color in an area instead of the calculated average.",
        action="store_true",
    )
    parser.add_argument(
        "--use-ascii", help="Generate traditional ASCII art image.", action="store_true"
    )
    args = parser.parse_args()

    # conversion to black/white is required
    if args.use_ascii:
        args.use_monochrome = True

    convert(args)


if __name__ == "__main__":
    main()

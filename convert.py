"""
Author: Roope Sinisalo / Github/kripi-png
Date: 10.3.2024

Changelog:
3.6.2024: Introduce pyright typing, make avg color the default
10.6.2024: Calculate suitable pixel size based on image width and height


TODO:
- do something about the styling part
  - maybe allow loading css from file?
- actual ASCII art mode
"""

import argparse
from typing import Any, Sequence
from PIL import Image
from math import sqrt, ceil
from xml.etree import ElementTree as ET
from random import choice


def generate_html_file(spans: Sequence[str], columns: int, args: argparse.Namespace):
    """Create <style>, <head>, and <body> and save them to output.html"""

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
        for tile in tiles:
            (r, g, b) = calculate_color(tile, args)
            hex = rgb2hex(r, g, b)
            char = choice(args.charlist)
            html_spans.append(f"<span style='color: {hex};'>{char}</span>")

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
    args = parser.parse_args()

    convert(args)


if __name__ == "__main__":
    main()

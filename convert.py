"""
Author: Roope Sinisalo / Github/kripi-png
Date: 10.3.2024

Changelog:
3.6.2024: Introduce pyright typing, make avg color the default


TODO:
- option for set of characters used to generate the image
  - by default something like ABCDabcd$€&/123 but can be changed to just "X" for example
- allow using both monochrome and average color options at the same time
- do something about the styling part
  - maybe allow loading css from file?
- option to change output file name  / location
- ensure defaults are displayed in --help
- autocalculate suitable pixel size
  - sometimes with certain image sizes the result is slanted
    this usually gets fixed when the pixel size is adjusted to be multiplicative of the image size
"""

import argparse
from typing import Any, Sequence
from PIL import Image
from math import sqrt, ceil
from xml.etree import ElementTree as ET


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

    ET.ElementTree(html).write("output.html", encoding="unicode", method="html")


def rgb2hex(r: int, g: int, b: int) -> str:
    """Returns the hexadecimal for given rgb color.
    Taken from https://stackoverflow.com/a/19917486"""

    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def crop(image: Image.Image, size: int, x: int, y: int) -> Image.Image:
    """Return a crop of given size of the image at given coordinates"""

    box = (x, y, x + size, y + size)
    return image.crop(box)


def get_area_colors(image: Image.Image):
    """get list of colors and their counts in an image / tile"""

    # max colors is equal to total number of pixels
    max_colors = image.size[0] * image.size[1]

    # for whatever reason .getcolors type annotation is list[tuple[int, int]]
    # which conflicts with the *actual* type of list[tuple[int, tuple[int, int, int]]]
    # hence there's some annoying workaround.
    # I dont know if .getcolors as Any as Sequence ... would work?
    colors: Any | Sequence[tuple[int, tuple[int, int, int]]] = image.getcolors(
        max_colors
    )
    if not isinstance(colors, Sequence):
        raise Exception("Unexpected error: colors is not a list")
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


def calculate_color(image: Image.Image, args: argparse.Namespace):
    """
    Calculate the RGB values for the image or tile.
    By default, returns the average RGB color in the area.
    # If --use-common is used, returns the most common RGB value (based on pixel count)
    # If --use-monochrome is used, return the color in monochrome
    """

    colors = get_area_colors(image)
    total_pixels = image.size[0] * image.size[1]

    return calculate_average_color(colors, total_pixels)

    # if args.use_monochrome:
    #     # monochrome only has one value for the color: the luminance
    #     total = 0
    #     for count, color in colors:
    #         total += color * count

    #     total //= total_pixels
    #     return (total, total, total)

    # if args.use_common:
    #     print("pre-sort", colors)
    #     # sort by count in ascending order
    #     sorted_colors = sorted(colors, key=lambda x: x[0])
    #     print(sorted_colors)
    #     # use last color (highest count)
    #     (_, rgb) = sorted_colors[-1]
    #     return (*rgb)


def convert(args: argparse.Namespace):
    """Convert file_path into letters, one for each letter_size area"""

    with Image.open(args.filename).convert("RGB") as im:
        (width, height) = im.size

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
            html_spans.append(f"<span style='color: {hex};'>X</span>")

        column_num = width // args.size
        generate_html_file(html_spans, column_num, args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to image file to convert")
    parser.add_argument(
        "-s", "--size", help="size of area for each letter", default=10, type=int
    )
    parser.add_argument(
        "-c",
        "--color",
        help="background color; hex or color name (css)",
        default="#262626",
    )
    parser.add_argument(
        "--fontsize", help="Letters' font-size; in px", type=int, default=24
    )

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

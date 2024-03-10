import argparse
from PIL import Image
from xml.etree import ElementTree as ET

def save_to_file(spans: list[str], columns: int, args: argparse.Namespace):
    """Generate a HTML file"""

    html = ET.Element('html')
    head = ET.Element('head')
    body = ET.Element('body')
    for span in spans:
        body.append(ET.fromstring(span))
   
    style = ET.Element('style');
    body_style = f"body {{ background: {args.color}; display: grid; grid-template-columns: repeat({columns}, {args.fontsize}px); align-content: start; }}"
    span_style = f"span {{ font-size: {args.fontsize}px; }}"
    style.text = body_style + "\n" + span_style

    head.append(style)
    html.append(head)
    html.append(body)

    ET.ElementTree(html).write("output.html", encoding="unicode", method="html")
        
def rgb2hex(r: int, g: int, b: int) -> str:
    """Returns the hexadecimal for given rgb color.
    Taken from https://stackoverflow.com/a/19917486"""

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)
    
def crop(image: Image.Image, size: int, x: int, y: int) -> Image.Image:
    """Return a crop of given size of the image at given coordinates"""
   
    box = (x, y, x + size, y + size)
    return image.crop(box)

def calculate_color(image: Image.Image, args: argparse.Namespace):
    """
    Calculate the color for the image.
    Returns the hex of most common color in the image by default.
    Returns the hex of most common color in monochrome if --monochrome is used.
    """
    
    # getcolors takes maxcolors attributes with default value of 256
    # if it is exceeded, the method returns None
    # however, there can be up to width*height colors in an image
    colors = image.getcolors(image.size[0] * image.size[1]);
    
    # after sorting, the first color is most common
    sorted_colors = sorted(colors, key=lambda x: x[0])
    (count, rgb) = sorted_colors[0]

    # in case of monochrome images, there is only one value instead of three
    if (args.monochrome):
        return rgb2hex(rgb, rgb, rgb)
    
    return rgb2hex(*rgb)

def convert(args):
    """Convert file_path into letters, one for each letter_size area"""

    with Image.open(args.filename).convert("L" if args.monochrome else "RGB") as im:
        (width, height) = im.size;
        
        tiles = []
        for y in range(0, height, args.size):
            for x in range(0, width, args.size):
                tiles.append(crop(im, args.size, x, y))

        html_spans = []
        for tile in tiles:
            hex = calculate_color(tile, args)
            html_spans.append(f"<span style='color: {hex};'>X</span>")

        column_num = width // args.size
        save_to_file(html_spans, column_num, args)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to image file to convert")
    parser.add_argument("-s", "--size", help="size of area for each letter", default=10, type=int)
    parser.add_argument("-c", "--color", help="background color; hex or color name (css)", default="#262626")
    parser.add_argument("--fontsize", help="Letters' font-size; in px", type=int, default=24)

    parser.add_argument("--monochrome", help="Generate a black and white picture", action="store_true")
    args = parser.parse_args()

    convert(args)

if __name__ == '__main__':
    main()

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
    
    total_pixels = image.size[0] * image.size[1]
    # getcolors takes maxcolors attribute with default value of 256
    # if the number is exceeded, the method returns None
    # however, an image can have up to as many colors as it has pixels
    colors = image.getcolors(total_pixels)
    
    if args.monochrome:
        # monochrome only has one value for the color: the luminance
        total = 0
        for count, color in colors:
            total += color * count
        return rgb2hex(total, total, total)

    if args.use_average_color:
        # calculate average rgb
        r,g,b = 0,0,0
        for count, color in colors:
            r += color[0] * count
            g += color[1] * count
            b += color[2] * count
        r //= total_pixels
        g //= total_pixels
        b //= total_pixels
        return rgb2hex(r, g, b)

    # by default use most common color in the image
    # sort by count in ascending order
    sorted_colors = sorted(colors, key=lambda x: x[0])
    # use last color (highest count)
    (_, rgb) = sorted_colors[-1]
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
    parser.add_argument("--use-average-color", help="Use average color of area instead of the most common.", action="store_true")
    args = parser.parse_args()

    convert(args)

if __name__ == '__main__':
    main()

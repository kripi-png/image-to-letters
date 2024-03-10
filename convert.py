import argparse
from PIL import Image

def save_to_file(spans: list[str], columns: int):
    """Generate a HTML file"""
    
    with open('output.html', 'w') as file:
        html_start = "<!DOCTYPE html><html><head><style>span { font-size: 24px; margin-top: -4px; } body { " + f"background: darkgrey; display: grid; grid-template-columns: repeat({columns}, 17px) " + "}</style></head><body>"
        html_spans = "\n".join(spans)
        html_end = "</body></html>"
        file.write(html_start)
        file.write(html_spans)
        file.write(html_end)
        
def rgb2hex(r: int, g: int, b: int) -> str:
    """Taken from https://stackoverflow.com/a/19917486"""

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)
    
def crop(image: Image.Image, size: int, x: int, y: int) -> Image.Image:
    """Return a crop of given size of the image at given coordinates"""
   
    box = (x, y, x + size, y + size)
    return image.crop(box)

def calculate_color(image: Image.Image):
    """Calculate color for the area."""
    
    # getcolors takes maxcolors attributes with default value of 256
    # if it is exceeded, the method returns None
    # however, there can be up to width*height colors in an image
    colors = image.getcolors(image.size[0] * image.size[1]);
    sorted_colors = sorted(colors, key=lambda x: x[0])
    (count, rgb) = sorted_colors[0]
    
    return rgb2hex(*rgb)

def convert(file_path: str, letter_size: int):
    """Convert file_path into letters, one for each letter_size area"""

    with Image.open(file_path).convert() as im:
        (width, height) = im.size;
        
        tiles = []
        for y in range(0, height, letter_size):
            for x in range(0, width, letter_size):
                tiles.append(crop(im, letter_size, x, y))

        html_spans = []
        for tile in tiles:
            hex = calculate_color(tile)
            html_spans.append(f"<span style='color: {hex}'>X</span>")

        column_num = width // letter_size
        save_to_file(html_spans, column_num)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to image file to convert")
    parser.add_argument("-s", "--size", help="size of area for each letter", default=10, type=int)
    args = parser.parse_args()
    
    print(f'Starting to convert file {args.filename}')
    convert(args.filename, args.size)

if __name__ == '__main__':
    main()


# image-to-letters

Convert an image into letters by splitting it into tiles of certain size,
and using the average color of each tile for the respective character.

## Installation

1. Clone repo
2. `pip install -r requirements.txt`
3. `python3 convert.py -h`

## Basic usage

#### Automatically calculate the size of tiles:
`convert.py path/to/image`

#### Set tile size to 25x25
`convert.py path/to/image -s 25`

#### Change default background color
`convert.py image -c #000000`

#### Use most common color in tile instead of the average
`convert.py image --use-common`

#### Generate traditional ASCII art
`convert.py image --use-ascii`

#### Change used characters
`convert.py image --charlist 1234567890`

#### Change output file
`convert.py image --output path/and/name.html`

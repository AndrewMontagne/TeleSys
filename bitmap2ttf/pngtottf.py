#!/usr/bin/env python

# * Copyright 2021 Andrew O'Rourke
# * Copyright 2011 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import click, os, sys, re
from PIL import Image
from bitmap2ttf.convert import converter


class PngFontFileUnicode():

    image: Image
    font_height: int
    font_width: int
    start_index: int

    def __init__(self, input: click.File, font_width: int, font_height: int):
        self.image = Image.open(input).convert('RGB')
        self.font_width = font_width
        self.font_height = font_height

        image_width, image_height = self.image.size

        if (image_height % font_height != 0):
            raise Exception("Image height for %s is not divisible by the font height!" % input.name)

        if (image_width % font_width != 0):
            raise Exception("Image width for %s is not divisible by the font height!" % input.name)

        self.start_index = int(os.path.splitext(input.name)[0], 0)

    def process(self, glyph_map: dict):
        image_width, image_height = self.image.size

        glyphs_x = int(image_width / self.font_width)
        glyphs_y = int(image_height / self.font_height)

        for y in range(0, glyphs_y):
            for x in range(0, glyphs_x):
                index = self.start_index + (y * glyphs_x) + x
                
                left = x * self.font_width
                upper = y * self.font_height
                right = left + self.font_width
                lower = upper + self.font_height

                glyph = self.image.crop((left, upper, right, lower))
                
                r, g, b = glyph.getpixel((1, 1))

                if (r == 255 and (g + b) == 0):
                    continue

                glyph_map[index] = glyph




@click.command()
@click.argument('width', type=click.INT, required=True, nargs=1)
@click.argument('height', type=click.INT, required=True, nargs=1)
@click.argument('pngs', type=click.File('rb'), required=True, nargs=-1)
@converter
def pngtottf(width:int, height:int, pngs):
    glyph_map = {}

    for file in pngs:
        codepage = PngFontFileUnicode(file, width, height)
        codepage.process(glyph_map)

    return glyph_map, height, 0

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(pngtottf())
#!/usr/bin/env python

# * Copyright 2021 Andrew O'Rourke <andrew@montagne.uk>
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
from convert import convert
import yaml

class PngFontFileUnicode():

    image: Image
    font_height: int
    font_width: int
    start_index: int

    def __init__(self, input: click.File, start_index, font_width: int, font_height: int):
        self.image = Image.open(input).convert('RGB')
        self.font_width = font_width
        self.font_height = font_height
        self.start_index = start_index

        image_width, image_height = self.image.size

        if (image_height % font_height != 0):
            raise Exception("Image height for %s is not divisible by the font height!" % input.name)

        if (image_width % font_width != 0):
            raise Exception("Image width for %s is not divisible by the font height!" % input.name)

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


def pngtottf(width:int, height:int, pngs):
    glyph_map = {}

    for file in pngs:
        codepage = PngFontFileUnicode(file, width, height)
        codepage.process(glyph_map)

    return glyph_map, height, 0

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print(f"Usage: {sys.argv[0]} font.yaml")
        sys.exit(1)

    with open(sys.argv[1]) as yaml_stream:
        config = yaml.safe_load(yaml_stream)

    try:
        name = config["name"]
        width = config["width"]
        height = config["height"]
        glyph_config = config["glyphs"]
    except KeyError as e:
        print(f"Missing required config entry: {e.args[0]}")
        sys.exit(2)

    version = config.get("version", "0.0.1")
    weight = config.get("weight", "Medium")
    filename = config.get("filename", f"{name} {weight}.ttf")

    license = config.get("license", "Public Domain")
    license_url = config.get("license_url", None)

    designer = config.get("designer", "Anonymous")
    designer_url = config.get("designer_url", None)

    vendor = config.get("vendor", None)
    vendor_url = config.get("vendor_url", None)

    sample_text = config.get("sample_text", None)

    

    glyphs = {}

    for glyph_page in glyph_config:
        codepage = PngFontFileUnicode(glyph_page["file"], glyph_page["start"], width, height)
        codepage.process(glyphs)

    convert(glyphs, height, 0, name, filename, weight, license, version)

    

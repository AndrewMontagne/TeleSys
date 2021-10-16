# licenced GPL v2
# Copyright (c) 2021 Andrew O'Rourke <andrew@montagne.uk>
# Copyright (c) 2010 Kyle Keen
# Copyright (c) 2011-2019 Alistair Buxton <a.j.buxton@gmail.com>

# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import os
import shutil
import subprocess
import tempfile

from functools import wraps

import click
from PIL import ImageOps


from tqdm import tqdm

from outliner import outliner


def xml_wrap(tag, inner, **kwargs):
    kw = ' '.join('%s="%s"' % (k, str(v)) for k,v in kwargs.items())
    if inner is None:
        return f'<%s %s/>' % (tag, kw)
    return '<%s %s>%s</%s>\n' % (tag, kw, inner, tag)


def path(polys, xdim, ydim, em, par):
    d = '\n'.join(
        'M ' + 'L '.join(
            '%d %d ' % (int(x * par * em / ydim), int(y * em / ydim)) for (x, y) in poly
        ) + 'Z' for poly in polys
    )
    return xml_wrap('path', None, d=d, fill='currentColor')


def path_to_svg(polys, xdim, ydim, em, par):
    return '\n'.join([
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/SVG/DTD/svg10.dtd">',
        xml_wrap('svg', path(polys, xdim, ydim, em, par), width=int(par * xdim * em) / ydim, height=em),
    ])


def convert(glyphs, ascent, descent, name, ttf, weight, copyright, version, par=1, keep=False):

    em = 1000
    scale = em / (ascent + descent)
    print(ascent, descent)
    path = tempfile.mkdtemp()

    pe = open(os.path.join(path, ttf+'.pe'), 'w')
    pe.write('New()\n')
    pe.write('SetFontNames("%s", "%s", "%s", "%s", "%s", "%s")\n' % (name, name, name, weight, copyright, version))
    pe.write('SetTTFName(0x409, 1, "%s")\n' % name)
    pe.write('SetTTFName(0x409, 2, "Medium")\n')
    pe.write('SetTTFName(0x409, 4, "%s")\n' % name)
    pe.write('SetTTFName(0x409, 5, "%s")\n' % version)
    pe.write('SetTTFName(0x409, 6, "%s")\n' % name)
    pe.write('ScaleToEm(%d, %d)\n' % (int(ascent*scale), int(descent*scale)))
    pe.write('Reencode("unicodefull")\n')

    for i,v in tqdm(glyphs.items()):
        img = ImageOps.invert(v.convert("L"))
        polygons = outliner(img)
        (xdim, ydim) = img.size
        pe.write('SelectSingletons(UCodePoint(%d))\n' % i)

        if polygons:
            # Only generate the svg file for non-empty glyph (ie not SPACE and similar).
            svg = path_to_svg(polygons, xdim, ydim, em, par)
            open(os.path.join(path, '%04x.svg' % i), 'w').write(svg)
            # FontForge does not like empty SVG files, but if we just don't import anything
            # then we get a blank glyph for this codepoint.
            pe.write('Import("%s/%04x.svg", 0)\n' % (path, i))

        pe.write('SetWidth(%d)\n' % int(par*xdim*em/ydim))
        pe.write('CanonicalStart()\n')
        pe.write('CanonicalContours()\n')

    pe.write('Generate("%s/%s")\n' % (os.getcwd(), ttf))
    pe.close()

    subprocess.check_call(['fontforge', '-script', os.path.join(path, ttf+'.pe')])
    if keep:
        print(path)
    else:
        shutil.rmtree(path)


def converter(f):
    @click.option('-t', '--ttf', type=click.Path(exists=False), required=True, help="Name of the output file")
    @click.option('-n', '--name', type=str, required=True, help="The actual name of the font face")
    @click.option('-w', '--weight', type=str, default='Medium', help="The weight of the font")
    @click.option('-c', '--copyright', type=str, required=True, help="The copyright string of the font")
    @click.option('-v', '--version', type=str, default='0.0.1', help="The version string of the font")
    @click.option('-k', '--keep', is_flag=True, help='Keep intermediate files.')
    @click.option('-a', '--ascent', type=int, default=None, help='Override input ascent.')
    @click.option('-d', '--descent', type=int, default=None, help='Override input descent.')
    @click.option('-x', '--xscale', type=float, default=1.0, help='X scale.')
    @click.option('-y', '--yscale', type=float, default=1.0, help='Y scale.')
    @wraps(f)
    def _convert(ttf, name, weight, copyright, version, keep, ascent, descent, xscale, yscale, *args, **kwargs):
        glyphs, _ascent, _descent = f(*args, **kwargs)
        if ascent is not None:
            _ascent = ascent
        if descent is not None:
            _descent = descent
        convert(glyphs, _ascent, _descent, name, ttf, weight, copyright, version, keep=keep, par=xscale/yscale)
    return _convert


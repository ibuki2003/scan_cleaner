#!/bin/env python
import sys
import io
import argparse
import cv2
from PIL import Image
from pathlib import Path
import img2pdf

import paper_size
from crop import process_page
from xmap import xmap

import time

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dpi', required=True, type=int)
    parser.add_argument('--size', required=True, help='paper size HxW in mm or standard name')
    parser.add_argument('--direction',
                        choices=['landscape', 'portrait'],
                        required=False,
                        help='paper direction')
    parser.add_argument('--mode',
                        choices=['color', 'gray'],
                        default='gray')
    parser.add_argument('--level', action='store')
    parser.add_argument('-P', '--max-process', type=int, help='number of process to run parallel')
    parser.add_argument('-o', '--output', required=True, help='Output pdf file or directory')

    parser.add_argument('input', nargs='+', help='Input file. set to "-" to read stdin')

    args = parser.parse_args()

    size = paper_size.get_size_in_dots(args.size, args.dpi)
    if len(size) != 2:
        raise Exception('Invalid paper size')

    if args.direction is not None:
        d = 'landscape' if size[0] > size[1] else 'portrait'
        if d != args.direction:
            size = size[::-1]

    if args.input == ['-']:
        args.input = ( line.strip() for line in sys.stdin )

    level = list(map(int, args.level.split(','))) if args.level else None

    processed_images = xmap(
        lambda fn: (
            fn,
            process_page(cv2.imread(fn), size, args.mode or 'color', level)
        ),
        args.input,
        processes=args.max_process,
    )
    processed_images = list(processed_images)

    if args.output.endswith('.pdf'):
        with open(args.output,"wb") as f:
            pages_bytes = xmap(
                img_to_bytes,
                [ i[1] for i in processed_images ],
                processes=args.max_process,
            )
            # TODO: speedup; img2pdf is too slow
            b = img2pdf.convert(pages_bytes)
            if b is not None:
                f.write(b)
    else:
        out = Path(args.output)
        if out.exists() and not out.is_dir():
            raise Exception('output is not directory')
        out.mkdir(exist_ok=True)


        def save_img(entry):
            fn, img = entry
            dest = out / fn
            dest.parent.mkdir(exist_ok=True)
            cv2.imwrite(str(dest), img, [int(cv2.IMWRITE_PNG_COMPRESSION),9])
        xmap(save_img, processed_images, processes=args.max_process)


def img_to_bytes(img):
    img_bytes = io.BytesIO()
    if len(img.shape) == 3 and img.shape[2] == 3:
        # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        image = Image.fromarray(img, 'RGB')
        image.save(img_bytes, format='PNG')
    else:
        image = Image.fromarray(img, 'L')
        image.save(img_bytes, format='TIFF', compression='tiff_adobe_deflate')
    return img_bytes.getvalue()


if __name__ == '__main__':
    cli()

"""Prepare the supplied profile JPEG for luminance-to-ASCII conversion."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/het-portrait.jpeg"
PREPPED = ROOT / "assets/het-portrait-prepped.png"

# Hand-traced silhouette of the supplied 400 × 400 photo. The feather follows
# its hair, glasses, and jacket edges while lifting the wall and dark trim.
SILHOUETTE = (
    (0, 400), (0, 363), (9, 326), (19, 292), (23, 263), (30, 246),
    (39, 238), (60, 231), (93, 220), (104, 215), (113, 209), (117, 201),
    (132, 190), (148, 178), (155, 164), (164, 151), (170, 136),
    (171, 117), (176, 103), (183, 88), (189, 84), (193, 70),
    (204, 56), (218, 48), (235, 44), (251, 47), (267, 45),
    (277, 49), (290, 58), (300, 70), (310, 79), (316, 92),
    (322, 105), (321, 118), (313, 133), (302, 145), (289, 154),
    (280, 168), (267, 184), (260, 200), (279, 203), (311, 211),
    (324, 216), (334, 231), (340, 252), (350, 282), (359, 312),
    (370, 339), (386, 366), (399, 392), (400, 400),
)


def prepare(source, destination, keep_background=False):
    with Image.open(source) as photo:
        luminance = photo.convert("L")
    # Find the content on the original pixels, before lifting the background.
    content = luminance.getbbox()
    if source.resolve() == SOURCE.resolve() and luminance.size == (400, 400) and not keep_background:
        mask = Image.new("L", luminance.size)
        ImageDraw.Draw(mask).polygon(SILHOUETTE, fill=255)
        luminance = Image.composite(luminance, Image.new("L", luminance.size, 255),
                                    mask.filter(ImageFilter.GaussianBlur(3)))
    if content:
        luminance = luminance.crop(content)
    luminance = ImageEnhance.Contrast(luminance).enhance(1.08)
    luminance = luminance.filter(ImageFilter.UnsharpMask(radius=1.2, percent=165, threshold=3))
    luminance.thumbnail((400, 400), Image.Resampling.LANCZOS)
    square = Image.new("L", (400, 400), 255)
    square.paste(luminance, ((400 - luminance.width) // 2, (400 - luminance.height) // 2))
    square.save(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=PREPPED)
    parser.add_argument("--keep-background", action="store_true")
    args = parser.parse_args()
    prepare(args.source, args.output, args.keep_background)

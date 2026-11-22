"""Map the prepared portrait's luminance to animated monospaced SVG rows."""

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

from .prep_photo import PREPPED
from .svg_art import INK, MONO, ROOT, svg, timing


PORTRAIT = ROOT / "het-ascii.svg"
SIDE = 800
RAMP = " .`:-=+*cs#%@"
NAMESPACE = "{http://www.w3.org/2000/svg}"


def sample_rows(source, columns=180):
    rows = round(columns * 8 / 15)
    with Image.open(source) as photo:
        grid = photo.convert("L").resize((columns, rows), Image.Resampling.LANCZOS)
    lookup = [RAMP[round((len(RAMP) - 1) * (1 - (tone / 255) ** 1.1))]
              if tone < 214 else " " for tone in range(256)]
    return [
        "".join(lookup[grid.getpixel((x, y))] for x in range(columns))
        for y in range(rows)
    ]


def portrait_rows(rows):
    stride = SIDE / len(rows)
    return "".join(
        f'<text class="portrait-row" {timing(.25 + i * .018)} '
        f'xml:space="preserve" x="0" y="{(i + .78) * stride:.4f}" fill="{INK}" '
        f'font-family="{MONO}" font-size="{stride * .90:.4f}" '
        f'textLength="{SIDE}" lengthAdjust="spacingAndGlyphs">{row}</text>\n'
        for i, row in enumerate(rows)
    )


def generate(source, destination, columns):
    description = "Grayscale ASCII portrait generated from Het Patel’s original profile photograph."
    body = portrait_rows(sample_rows(source, columns))
    destination.write_text(svg(SIDE, SIDE, "Het Patel portrait", description, body, ("mono",)), encoding="utf-8")


def read_rows(path=PORTRAIT):
    return [element.text or "" for element in ET.parse(path).getroot().findall(f"{NAMESPACE}text")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=PREPPED)
    parser.add_argument("--output", type=Path, default=PORTRAIT)
    parser.add_argument("--columns", type=int, default=180)
    args = parser.parse_args()
    if args.columns < 8:
        parser.error("--columns must be at least 8")
    generate(args.source, args.output, args.columns)

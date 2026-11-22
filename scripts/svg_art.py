"""Shared SVG image primitives for the README and standalone portrait."""

import base64
import os
from functools import cache
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER, PAPER_DEEP = "#f3f3f1", "#e2e2de"
INK, INK_SOFT, MUTED, RULE = "#111111", "#3a3a3c", "#6e6e73", "#dcdcd7"
BLUE, RED, YELLOW = "#2f55ff", "#ef3b2d", "#ffc81a"
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, sans-serif"
MONO = "'Geist Mono', ui-monospace, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "instrument-serif.woff"),
    "italic": ("Instrument Serif", "italic", 400, "instrument-serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-regular.woff"),
    "semibold": ("Geist", "normal", 600, "geist-semibold.woff"),
    "mono": ("Geist Mono", "normal", 400, "geist-mono.woff"),
}

ANIMATIONS = """
@keyframes lift {
  from { opacity: 0; transform: translateY(16px) }
}
@keyframes reveal { from { opacity: 0 } }
@keyframes grow { from { transform: scaleY(0) } }
@keyframes cell {
  0% { opacity: 0; transform: scale(.3) }
  70% { opacity: 1; transform: scale(1.15) }
}
@keyframes beacon { 50% { opacity: .25 } }
@keyframes arrow-right { 50% { transform: translateX(4px) } }
@keyframes arrow-up { 50% { transform: translate(3px, -3px) } }
@keyframes swing {
  0% { opacity: 0; transform: translateY(90px) rotate(-9deg) scale(.6) }
  55% { opacity: 1; transform: translateY(-10px) rotate(2deg) scale(1.05) }
  75% { transform: translateY(3px) rotate(-.8deg) scale(.98) }
  90% { transform: translateY(-1px) rotate(.2deg) scale(1.01) }
}
@keyframes label-in { from { opacity: 0; transform: translateX(-26px) } }
@keyframes arrow-in {
  0% { opacity: 0; transform: translateX(-30px) }
  60% { opacity: 1; transform: translateX(6px) }
}
@keyframes roll-in { from { transform: translateY(60px) } }
@keyframes ripple {
  from { opacity: .7; transform: scale(.2) }
  to { opacity: 0; transform: scale(2.4) }
}
@keyframes gloss {
  from { transform: translateX(-260px) skewX(-20deg) }
  22%, 100% { transform: translateX(420px) skewX(-20deg) }
}
.lift, .reveal, .portrait-row, .bar, .cell, .swing, .label-in, .arrow-in, .roll-in, .ring {
  animation-delay: var(--delay, 0s);
  animation-fill-mode: both;
  transform-box: fill-box;
}
.lift { animation-name: lift; animation-duration: .8s; animation-timing-function: cubic-bezier(.2,.7,.2,1) }
.reveal, .portrait-row { animation-name: reveal; animation-duration: .9s; animation-timing-function: ease-out }
.portrait-row { animation-duration: .35s }
.bar { animation-name: grow; animation-duration: .8s; animation-timing-function: cubic-bezier(.2,.7,.2,1); transform-origin: bottom }
.cell { animation-name: cell; animation-duration: .4s; animation-timing-function: ease-out; transform-origin: center }
.beacon { animation: beacon 1.6s ease-in-out infinite }
.arrow-right { animation: arrow-right 1.8s ease-in-out var(--delay, 0s) infinite }
.arrow-up { animation: arrow-up 1.8s ease-in-out infinite }
.swing { animation-name: swing; animation-duration: 1.1s; animation-timing-function: cubic-bezier(.2,.8,.2,1); transform-origin: 50% 60% }
.label-in { animation-name: label-in; animation-duration: .6s; animation-timing-function: cubic-bezier(.2,.7,.2,1) }
.arrow-in { animation-name: arrow-in; animation-duration: .7s; animation-timing-function: cubic-bezier(.2,.7,.2,1) }
.roll-in { animation-name: roll-in; animation-duration: .8s; animation-timing-function: cubic-bezier(.15,.8,.2,1) }
.ring { animation-name: ripple; animation-duration: 1s; animation-timing-function: ease-out; transform-origin: center }
.gloss { animation: gloss 5s ease-in-out var(--delay) infinite backwards }
.motion { display: inline }
.still { display: none }
.name-shine { fill: url(#sweep) }
"""


def static_mode():
    return os.environ.get("STATIC") == "1"


@cache
def font_face(key):
    family, style, weight, file = FONT_FILES[key]
    encoded = base64.b64encode((ROOT / "fonts" / file).read_bytes()).decode("ascii")
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{encoded}) format('woff')}}\n")


def svg(width, height, title, description, body, fonts):
    css = "".join(font_face(font) for font in fonts)
    if not static_mode():
        css += ".motion { display: none }\n@media (prefers-reduced-motion: no-preference) {"
        css += ANIMATIONS + "}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}" height="{height}" '
        f'viewBox="0 0 {width:.3f} {height}" role="img" aria-labelledby="title description">\n'
        f'<title id="title">{escape(title)}</title>\n<desc id="description">{escape(description)}</desc>\n'
        f'<style>{css}</style>\n{body}\n</svg>\n'
    )


def timing(seconds):
    return f'style="--delay: {seconds:.3f}s"'


def text(x, y, content, family=SANS, size=14, fill=INK, attrs=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" {attrs}>{escape(str(content))}</text>\n')

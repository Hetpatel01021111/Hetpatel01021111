"""Build the animated SVG images embedded in the profile README."""

import argparse
import re
from datetime import date
from pathlib import Path

from .fetch_contributions import PROFILE, load_snapshot
from .startup import read_metrics, read_valuation
from .svg_art import (
    BLUE, INK, INK_SOFT, MONO, MUTED, PAPER, PAPER_DEEP, RED, ROOT, RULE, SANS,
    SERIF, YELLOW, static_mode, svg, text, timing,
)


WIDTH = 880
COLUMN = WIDTH / 3
TILE_WIDTH = COLUMN - 8
BOTTOM = 12
WHITE = "#ffffff"
DISPLAY_FONTS = ("serif", "italic", "sans", "mono")
HEAT_COLORS = (PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", BLUE, "#1a3be0")
PROJECTS = (
    ("FinBot", ("Personal finance tools for tracking", "transactions, budgeting, and", "AI-powered spending insights."), "JavaScript", BLUE),
    ("AeroTrackAI", ("Uses live flight data to forecast", "aircraft usage and schedule", "preventive maintenance."), "TypeScript", RED),
    ("Fractal", ("Combines keyword and semantic", "search using Elasticsearch and", "Gemini embeddings."), "TypeScript", YELLOW),
)


def panel(w, h, fill=PAPER):
    return f'<rect width="{w:.3f}" height="{h}" rx="14" fill="{fill}"/>'


def lines(x, y, content, height, size=14, fill=INK_SOFT):
    return "".join(text(x, y + i * height, line, size=size, fill=fill) for i, line in enumerate(content))


def animated(cls, delay):
    return f'class="{cls}" {timing(delay)}'


def column_svg(index, height, title, description, body, fonts):
    body = f'<g transform="translate({index * 4} 0)">{body}</g>'
    return svg(COLUMN, height + BOTTOM, title, description, body, fonts)


def hero():
    shine = ""
    if not static_mode():
        stops = "".join(
            f'<stop offset="{offset}" stop-color="{color}"/>'
            for offset, color in ((0, INK), (.42, INK), (.50, BLUE), (.58, INK), (1, INK))
        )
        shine = f"""
<defs>
  <linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1="0" x2="600" y1="0" y2="0">
    {stops}
    <animateTransform attributeName="gradientTransform" type="translate"
      values="-600 0;600 0;600 0" keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>"""

    body = f"""
{shine}
{panel(WIDTH, 420)}
<g class="reveal">
  <rect class="beacon" x="48" y="49" width="8" height="8" rx="2" fill="{BLUE}"/>
  {text(66, 57, "FOUNDER & CEO AT SHIPMITRA", MONO, 12, MUTED, 'letter-spacing="1"')}
</g>
{text(44, 190, "Het", SERIF, 116, attrs=animated("lift", .15) + ' letter-spacing="-2.5"')}
{text(44, 290, "Patel", SERIF, 116, attrs=animated("lift name-shine", .30) + ' font-style="italic" letter-spacing="-2.5"')}
<g {animated("lift", .55)}>
  {lines(48, 338, ("Founder, engineer, and builder.", "Working on logistics, AI, and real-world products."), 27, 18)}
</g>
<g {animated("reveal", .80)}>
  {text(48, 396, "shipmitra.net", MONO, 13)}
  {text(154, 396, "↗", MONO, 13, BLUE, 'class="arrow-up"')}
</g>
<defs>
  <pattern id="route-grid" width="18" height="18" patternUnits="userSpaceOnUse">
    <circle cx="5" cy="5" r="1" fill="{MUTED}" opacity=".27"/>
  </pattern>
</defs>
<g id="shipping-route" aria-hidden="true" {animated("reveal", .35)}>
  <g transform="translate(529 60)">
    <rect width="303" height="300" rx="14" fill="{PAPER_DEEP}" fill-opacity=".35"/>
    <rect x="14" y="14" width="275" height="272" rx="8" fill="url(#route-grid)"/>
    <path d="M51 243h55q45 0 45-45v-33q0-51 51-51h10q39 0 39-39V56"
      fill="none" stroke="{BLUE}" stroke-opacity=".65" stroke-width="2.5"
      stroke-linecap="round" stroke-dasharray="1 7"/>
    <circle cx="51" cy="243" r="8" fill="{PAPER}" stroke="{BLUE}" stroke-width="2"/>
    <circle cx="51" cy="243" r="2.5" fill="{BLUE}"/>
    <circle cx="251" cy="56" r="12" fill="{BLUE}" fill-opacity=".12"/>
    <circle cx="251" cy="56" r="5" fill="{BLUE}"/>
    <g stroke="{BLUE}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">
      <path d="m151 94 47 25v51l-47 25-47-25v-51z" fill="{PAPER}"/>
      <path d="m104 119 47 25 47-25m-47 25v51m-23-88 47 25v15" fill="none"/>
    </g>
  </g>
</g>"""
    description = ("Founder & CEO at ShipMitra. Founder, engineer, and builder working on logistics, AI, "
                   "and real-world products.")
    return svg(WIDTH, 420 + BOTTOM, "Het Patel", description, body, DISPLAY_FONTS)


def count_up(value, label, size, fill, begin):
    tail = f' <tspan font-style="italic">{label}</tspan>' if label else ""

    def frame(number):
        return (f'<text x="22" y="112" font-family="{SERIF}" font-size="{size}" fill="{fill}">'
                f'{number}{tail}</text>')

    match = re.fullmatch(r"(\$?)([0-9][0-9,]*)([KMB]?)", value)
    if static_mode() or match is None:
        return frame(value)

    prefix, digits, suffix = match.groups()
    target = int(digits.replace(",", ""))
    count = 18
    duration = 1.1
    frames = []
    for step in range(count + 1):
        fraction = step / count
        number = round(target * (1 - (1 - fraction) ** 3))
        display = value if step == count else f"{prefix}{number:,}{suffix}"
        start = begin + duration * fraction
        period = "" if step == count else f' dur="{duration / count:.6f}s"'
        animation = f'<set attributeName="opacity" to="1" begin="{start:.6f}s"{period}/>'
        frames.append(f'<g opacity="0">{frame(display)}{animation}</g>')
    return (
        f'<g class="still">{frame(value)}</g>'
        f'<g class="motion" aria-hidden="true">{"".join(frames)}</g>'
    )


def world_tile(index, label, fill, foreground, figure, unit, copy, support=""):
    height, delay = 210, 3.1 + index * .25
    size = 44 if len(figure + unit) <= 13 else min(40, 465 // len(figure + unit) + 10)
    effects = ""
    if not static_mode():
        effects = f"""
  <g clip-path="url(#outline)">
    <circle {animated("motion ring", delay + .5)} cx="{TILE_WIDTH - 40:.3f}" cy="170" r="60"
      fill="none" stroke="{foreground}" stroke-opacity=".5" stroke-width="2"/>
    <rect {animated("motion gloss", delay + 1.4)} x="0" y="-20" width="90" height="250" fill="url(#gloss)"/>
  </g>"""
    body = f"""
<defs>
  <clipPath id="outline">{panel(TILE_WIDTH, height)}</clipPath>
  <clipPath id="number-slot"><rect x="0" y="63" width="{TILE_WIDTH:.3f}" height="61"/></clipPath>
  <linearGradient id="gloss">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
</defs>
<g {animated("swing", delay)}>
  {panel(TILE_WIDTH, height, fill)}
{effects}
  {text(24, 38, label, MONO, 12, foreground, animated("label-in", delay + .35) + ' letter-spacing="1.2"')}
  <g {animated("arrow-in", delay + .5)}>
    {text(250, 38, "→", MONO, 14, foreground, animated("arrow-right", delay + 1.3))}
  </g>
  <g clip-path="url(#number-slot)">
    <g {animated("roll-in", delay + .45)}>
      {count_up(figure, unit, size, foreground, delay + .45)}
    </g>
  </g>
{text(24, 134, support, SERIF, 19, foreground, animated("lift", delay + .65) + ' font-style="italic"') if support else ""}
  {"".join(text(24, (159 if support else 150) + i * 20, line, SANS, 14, foreground,
                animated("lift", delay + .75 + i * .1)) for i, line in enumerate(copy))}
</g>"""
    description = " ".join(part for part in (figure, unit, support, *copy) if part)
    return column_svg(index, height, label, description, body, DISPLAY_FONTS)


def contribution_level(count):
    return sum(count > boundary for boundary in (0, 5, 15, 30, 50))


def heatmap(data):
    height = 245
    heading = (f'<text x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}" '
               f'{animated("lift", .8)}>Every day, <tspan font-style="italic" fill="{BLUE}">in blue</tspan></text>')
    body = panel(WIDTH, height) + heading
    if data is None:
        body += text(44, 154, "GitHub contribution data is temporarily unavailable.", size=16, fill=MUTED)
        return svg(WIDTH, height + BOTTOM, "Every day, in blue", "Contribution data unavailable.", body, DISPLAY_FONTS)

    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    sunday_offset = (first.weekday() + 1) % 7
    columns = (len(days) + sunday_offset + 6) // 7
    origin, step = 44, min(15, (WIDTH - 80) / columns)
    right = origin + columns * step - 3
    legend_x = right - len(HEAT_COLORS) * 14 - 28
    body += text(right, 60, "REFRESHED DAILY", MONO, 12, MUTED,
                 animated("reveal", .8) + ' text-anchor="end" letter-spacing="1"')
    labels = []
    cells = []
    for index, day in enumerate(days):
        stamp = date.fromisoformat(day["date"])
        week, row = divmod(index + sunday_offset, 7)
        x, y = origin + week * step, 96 + row * 15
        count = day["count"]
        cells.append(f'<rect x="{x:.2f}" y="{y}" width="12" height="12" rx="3" '
                     f'fill="{HEAT_COLORS[contribution_level(count)]}" {animated("cell", 1 + week * .03 + row * .02)}>'
                     f'<title>{stamp.isoformat()} · {count:,} contributions</title></rect>')
        if row == 0 and stamp.day <= 7 and x < legend_x - 60:
            labels.append(text(round(x, 2), 217, stamp.strftime("%b"), MONO, 11, MUTED))
    legend = "".join(
        f'<rect x="{legend_x + i * 14:.2f}" y="207" width="11" height="11" rx="2.5" fill="{color}"/>'
        for i, color in enumerate(HEAT_COLORS)
    )
    body += f"""
{"".join(cells)}
<g {animated("reveal", 2.4)}>
  {"".join(labels)}
  {text(round(legend_x - 8, 2), 217, "less", MONO, 11, MUTED, 'text-anchor="end"')}
  {legend}
  {text(round(right - 24, 2), 217, "more", MONO, 11, MUTED)}
</g>"""
    scope = data["range"]
    description = f'{data["total_contributions"]:,} public GitHub contributions, {scope["start"]} to {scope["end"]}.'
    return svg(WIDTH, height + BOTTOM, "Every day, in blue", description, body, DISPLAY_FONTS)


def activity(data):
    height = 340
    body = panel(WIDTH, height) + text(
        40, 58, "THE LAST 12 MONTHS ON GITHUB", MONO, 12, MUTED, animated("reveal", 1.9) + ' letter-spacing="1"'
    )
    if data is None:
        body += text(38, 114, "Activity unavailable", SERIF, 52)
        body += text(40, 154, "GitHub contribution data is temporarily unavailable.", size=16, fill=MUTED)
        return svg(WIDTH, height + BOTTOM, "The last 12 months on GitHub", "Activity unavailable.", body, DISPLAY_FONTS)

    months = data["monthly"][-12:]
    best_month = max(months[:-1] or months, key=lambda month: month["total"])
    scale = max(1, max(month["total"] for month in months))
    slot = 570 / len(months)
    bar_width = slot - 10
    for i, month in enumerate(months):
        x = 40 + i * slot
        partial = i == len(months) - 1
        highlight = month == best_month and month["total"] > 0 and not partial
        color = "#c9c9c4" if partial else BLUE if highlight else INK
        bar_height = max(4, round(140 * month["total"] / scale))
        label = date.fromisoformat(month["month"] + "-01").strftime("%b")
        delay = 2.20 + i * .07
        body += (
            f'<rect x="{x:.2f}" y="{292 - bar_height}" width="{bar_width:.2f}" height="{bar_height}" '
            f'rx="4" fill="{color}" {animated("bar", delay)}>'
            f'<title>{month["month"]} · {month["total"]:,} contributions{" (month in progress)" if partial else ""}</title></rect>'
        )
        attrs = ' text-anchor="middle"'
        midpoint = round(x + bar_width / 2, 2)
        body += text(midpoint, 314, label, MONO, 11, MUTED, animated("reveal", delay) + attrs)
        if highlight:
            body += text(midpoint, 282 - bar_height, f'{month["total"]:,}', MONO, 11, BLUE, animated("cell", 3.2) + attrs)

    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    total = data["total_contributions"]
    active = data["active_days"]
    busiest = data["best_day"]
    stats = (
        (f'{current} <tspan font-style="italic">{"day" if current == 1 else "days"}</tspan>', f"current streak · longest {longest}"),
        (f'{active}<tspan fill="{MUTED}"> / {len(data["days"])}</tspan>', "days with contributions"),
        (f'{busiest["count"]:,}', "on the busiest day"),
    )
    body += (f'<text x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}" '
             f'{animated("lift", 2.0)}>{total:,} <tspan font-style="italic">contributions</tspan></text>')
    for i, (figure, caption) in enumerate(stats):
        y = 104 + 92 * i
        body += f"""
<g {animated("lift", 2.6 + i * .15)}>
  <text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{figure}</text>
  {text(650, y + 24, caption, size=13, fill=MUTED)}
</g>"""
        if i < 2:
            body += f'<path d="M650 {y + 44}h190" stroke="{RULE}" {animated("reveal", 2.6)}/>'
    monthly_summary = ", ".join(f'{month["month"]}: {month["total"]:,}' for month in months)
    scope = data["range"]
    desc = (f'{total:,} public contributions across {active} days from {scope["start"]} to {scope["end"]}. '
            f"Current streak {current} days. "
            f"Longest streak {longest} days. Busiest day: {busiest['count']:,} contributions"
            f"{' on ' + busiest['date'] if busiest['date'] else ''}. "
            f"Chart totals for the 12 latest calendar months: {monthly_summary}.")
    return svg(WIDTH, height + BOTTOM, "The last 12 months on GitHub", desc, body, DISPLAY_FONTS)


def project_card(index, name, description, language, color):
    height = 176
    body = f"""
{panel(TILE_WIDTH, height)}
<g {animated("lift", 4.6 + index * .12)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  {text(40, 39, name, size=18, attrs='font-weight="600"')}
  {lines(24, 72, description, 21)}
  {text(24, 152, language, MONO, 12, MUTED)}
</g>"""
    return column_svg(index, height, name, " ".join(description) + " " + language + ".", body, ("sans", "semibold", "mono"))


def section_title(dark):
    fg = "#e6edf3" if dark else INK
    body = (f'<text x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}" {animated("lift", 4.4)}>'
            'What I’m <tspan font-style="italic">coding</tspan></text>')
    return svg(WIDTH, 64, "What I’m coding", f"Featured public repositories from {PROFILE}.",
               body, ("serif", "italic"))


def render(output):
    contributions = load_snapshot()
    brand, unit, copy = read_metrics()
    value, company, offer = read_valuation()
    cards = {
        "hero": hero(),
        "heatmap": heatmap(contributions),
        "activity": activity(contributions),
        "build": world_tile(0, "BUILD", BLUE, WHITE, "1", "startup", (
            "ShipMitra - simplifying domestic",
            "and international shipping",
            "through technology.",
        )),
        "brand": world_tile(1, "BRAND", RED, WHITE, brand, unit, copy),
        "valuation": world_tile(2, "VALUATION", YELLOW, INK, value, "", (offer,), company),
        "title-coding-light": section_title(False),
        "title-coding-dark": section_title(True),
    }
    for index, project in enumerate(PROJECTS):
        cards[f"repo-{project[0].lower()}"] = project_card(index, *project)

    output.mkdir(parents=True, exist_ok=True)
    for name, art in cards.items():
        (output / f"{name}.svg").write_text(art, encoding="utf-8")
    print(f"Generated {len(cards)} {'static' if static_mode() else 'animated'} SVG cards in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "cards")
    render(parser.parse_args().output)

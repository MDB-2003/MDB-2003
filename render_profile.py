#!/usr/bin/env python3
"""Build the terminal profile cards from a portrait photo."""

import base64
import io
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets"
PHOTO = Path(
    "/Users/mohith/.cursor/projects/Users-mohith-Documents-Projects-github-repo/assets/"
    "WhatsApp_Image_2026-09-30_at_16.00.40-e6e6bb44-4017-4b89-8ced-fd8398ed20d2.jpg"
)
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"

WIDTH = 1260
HEIGHT = 680
RAMP = " .:-=+*#%@"

LINKS = {
    "email.personal": "mailto:dodapanenimohith2003@gmail.com",
    "linkedin": "https://www.linkedin.com/in/dodapaneni-balaraju-mohith/",
}

SECTIONS = [
    (
        None,
        [
            ("name", "Mohith Dodapaneni Balaraju"),
            ("first_seen", "Jun-07-2003"),
        ],
    ),
    (
        "Education",
        [
            ("University Of Houston", "Master's in Engineering Data Science and AI"),
            ("", "2025 — current"),
            ("GITAM", "Bachelor's in Computer Science and Engineering"),
            ("", "2021 — 2025"),
        ],
    ),
    (
        "Software",
        [
            ("languages", "Python, SQL"),
            ("stack", "ML, ANN, Power BI"),
            ("arsenal", "Snowflake · dbt · GCP · AWS"),
        ],
    ),
    (
        "Hobbies",
        [
            ("hobbies", "cricket, gym, exploring"),
        ],
    ),
    (
        "Interests",
        [
            ("interests", "data engineering"),
            ("", "AI & ML"),
            ("", "building projects that are useful for day-to-day life"),
        ],
    ),
    (
        "Contact",
        [
            ("email.personal", "dodapanenimohith2003@gmail.com"),
            ("linkedin", "dodapaneni-balaraju-mohith"),
        ],
    ),
]

THEMES = {
    "dark": {
        "card": (13, 17, 23),
        "bar": (22, 27, 34),
        "border": (48, 54, 61),
        "text": (255, 255, 255),
        "muted": (255, 166, 87),
        "faint": (125, 133, 144),
        "mint": (110, 231, 183),
        "value": (165, 214, 255),
        "portrait_bg": (13, 17, 23),
    },
    "light": {
        "card": (255, 255, 255),
        "bar": (246, 248, 250),
        "border": (208, 215, 222),
        "text": (36, 41, 47),
        "muted": (149, 56, 0),
        "faint": (194, 207, 222),
        "mint": (15, 118, 110),
        "value": (10, 48, 105),
        "portrait_bg": (13, 17, 23),
    },
}


def flood_background(arr, thresh=50):
    height, width = arr.shape[:2]
    values = arr.astype(np.int16)
    visited = np.zeros((height, width), np.uint8)
    background = np.zeros((height, width), bool)
    queue = deque()
    for x in range(0, width, 2):
        for y in (0, height - 1):
            visited[y, x] = 1
            queue.append((y, x))
    for y in range(0, height, 2):
        for x in (0, width - 1):
            if not visited[y, x]:
                visited[y, x] = 1
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        background[y, x] = True
        base = values[y, x]
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if ny < 0 or nx < 0 or ny >= height or nx >= width or visited[ny, nx]:
                continue
            if int(np.abs(values[ny, nx] - base).sum()) <= thresh:
                visited[ny, nx] = 1
                queue.append((ny, nx))
    return background


def fill_holes(person):
    height, width = person.shape
    empty = ~person
    seen = np.zeros_like(empty, bool)
    queue = deque()
    for x in range(width):
        for y in (0, height - 1):
            if empty[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))
    for y in range(height):
        for x in (0, width - 1):
            if empty[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < height and 0 <= nx < width and empty[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                queue.append((ny, nx))
    return person | (empty & ~seen)


def portrait_source():
    image = np.array(Image.open(PHOTO).convert("RGB"))
    person = fill_holes(~flood_background(image, 50))
    rows = np.where(person.mean(1) > 0.04)[0]
    top = int(rows[0])
    columns = np.where(person[top : top + 190].mean(0) > 0.12)[0]
    left, right = int(columns[0]) - 8, int(columns[-1]) + 8
    bottom = top + 300
    crop = image[max(0, top - 8) : bottom, max(0, left) : right]
    mask = person[max(0, top - 8) : bottom, max(0, left) : right]
    crop = crop.copy()
    crop[~mask] = (13, 17, 23)
    picture = Image.fromarray(crop)
    picture = ImageEnhance.Color(picture).enhance(1.35)
    picture = ImageEnhance.Contrast(picture).enhance(1.4)
    return picture.filter(ImageFilter.SHARPEN)


def portrait_cells():
    source = np.array(portrait_source()).astype(np.float32)
    src_h, src_w = source.shape[:2]
    cols = 58
    rows = max(28, int(round(cols * (src_h / src_w) * 0.50)))
    grid = []
    for y in range(rows):
        y0 = int(y * src_h / rows)
        y1 = max(y0 + 1, int((y + 1) * src_h / rows))
        line = []
        for x in range(cols):
            x0 = int(x * src_w / cols)
            x1 = max(x0 + 1, int((x + 1) * src_w / cols))
            cell = source[y0:y1, x0:x1]
            luminance = cell.mean(2)
            coverage = float((luminance > 22).mean())
            if coverage < 0.3:
                line.append((" ", "#0d1117"))
                continue
            body = cell[luminance > 22]
            average = body.mean(0) if len(body) else cell.mean((0, 1))
            darkest = float(luminance.min())
            mean_l = float(luminance[luminance > 22].mean())
            in_face = 0.08 < (y / rows) < 0.58 and 0.22 < (x / cols) < 0.78
            if in_face and darkest < 42 and mean_l > 75:
                glyph = "@"
                color = (236, 242, 247)
            elif mean_l < 50:
                glyph = "+"
                color = (176, 184, 194)
            else:
                level = min(1.0, mean_l / 230)
                glyph = RAMP[min(len(RAMP) - 1, int(level * (len(RAMP) - 1)))]
                color = tuple(int(max(0, min(255, channel))) for channel in average)
            line.append((glyph, "#{:02x}{:02x}{:02x}".format(*color)))
        grid.append(line)
    return grid


def render_portrait():
    grid = portrait_cells()
    font_size = 12
    font = ImageFont.truetype(FONT_PATH, font_size)
    cell_w = float(font.getlength("M"))
    cell_h = font_size + 1
    rows = len(grid)
    cols = len(grid[0])
    image = Image.new("RGB", (int(cols * cell_w) + 8, int(rows * cell_h) + 8), (13, 17, 23))
    draw = ImageDraw.Draw(image)
    for y, line in enumerate(grid):
        for x, (glyph, color) in enumerate(line):
            if glyph == " ":
                continue
            draw.text((4 + x * cell_w, 4 + y * cell_h), glyph, font=font, fill=color)
    return image


def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def draw_dotted_row(draw, font, x, y, right, label, value, theme):
    label_width = font.getlength(label) if label else 0
    value_width = font.getlength(value)
    if label:
        draw.text((x, y), label, font=font, fill=theme["muted"])
    gap_left = x + label_width + (8 if label else 0)
    gap_right = right - value_width - 8
    dot_width = font.getlength(".")
    if gap_right > gap_left and dot_width > 0:
        count = int((gap_right - gap_left) / dot_width)
        draw.text((gap_left, y), "." * count, font=font, fill=theme["faint"])
    draw.text((right - value_width, y), value, font=font, fill=theme["value"])


def draw_section(draw, font, x, y, right, title, theme):
    heading = f"- {title} "
    draw.text((x, y), heading, font=font, fill=theme["text"])
    rule_x = x + font.getlength(heading)
    dash_width = font.getlength("-")
    count = int((right - rule_x) / dash_width) if dash_width else 0
    draw.text((rule_x, y), "-" * max(count, 0), font=font, fill=theme["faint"])


def render_card(theme_name, portrait):
    theme = THEMES[theme_name]
    font = ImageFont.truetype(FONT_PATH, 22)
    head = ImageFont.truetype(FONT_PATH, 34)
    row_h = 36
    rows = sum(len(fields) for _, fields in SECTIONS)
    headers = sum(1 for title, _ in SECTIONS if title)
    block_h = 78 + rows * row_h + headers * 52
    labels = [label for _, fields in SECTIONS for label, _ in fields if label]
    values = [value for _, fields in SECTIONS for _, value in fields]
    text_width = int(max(font.getlength(label) for label in labels) + 72 + max(font.getlength(value) for value in values))
    left_width = portrait.width + 48
    width = left_width + 36 + text_width + 36
    height = max(portrait.height + 150, block_h + 130)
    card = Image.new("RGB", (width, height), theme["card"])
    draw = ImageDraw.Draw(card)
    rounded_rect(draw, (0, 0, width - 1, height - 1), 18, theme["card"])
    draw.rectangle((0, 0, width, 52), fill=theme["bar"])
    draw.rectangle((0, 30, width, 52), fill=theme["bar"])
    draw.line((0, 52, width, 52), fill=theme["border"], width=1)
    for color, cx in (((255, 95, 87), 26), ((254, 188, 46), 52), ((40, 200, 64), 78)):
        draw.ellipse((cx - 8, 16, cx + 8, 32), fill=color)
    title_font = ImageFont.truetype(FONT_PATH, 16)
    title = "mohith@github — zsh"
    title_w = title_font.getlength(title)
    draw.text(((width - title_w) / 2, 16), title, font=title_font, fill=theme["muted"])

    pad_x = 20
    pad_y = max(16, (height - 72 - 28 - portrait.height) // 2)
    card.paste(portrait, (pad_x, 72 + pad_y))
    draw.line((left_width, 76, left_width, height - 28), fill=theme["border"], width=1)

    x = left_width + 36
    right = width - 36
    y = 84 + max(0, (height - 110 - block_h) // 2)
    draw.text((x, y), "mohith@github", font=head, fill=theme["mint"])
    y += 44
    name_w = head.getlength("mohith@github")
    draw.line((x, y, x + name_w, y), fill=theme["mint"], width=2)
    y += 20
    for title, fields in SECTIONS:
        if title:
            y += 12
            draw_section(draw, font, x, y, right, title, theme)
            y += 40
        for label, value in fields:
            draw_dotted_row(draw, font, x, y, right, label, value, theme)
            y += row_h
    return card


def hex_color(color):
    return "#{:02x}{:02x}{:02x}".format(*color)


def xml_text(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(theme_name, portrait):
    theme = THEMES[theme_name]
    font = ImageFont.truetype(FONT_PATH, 20)
    labels = [label for _, fields in SECTIONS for label, _ in fields if label]
    values = [value for _, fields in SECTIONS for _, value in fields]
    text_width = int(max(font.getlength(label) for label in labels) + 64 + max(font.getlength(value) for value in values))
    portrait_w, portrait_h = portrait.size
    buffer = io.BytesIO()
    portrait.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    left = 36 + portrait_w + 28
    width = left + text_width + 28
    row_h = 32
    info_rows = sum(len(fields) for _, fields in SECTIONS)
    headers = sum(1 for title, _ in SECTIONS if title)
    block_h = 86 + info_rows * row_h + headers * 46
    height = max(portrait_h + 110, block_h + 96)
    label_color = hex_color(theme["muted"])
    value_color = hex_color(theme["value"])
    dot_color = hex_color(theme["faint"])
    text_color = hex_color(theme["text"])
    mint = hex_color(theme["mint"])
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="20">',
        f'<rect width="{width}" height="{height}" rx="16" fill="{hex_color(theme["card"])}"/>',
        f'<rect width="{width}" height="48" fill="{hex_color(theme["bar"])}"/>',
        f'<line x1="0" y1="48" x2="{width}" y2="48" stroke="{hex_color(theme["border"])}"/>',
    ]
    for color, cx in ("#ff5f57", 24), ("#febc2e", 48), ("#28c840", 72):
        parts.append(f'<circle cx="{cx}" cy="24" r="7" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2}" y="29" fill="{dot_color}" font-size="15" text-anchor="middle">mohith@github — zsh</text>'
    )
    portrait_y = 64 + max(0, (height - 88 - portrait_h) // 2)
    parts.append(
        f'<image x="20" y="{portrait_y}" width="{portrait_w}" height="{portrait_h}" href="data:image/png;base64,{encoded}" xlink:href="data:image/png;base64,{encoded}"/>'
    )
    parts.append(f'<line x1="{left - 18}" y1="64" x2="{left - 18}" y2="{height - 24}" stroke="{hex_color(theme["border"])}"/>')
    y = 78 + max(0, (height - 90 - block_h) // 2)
    parts.append(f'<text x="{left}" y="{y}" fill="{mint}" font-size="30">mohith@github</text>')
    name_w = int(ImageFont.truetype(FONT_PATH, 30).getlength("mohith@github"))
    parts.append(f'<line x1="{left}" y1="{y + 10}" x2="{left + name_w}" y2="{y + 10}" stroke="{mint}" stroke-width="2"/>')
    y += 46
    right = width - 24
    for title, fields in SECTIONS:
        if title:
            y += 14
            heading = f"- {title} "
            rule = "-" * max(1, int((right - left - font.getlength(heading)) / font.getlength("-") * 0.92))
            parts.append(
                f'<text x="{left}" y="{y}" font-size="20"><tspan fill="{text_color}">{xml_text(heading)}</tspan><tspan fill="{dot_color}">{rule}</tspan></text>'
            )
            y += 36
        for label, value in fields:
            label_w = font.getlength(label) if label else 0
            value_w = font.getlength(value)
            gap = (right - left - label_w - value_w - 28) * 0.9
            count = max(2, int(gap / font.getlength(".")))
            label_svg = f'<tspan fill="{label_color}">{xml_text(label)} </tspan>' if label else ""
            parts.append(
                f'<text x="{left}" y="{y}" font-size="20">{label_svg}<tspan fill="{dot_color}">{"." * count}</tspan></text>'
            )
            decoration = ' text-decoration="underline"' if label in LINKS else ""
            value_text = (
                f'<text x="{right}" y="{y}" font-size="20" text-anchor="end" fill="{value_color}"'
                f'{decoration}>{xml_text(value)}</text>'
            )
            if label in LINKS:
                parts.append(f'<a href="{LINKS[label]}" target="_blank">{value_text}</a>')
            else:
                parts.append(value_text)
            y += row_h
    parts.append("</svg>")
    return "\n".join(parts), (width, height)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    portrait = render_portrait()
    for name in THEMES:
        render_card(name, portrait).save(OUT / f"profile-{name}.png", optimize=True)
        svg, size = render_svg(name, portrait)
        path = OUT / f"profile-{name}.svg"
        path.write_text(svg)
        print(path, size)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the terminal profile cards from a portrait photo."""

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
            ("Houston", "Master's in Engineering Data Science and AI"),
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
        "text": (230, 237, 243),
        "muted": (139, 148, 158),
        "faint": (72, 79, 88),
        "mint": (126, 224, 198),
        "value": (121, 192, 255),
        "portrait_bg": (13, 17, 23),
    },
    "light": {
        "card": (255, 255, 255),
        "bar": (246, 248, 250),
        "border": (208, 215, 222),
        "text": (31, 35, 40),
        "muted": (101, 109, 118),
        "faint": (175, 184, 193),
        "mint": (15, 118, 110),
        "value": (9, 105, 218),
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


def render_portrait():
    source = np.array(portrait_source()).astype(np.float32)
    src_h, src_w = source.shape[:2]
    cols = 58
    rows = max(28, int(round(cols * (src_h / src_w) * 0.50)))
    font_size = 12
    font = ImageFont.truetype(FONT_PATH, font_size)
    cell_w = float(font.getlength("M"))
    cell_h = font_size + 1
    image = Image.new("RGB", (int(cols * cell_w) + 8, int(rows * cell_h) + 8), (13, 17, 23))
    draw = ImageDraw.Draw(image)
    for y in range(rows):
        y0 = int(y * src_h / rows)
        y1 = max(y0 + 1, int((y + 1) * src_h / rows))
        for x in range(cols):
            x0 = int(x * src_w / cols)
            x1 = max(x0 + 1, int((x + 1) * src_w / cols))
            cell = source[y0:y1, x0:x1]
            luminance = cell.mean(2)
            coverage = float((luminance > 22).mean())
            if coverage < 0.3:
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
    font = ImageFont.truetype(FONT_PATH, 15)
    head = ImageFont.truetype(FONT_PATH, 22)
    row_h = 24
    rows = sum(len(fields) for _, fields in SECTIONS)
    headers = sum(1 for title, _ in SECTIONS if title)
    block_h = 34 + rows * row_h + headers * 36
    height = max(portrait.height + 120, block_h + 120)
    card = Image.new("RGB", (WIDTH, height), theme["card"])
    draw = ImageDraw.Draw(card)
    rounded_rect(draw, (0, 0, WIDTH - 1, height - 1), 18, theme["card"])
    draw.rectangle((0, 0, WIDTH, 48), fill=theme["bar"])
    draw.rectangle((0, 28, WIDTH, 48), fill=theme["bar"])
    draw.line((0, 48, WIDTH, 48), fill=theme["border"], width=1)
    for color, cx in (((255, 95, 87), 24), ((254, 188, 46), 48), ((40, 200, 64), 72)):
        draw.ellipse((cx - 7, 16, cx + 7, 30), fill=color)
    title_font = ImageFont.truetype(FONT_PATH, 15)
    title = "mohith@github — zsh"
    title_w = title_font.getlength(title)
    draw.text(((WIDTH - title_w) / 2, 16), title, font=title_font, fill=theme["muted"])

    left_width = 500
    pad_x = max(16, (left_width - portrait.width) // 2)
    pad_y = max(16, (height - 68 - 28 - portrait.height) // 2)
    card.paste(portrait, (28 + pad_x, 68 + pad_y))
    draw.line((left_width + 16, 72, left_width + 16, height - 28), fill=theme["border"], width=1)

    x = left_width + 40
    right = WIDTH - 36
    y = 78 + max(8, (height - 100 - block_h) // 2)
    draw.text((x, y), "mohith@github", font=head, fill=theme["mint"])
    y += 30
    name_w = head.getlength("mohith@github")
    draw.line((x, y, x + name_w, y), fill=theme["faint"], width=1)
    y += 16
    for title, fields in SECTIONS:
        if title:
            y += 8
            draw_section(draw, font, x, y, right, title, theme)
            y += 28
        for label, value in fields:
            draw_dotted_row(draw, font, x, y, right, label, value, theme)
            y += row_h
    return card


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    portrait = render_portrait()
    for name in THEMES:
        path = OUT / f"profile-{name}.png"
        render_card(name, portrait).save(path, optimize=True)
        print(path)


if __name__ == "__main__":
    main()

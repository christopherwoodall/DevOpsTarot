"""Generate social preview image for OpenGraph / Twitter Cards."""

import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from tarotgen.cards import DOCS_DIR, load_site_config


def generate_social_preview():
    """Generates 1200x630 social-preview.png for OpenGraph / Twitter Cards."""
    w, h = 1200, 630
    img = Image.new("RGBA", (w, h), (11, 13, 18, 255))
    draw = ImageDraw.Draw(img)

    cyan = (0, 229, 255)
    green = (0, 255, 102)
    gold = (255, 215, 0)
    purple = (138, 43, 226)
    magenta = (255, 0, 127)

    # Diagonal gradient background (purple to black)
    for y in range(h):
        ratio = y / h
        r = int(11 + (60 - 11) * (1 - ratio))
        g = int(13 + (20 - 13) * (1 - ratio))
        b = int(18 + (80 - 18) * (1 - ratio))
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Radial starburst rays behind title
    center_x, center_y = 350, 200
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        x2 = int(center_x + math.cos(rad) * 400)
        y2 = int(center_y + math.sin(rad) * 250)
        draw.line([(center_x, center_y), (x2, y2)], fill=(gold[0], gold[1], gold[2], 30), width=2)

    # Grid overlay (subtle)
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(20, 30, 48, 80), width=1)
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(20, 30, 48, 80), width=1)

    # Comic-style borders
    draw.rectangle([20, 20, w - 20, h - 20], outline=gold, width=6)
    draw.rectangle([32, 32, w - 32, h - 32], outline=purple, width=3)
    draw.rectangle([42, 42, w - 42, h - 42], outline=(gold[0], gold[1], gold[2], 120), width=1)

    # Corner gem accents with glow
    for cx, cy in [(30, 30), (w - 30, 30), (30, h - 30), (w - 30, h - 30)]:
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=gold, width=4)
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=magenta)

    # Lightning bolt accents
    draw.polygon([(600, 50), (620, 90), (610, 90), (630, 140), (600, 100), (610, 100)], fill=(cyan[0], cyan[1], cyan[2], 180))
    draw.polygon([(900, 500), (920, 540), (910, 540), (930, 590), (900, 550), (910, 550)], fill=(gold[0], gold[1], gold[2], 180))

    # Load fonts
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_body = ImageFont.load_default()

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                font_title = ImageFont.truetype(p, 64)
                font_sub = ImageFont.truetype(p, 32)
                font_body = ImageFont.truetype(p, 22)
                break
            except Exception:
                pass

    # Left side: Hero card (The Commit / The Fool)
    hero_path = os.path.join(DOCS_DIR, "cards", "00-the-fool.png")
    if os.path.exists(hero_path):
        hero = Image.open(hero_path).convert("RGBA")
        hero_h = 480
        hero_w = int(hero.width * (hero_h / hero.height))
        hero = hero.resize((hero_w, hero_h), Image.Resampling.LANCZOS)
        # Slight rotation for comic dynamism
        hero = hero.rotate(-4, expand=True, resample=Image.Resampling.BICUBIC)
        hx = 50
        hy = (h - hero.height) // 2
        img.paste(hero, (hx, hy), hero)
        draw.rectangle([hx - 3, hy - 3, hx + hero.width + 3, hy + hero.height + 3], outline=gold, width=4)

    # Load social preview config
    _cfg = load_site_config()
    _sp = _cfg.get("social_preview", {})
    headline = _sp.get("headline", "DEVOPS TAROT")
    subheadline = _sp.get("subheadline", "YOUR PIPELINE IS DOOMED")
    cta = _sp.get("cta", "DRAW A CARD.")
    tagline = _sp.get("tagline", "78 Oracle Cards for SREs & Devs")
    _site = _cfg.get("site", {})
    bottom_badge = _sp.get("bottom_badge", f"⚡ {_site.get('cname', 'devopstarot.com')} ⚡")

    # Right side: Fun sales copy
    tx = 520
    # Headline with drop shadow
    draw.text((tx + 2, 122), headline, font=font_title, fill=(0, 0, 0, 200))
    draw.text((tx, 120), headline, font=font_title, fill=gold)
    draw.text((tx, 200), subheadline, font=font_sub, fill=cyan)
    draw.text((tx, 245), cta, font=font_sub, fill=green)
    draw.text((tx, 310), tagline, font=font_body, fill=(200, 220, 245))

    # Bottom badge bar
    badge_text = bottom_badge
    badge_font = font_body
    bbox = badge_font.getbbox(badge_text)
    bw = bbox[2] - bbox[0]
    bx = (w - bw) // 2
    draw.rectangle([bx - 20, h - 60, bx + bw + 20, h - 30], fill=(19, 23, 34, 200), outline=gold, width=2)
    draw.text((bx, h - 54), badge_text, font=badge_font, fill=gold)

    out_path = os.path.join(DOCS_DIR, "social-preview.png")
    img.save(out_path)
    print(f"Generated social preview image -> {out_path}")


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DOCS_DIR, "cards"), exist_ok=True)
    generate_social_preview()
    print("Done.")


if __name__ == "__main__":
    main()

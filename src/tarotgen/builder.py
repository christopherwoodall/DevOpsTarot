import os
import json
import yaml
from pathlib import Path

from tarotgen.cards import DOCS_DIR, CARDS_YML, MEANINGS_JSON, MEANINGS_ORIGINAL_JSON, load_site_config
from tarotgen.preview import generate_social_preview


def ensure_docs_dir():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DOCS_DIR, "cards"), exist_ok=True)


def generate_cname_and_readme():
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
        import math
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


def generate_cname_and_readme():
    _cfg = load_site_config()
    cname = _cfg.get("site", {}).get("cname", "devopstarot.com")
    cname_path = os.path.join(DOCS_DIR, "CNAME")
    if not os.path.exists(cname_path):
        with open(cname_path, "w", encoding="utf-8") as f:
            f.write(f"{cname}\n")
    print(f"Verified CNAME -> {cname_path}")

    readme_path = os.path.join(DOCS_DIR, "README.md")
    readme_content = """# DevOps Tarot - GitHub Pages Site

This directory contains the production-ready static site deployment for **DevOps Tarot**.

## Features
- **78 Custom DevOps Tarot Cards**: Major & Minor Arcana (Code, Logs, Bugs, Servers).
- **Single Card Draw & 3-Card Spread**: Past (Legacy), Present (Production), Future (Deployment).
- **Upright & Reversed Interpretations**: Highlighting both optimal practices and technical debt/outages.
- **Original / DevOps Toggle**: Switch between classic Rider-Waite tarot meanings and enhanced DevOps/SRE interpretations.
- **Corporate Comic Style**: Bold line art, thick expressive outlines, bright cel-shaded colors, and playful cartoon energy.
- **Card Browser**: Browse all 78 cards at `cards.html`.

## Build Instructions
1. Generate card graphics (GPT-Image-2):
   ```bash
   tarotgen-generate
   ```
2. Build static HTML site:
   ```bash
   tarotgen-build
   ```

Deploy to GitHub Pages by configuring repository settings to serve from the `/docs` folder!
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Generated README -> {readme_path}")


def build_html_site():
    with open(CARDS_YML, "r", encoding="utf-8") as f:
        cards_yml = yaml.safe_load(f)
    with open(MEANINGS_JSON, "r", encoding="utf-8") as f:
        meanings = json.load(f)
    with open(MEANINGS_ORIGINAL_JSON, "r", encoding="utf-8") as f:
        meanings_original = json.load(f)

    def build_cards_list(meanings_dict):
        cards_list = []
        for c in cards_yml["cards"]:
            cid = c["id"]
            info = meanings_dict.get(cid, {})
            img_url = f"cards/{cid}.png"
            cards_list.append({
                "id": cid,
                "slug": cid,
                "name": info.get("name", cid.replace("-", " ").title()),
                "scene": c.get("scene", ""),
                "upright": info.get("upright", ""),
                "reversed": info.get("reversed", ""),
                "image": img_url
            })
        return cards_list

    cards_list_devops = build_cards_list(meanings)
    cards_list_original = build_cards_list(meanings_original)

    cards_data = {
        "devops": cards_list_devops,
        "original": cards_list_original,
    }
    cards_data_path = os.path.join(DOCS_DIR, "cards-data.json")
    with open(cards_data_path, "w", encoding="utf-8") as f:
        json.dump(cards_data, f, indent=2, ensure_ascii=False)
    print(f"Generated cards data -> {cards_data_path}")

    # Copy static templates to docs/
    pkg_dir = Path(__file__).parent
    _cfg = load_site_config()
    cname = _cfg.get("site", {}).get("cname", "devopstarot.com")
    og_url = f"https://{cname}"
    og_image = f"https://{cname}/social-preview.png"

    for src_name, dst_name in [
        ("style.css", "style.css"),
        ("index.html", "index.html"),
        ("cards.html", "cards.html"),
    ]:
        src_path = pkg_dir / src_name
        dst_path = DOCS_DIR / dst_name
        if src_path.exists():
            text = src_path.read_text(encoding="utf-8")
            if src_name == "index.html":
                text = text.replace('content="social-preview.png"', f'content="{og_image}"')
                if 'property="og:url"' not in text:
                    text = text.replace(
                        '<meta property="og:type" content="website" />',
                        f'<meta property="og:url" content="{og_url}" />\n  <meta property="og:type" content="website" />'
                    )
            dst_path.write_text(text, encoding="utf-8")
            print(f"Copied {src_name} -> {dst_path}")
        else:
            print(f"[WARNING] Template not found: {src_path}")

    print("Static site build finished successfully!")


def main():
    ensure_docs_dir()
    generate_social_preview()
    generate_cname_and_readme()
    build_html_site()
    print("All done.")


if __name__ == "__main__":
    main()

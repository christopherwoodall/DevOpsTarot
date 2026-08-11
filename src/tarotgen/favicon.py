"""Generate favicon.png for the DevOps Tarot site."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from tarotgen.cards import DOCS_DIR, load_site_config


def generate_favicon():
    """Generates a favicon.png using Pillow."""
    _cfg = load_site_config()
    _fav = _cfg.get("favicon", {})
    _site = _cfg.get("site", {})

    size = _fav.get("size", 64)
    text = _fav.get("text", "🎴")
    bg_color = _fav.get("background", "#0B0D12")
    border_color = _fav.get("border_color", "#00FFD7")
    text_color = _fav.get("text_color", "#FFD700")

    # Convert hex to RGB tuples
    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    bg = hex_to_rgb(bg_color)
    border = hex_to_rgb(border_color)
    text_c = hex_to_rgb(text_color)

    img = Image.new("RGBA", (size, size), bg + (255,))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle border (tarot card shape)
    corner_radius = size // 8
    border_width = max(2, size // 32)
    draw.rounded_rectangle(
        [border_width, border_width, size - border_width, size - border_width],
        radius=corner_radius,
        outline=border,
        width=border_width
    )

    # Draw inner accent line
    inner_pad = border_width * 2
    draw.rounded_rectangle(
        [inner_pad, inner_pad, size - inner_pad, size - inner_pad],
        radius=corner_radius - inner_pad // 2,
        outline=text_c + (180,),
        width=1
    )

    # Draw text in center
    font_size = size // 2
    font = ImageFont.load_default()
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, font_size)
                break
            except Exception:
                pass

    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - bbox[1] // 2
    draw.text((tx, ty), text, font=font, fill=text_c)

    out_path = os.path.join(DOCS_DIR, "favicon.png")
    img.save(out_path)
    print(f"Generated favicon -> {out_path}")


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    generate_favicon()
    print("Done.")


if __name__ == "__main__":
    main()

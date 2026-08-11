import os
import json
import yaml
from PIL import Image, ImageDraw, ImageFont

from tarotgen.cards import DOCS_CARDS_DIR, load_meanings

CARDS_SRC_DIR = "./cards"

# 1:1.75 Tarot aspect ratio canvas size
CANVAS_W = 1024
CANVAS_H = 1792

# Palette
BG_COLOR = (10, 10, 12, 255)       # #0a0a0c
PANEL_BG = (19, 23, 34, 255)      # #131722
NEON_GREEN = (0, 255, 102, 255)    # #00ff66
NEON_CYAN = (0, 229, 255, 255)     # #00e5ff
BORDER_ACCENT = (0, 255, 102, 255)
INNER_BORDER = (0, 229, 255, 180)
TEXT_WHITE = (240, 245, 255, 255)


def ensure_dirs():
    os.makedirs(DOCS_CARDS_DIR, exist_ok=True)


def try_load_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def format_card(src_path, dst_path, card_name="DEVOPS TAROT", is_back=False):
    """Formats a 1024x1024 raw card into a 1024x1792 tarot card layout."""
    # 1. Create canvas
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # 2. Outer Double Accent Border
    # Outer Border (16px inset)
    draw.rectangle([16, 16, CANVAS_W - 16, CANVAS_H - 16], outline=NEON_GREEN, width=4)
    # Inner Border (28px inset)
    draw.rectangle([28, 28, CANVAS_W - 28, CANVAS_H - 28], outline=INNER_BORDER, width=2)

    # Corner Tech Dots & Accents
    corner_inset = 28
    dot_r = 6
    for cx in [corner_inset, CANVAS_W - corner_inset]:
        for cy in [corner_inset, CANVAS_H - corner_inset]:
            draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=NEON_CYAN)

    # 3. Load & Place Raw Image Centered Vertically in Upper Region
    # Image frame box: 920x920 at x=52, y=80
    box_w, box_h = 920, 920
    box_x = (CANVAS_W - box_w) // 2  # 52
    box_y = 80

    if os.path.exists(src_path):
        raw_img = Image.open(src_path).convert("RGBA")
        raw_img = raw_img.resize((box_w, box_h), Image.Resampling.LANCZOS)
        canvas.paste(raw_img, (box_x, box_y), raw_img)
    else:
        # Placeholder panel if raw image missing
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=PANEL_BG, outline=NEON_CYAN, width=3)

    # Outer Frame for raw image
    draw.rectangle([box_x - 4, box_y - 4, box_x + box_w + 4, box_y + box_h + 4], outline=NEON_CYAN, width=3)
    draw.rectangle([box_x - 10, box_y - 10, box_x + box_w + 10, box_y + box_h + 10], outline=NEON_GREEN, width=1)

    # 4. Upper Sub-header / Header Line (between image and banner)
    header_font = try_load_font(22)
    header_text = "DEVOPS TAROT // OPERATIONAL WISDOM" if not is_back else "DEVOPS TAROT // SYSTEM BACK"
    bbox = header_font.getbbox(header_text)
    tw = bbox[2] - bbox[0]
    draw.text(((CANVAS_W - tw) // 2, 1020), header_text, font=header_font, fill=(0, 229, 255, 200))

    # Decorative separator line
    draw.line([(64, 1060), (CANVAS_W - 64, 1060)], fill=NEON_CYAN, width=2)

    # 5. Middle Ornamental Tech Grid / Symbols
    symbols_font = try_load_font(28)
    sym_text = "⚡ [0x00..0xFF] ⚡" if not is_back else "⬡ RECURSIVE ARCHITECTURE ⬡"
    s_bbox = symbols_font.getbbox(sym_text)
    s_tw = s_bbox[2] - s_bbox[0]
    draw.text(((CANVAS_W - s_tw) // 2, 1100), sym_text, font=symbols_font, fill=NEON_GREEN)

    # 6. Bottom Banner Bar Layout
    # Banner area from y=1200 to y=1680
    banner_x1 = 52
    banner_y1 = 1200
    banner_x2 = CANVAS_W - 52
    banner_y2 = 1680

    # Draw Banner Panel
    draw.rectangle([banner_x1, banner_y1, banner_x2, banner_y2], fill=PANEL_BG, outline=NEON_GREEN, width=3)
    draw.rectangle([banner_x1 + 6, banner_y1 + 6, banner_x2 - 6, banner_y2 - 6], outline=INNER_BORDER, width=1)

    # Corner cuts inside banner panel
    draw.line([(banner_x1, banner_y1 + 20), (banner_x1 + 20, banner_y1)], fill=NEON_CYAN, width=3)
    draw.line([(banner_x2 - 20, banner_y1), (banner_x2, banner_y1 + 20)], fill=NEON_CYAN, width=3)
    draw.line([(banner_x1, banner_y2 - 20), (banner_x1 + 20, banner_y2)], fill=NEON_CYAN, width=3)
    draw.line([(banner_x2 - 20, banner_y2), (banner_x2, banner_y2 - 20)], fill=NEON_CYAN, width=3)

    # Banner Content: Card Name in Bold Uppercase Text with Neon Accent
    name_font = try_load_font(44)
    card_name_upper = card_name.upper()

    # Wrap text if long
    n_bbox = name_font.getbbox(card_name_upper)
    n_w = n_bbox[2] - n_bbox[0]
    if n_w > (banner_x2 - banner_x1 - 40):
        name_font = try_load_font(34)
        n_bbox = name_font.getbbox(card_name_upper)
        n_w = n_bbox[2] - n_bbox[0]

    n_x = (CANVAS_W - n_w) // 2
    n_y = banner_y1 + 60
    draw.text((n_x, n_y), card_name_upper, font=name_font, fill=NEON_GREEN)

    # Subtitle / Accent Line under Name
    draw.line([(n_x, n_y + 60), (n_x + n_w, n_y + 60)], fill=NEON_CYAN, width=3)

    # Additional DevOps Emblem / Subtext inside banner
    tag_font = try_load_font(24)
    tag_text = "QUERY THE SYSTEM // EXPAND YOUR MIND" if not is_back else "SYSTEM NODE BACK // ENCRYPTED"
    t_bbox = tag_font.getbbox(tag_text)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text(((CANVAS_W - t_w) // 2, banner_y1 + 160), tag_text, font=tag_font, fill=(200, 220, 245, 220))

    # Bottom status badge
    badge_font = try_load_font(18)
    badge_text = "[ STACK: 78 CARDS // SYSTEM READY ]"
    b_bbox = badge_font.getbbox(badge_text)
    b_w = b_bbox[2] - b_bbox[0]
    draw.text(((CANVAS_W - b_w) // 2, banner_y1 + 240), badge_text, font=badge_font, fill=NEON_CYAN)

    # Save output formatted image
    canvas.save(dst_path)


def main():
    ensure_dirs()
    meanings = load_meanings()

    print("Formatting 1024x1024 raw images into 1024x1792 (1:1.75 ratio) tarot cards in ./docs/cards/...")

    # Format card back
    back_src = os.path.join(CARDS_SRC_DIR, "card-back.png")
    back_dst = os.path.join(DOCS_CARDS_DIR, "card-back.png")
    format_card(back_src, back_dst, card_name="SYSTEM BACK", is_back=True)
    print(f"Formatted card back -> {back_dst}")

    # Format each card
    if os.path.exists(CARDS_SRC_DIR):
        raw_files = [f for f in os.listdir(CARDS_SRC_DIR) if f.endswith(".png") and f != "card-back.png"]
        for idx, filename in enumerate(sorted(raw_files), 1):
            card_id = filename.replace(".png", "")
            card_info = meanings.get(card_id, {})
            card_name = card_info.get("name", card_id.replace("-", " ").title())
            
            src_path = os.path.join(CARDS_SRC_DIR, filename)
            dst_path = os.path.join(DOCS_CARDS_DIR, filename)

            format_card(src_path, dst_path, card_name=card_name, is_back=False)
            if idx % 10 == 0 or idx == len(raw_files):
                print(f"[{idx}/{len(raw_files)}] Formatted {card_id} -> {dst_path}")

    print("Formatting complete!")


if __name__ == "__main__":
    main()

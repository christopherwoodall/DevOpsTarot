#!/usr/bin/env python3
"""Generate 3 style samples for user review."""

import os
import base64
import concurrent.futures
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from tarotgen.cards import DOCS_DIR

OUT_DIR = DOCS_DIR / "cards" / "samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gpt-image-2"
QUALITY = "medium"
SIZE = "1024x1792"

SCENE = (
    "A glowing terminal cursor hovering over git push --force on a main branch, "
    "floating code snippets ascending into a bright blue neon void, electric spark lines"
)

TAROT_NAME = "The Fool"
DEVOPS_NAME = "The Commit"

STYLES = {
    "A": {
        "label": "Flat Vector Tech",
        "front_prompt": (
            "{scene}. Modern flat vector illustration style, friendly cartoon characters, "
            "clean bold colors, playful tech startup aesthetic, minimalist geometric shapes, "
            "soft pastel gradients, cheerful office lighting, crisp clean linework, no shadows. "
            "Standard tarot card aspect ratio (1:1.75 vertical). Flat 2D straight-on centered view. "
            "Isolated on a solid black #000000 background, no text, no words, no letters."
        ),
        "back_prompt": (
            "Symmetrical tech mandala card back design. Modern flat vector illustration style, "
            "clean bold colors, minimalist geometric shapes, soft pastel gradients, "
            "glowing circuit patterns, fiber-optic infinity loop at center, playful startup aesthetic. "
            "Standard tarot card aspect ratio (1:1.75 vertical). Isolated on solid black #000000 background, "
            "no text, no words, no letters."
        ),
    },
    "B": {
        "label": "Retro Pixel Art",
        "front_prompt": (
            "{scene}. Retro 8-bit pixel art style, vibrant limited color palette, chunky pixels, "
            "nostalgic arcade game aesthetic, crisp pixel edges, bright saturated colors, "
            "charming low-resolution digital art. Standard tarot card aspect ratio (1:1.75 vertical). "
            "Flat 2D straight-on centered view. Isolated on a solid black #000000 background, "
            "no text, no words, no letters."
        ),
        "back_prompt": (
            "Symmetrical pixel mandala card back design. Retro 8-bit pixel art style, "
            "vibrant limited color palette, chunky pixels, nostalgic arcade aesthetic, "
            "glowing pixel circuit patterns, pixelated infinity loop at center. "
            "Standard tarot card aspect ratio (1:1.75 vertical). Isolated on solid black #000000 background, "
            "no text, no words, no letters."
        ),
    },
    "C": {
        "label": "Corporate Comic",
        "front_prompt": (
            "{scene}. Bold line art comic style, thick expressive outlines, bright flat cel-shaded colors, "
            "playful exaggerated cartoon characters, office humor energy, dynamic poses, "
            "clean cartoon shading, friendly techie vibe. Standard tarot card aspect ratio (1:1.75 vertical). "
            "Flat 2D straight-on centered view. Isolated on a solid black #000000 background, "
            "no text, no words, no letters."
        ),
        "back_prompt": (
            "Symmetrical comic mandala card back design. Bold line art comic style, thick expressive outlines, "
            "bright flat cel-shaded colors, glowing neon circuit patterns, dynamic energy lines, "
            "stylized infinity loop at center. Standard tarot card aspect ratio (1:1.75 vertical). "
            "Isolated on solid black #000000 background, no text, no words, no letters."
        ),
    },
}


def generate_image(client: OpenAI, prompt: str, out_path: Path) -> bool:
    try:
        response = client.images.generate(
            model=MODEL,
            prompt=prompt,
            size=SIZE,
            quality=QUALITY,
            n=1,
        )
        img_bytes = base64.b64decode(response.data[0].b64_json)
        out_path.write_bytes(img_bytes)
        print(f"  -> Saved {out_path} ({out_path.stat().st_size // 1024} KB)")
        return True
    except Exception as e:
        print(f"  -> ERROR: {e}")
        return False


def worker_generate(job: dict) -> tuple:
    key, kind, prompt, out_path = job["key"], job["kind"], job["prompt"], job["out_path"]
    client = OpenAI()
    success = generate_image(client, prompt, out_path)
    return (key, kind, success)


def add_text_overlay(src_path: Path, dst_path: Path, tarot_name: str, devops_name: str) -> None:
    img = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # Try to load a clean font
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_title = None
    font_sub = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 42)
                font_sub = ImageFont.truetype(fp, 32)
                break
            except Exception:
                pass
    if font_title is None:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Top banner — tarot name
    top_text = tarot_name.upper()
    bbox = draw.textbbox((0, 0), top_text, font=font_title)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = 40

    # Dark semi-transparent banner behind top text
    banner_pad = 16
    banner_overlay = Image.new("RGBA", (tw + banner_pad * 2, th + banner_pad * 2), (0, 0, 0, 180))
    img.paste(banner_overlay, (tx - banner_pad, ty - banner_pad), banner_overlay)
    draw.text((tx, ty), top_text, font=font_title, fill=(0, 229, 255, 255))  # cyan

    # Bottom banner — devops name
    bot_text = devops_name.upper()
    bbox = draw.textbbox((0, 0), bot_text, font=font_sub)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = h - th - 50

    banner_overlay = Image.new("RGBA", (tw + banner_pad * 2, th + banner_pad * 2), (0, 0, 0, 180))
    img.paste(banner_overlay, (tx - banner_pad, ty - banner_pad), banner_overlay)
    draw.text((tx, ty), bot_text, font=font_sub, fill=(0, 255, 102, 255))  # green

    img.save(dst_path, "PNG")
    print(f"  -> Text overlay {dst_path}")


def main():
    print(f"\nGenerating 3 style samples (front + back each) = 6 images...\n")

    jobs = []
    for key, style in STYLES.items():
        front_prompt = style["front_prompt"].format(scene=SCENE)
        back_prompt = style["back_prompt"]

        front_raw = OUT_DIR / f"style-{key}-front-raw.png"
        back_raw = OUT_DIR / f"style-{key}-back-raw.png"
        front_final = OUT_DIR / f"style-{key}-front.png"
        back_final = OUT_DIR / f"style-{key}-back.png"

        jobs.append({"key": key, "kind": "front", "prompt": front_prompt, "out_path": front_raw})
        jobs.append({"key": key, "kind": "back", "prompt": back_prompt, "out_path": back_raw})

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(worker_generate, job): job for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            job = futures[future]
            try:
                key, kind, success = future.result()
                if not success:
                    print(f"[FAIL] Style {key} {kind}")
            except Exception as e:
                print(f"[ERROR] Style {job['key']} {job['kind']}: {e}")

    print("\nAdding text overlays...\n")
    for key in STYLES:
        front_raw = OUT_DIR / f"style-{key}-front-raw.png"
        back_raw = OUT_DIR / f"style-{key}-back-raw.png"
        front_final = OUT_DIR / f"style-{key}-front.png"
        back_final = OUT_DIR / f"style-{key}-back.png"

        if front_raw.exists():
            add_text_overlay(front_raw, front_final, TAROT_NAME, DEVOPS_NAME)
        if back_raw.exists():
            add_text_overlay(back_raw, back_final, "", "")  # Back gets no text overlay

    print("\nDone! Samples are in ./docs/cards/samples/")
    for key in STYLES:
        print(f"  Style {key} ({STYLES[key]['label']}):")
        print(f"    Front: {OUT_DIR / f'style-{key}-front.png'}")
        print(f"    Back:  {OUT_DIR / f'style-{key}-back.png'}")


if __name__ == "__main__":
    main()

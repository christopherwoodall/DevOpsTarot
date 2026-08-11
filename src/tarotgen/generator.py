#!/usr/bin/env python3
"""
Generate DevOps Tarot card images using OpenAI GPT-Image-2.

Produces 1024x1792 (1:1.75 vertical tarot ratio) images with black backgrounds,
then post-processes to make near-black pixels transparent for PNG compositing.

Usage:
    uv run python -m tarotgen.generator --test          # generate one test card (new back + one front)
    uv run python -m tarotgen.generator --resume        # skip existing files
    uv run python -m tarotgen.generator                 # full batch (asks for confirmation)

Cost estimate (gpt-image-2 medium, 1024x1792): ~$0.05 per image (conservative).
78 cards + 1 back = ~$3.95.
"""

import os
import sys
import time
import json
import yaml
import argparse
import base64
import concurrent.futures
from pathlib import Path

from PIL import Image
from openai import OpenAI

from tarotgen.cards import (
    DOCS_CARDS_DIR,
    CARDS_YML,
    MEANINGS_JSON,
    load_cards,
    load_meanings,
    id_to_tarot_name,
)

COST_PER_IMAGE = 0.05  # Conservative estimate for gpt-image-2 medium 1024x1792
DALL_E_SIZE = "1024x1792"
DALL_E_MODEL = "gpt-image-2"
DALL_E_QUALITY = "medium"
MAX_WORKERS = 4

# Transparency threshold: pixels with max(R,G,B) below this become fully transparent
TRANSPARENCY_THRESHOLD = 18

CARD_FRONT_TEMPLATE = (
    "DevOps Corporate Comic Tarot Card. {scene}. "
    "Bold line art comic style, thick expressive outlines, bright flat cel-shaded colors, "
    "playful exaggerated cartoon characters, office humor energy, dynamic poses, "
    "clean cartoon shading, friendly techie vibe. "
    "Standard tarot card aspect ratio (1:1.75 vertical). "
    "Flat 2D straight-on centered view, zero perspective angle, zero drop shadow. "
    "The entire card must be isolated on a solid black #000000 background for easy transparent PNG background removal. "
    "The card frame itself must have rounded corners, a thick gold comic border with decorative corner accents, and uniform padding on all sides. "
    "At the top center, add the classic tarot name '{tarot_name}' in bold uppercase comic lettering with a gold outline. "
    "At the bottom center, add the DevOps title '{devops_name}' in bold uppercase comic lettering with a cyan outline. "
    "Both text labels must be centered, flat 2D, integrated into the card frame, no text outside the card."
)

CARD_BACK_PROMPT = (
    "DevOps Corporate Comic tarot card back design. "
    "Bold line art comic style, thick expressive outlines, bright flat cel-shaded colors, "
    "A deep multi-layered sacred geometry mandala floating in a dark void. "
    "At the center, a glowing fiber-optic infinity loop intertwined with an encrypted holographic server core pulsing with cyan light. "
    "Radiating outward: concentric rings of fine circuit board traces, occult runes made of binary code, and hexagonal data-cell lattices. "
    "Subtle holographic purple and deep blue accent shadows behind the main gold and cyan linework. "
    "Scattered micro-constellations of tiny glowing nodes connected by whisper-thin data streams. "
    "The entire composition feels alive, breathing with subtle energy pulses. "
    "Thick outer rounded-corner frame with a thick gold comic border and decorative corner accents. "
    "Standard tarot card aspect ratio (1:1.75 vertical). "
    "Isolated on a solid black #000000 background for transparent keying, flat 2D straight-on front view, no drop shadow, no text, no words, no letters."
)


def ensure_dirs():
    DOCS_CARDS_DIR.mkdir(parents=True, exist_ok=True)


def remove_black_background(src_path: Path, dst_path: Path) -> None:
    """Replace near-black pixels with transparent alpha."""
    img = Image.open(src_path).convert("RGBA")
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            max_val = max(r, g, b)
            if max_val < TRANSPARENCY_THRESHOLD:
                # Fully transparent
                pixels[x, y] = (0, 0, 0, 0)
            else:
                # Keep original color with full alpha
                pixels[x, y] = (r, g, b, 255)

    img.save(dst_path, "PNG")


def generate_image(client: OpenAI, prompt: str, out_path: Path) -> bool:
    """Generate a single image via GPT-Image-2 and save to disk."""
    try:
        response = client.images.generate(
            model=DALL_E_MODEL,
            prompt=prompt,
            size=DALL_E_SIZE,
            quality=DALL_E_QUALITY,
            n=1,
        )
        image_data = response.data[0]

        if image_data.b64_json:
            img_bytes = base64.b64decode(image_data.b64_json)
            temp_path = out_path.with_suffix(".raw.png")
            temp_path.write_bytes(img_bytes)
        elif image_data.url:
            import requests
            r = requests.get(image_data.url, timeout=120)
            r.raise_for_status()
            temp_path = out_path.with_suffix(".raw.png")
            temp_path.write_bytes(r.content)
        else:
            raise RuntimeError("No image data returned (no url or b64_json)")

        # Post-process: remove black background
        remove_black_background(temp_path, out_path)
        temp_path.unlink(missing_ok=True)

        print(f"  -> Saved {out_path} ({out_path.stat().st_size // 1024} KB)")
        return True

    except Exception as e:
        print(f"  -> ERROR: {e}")
        return False


def generate_card_back(client: OpenAI, resume: bool) -> bool:
    out_path = DOCS_CARDS_DIR / "card-back.png"
    if resume and out_path.exists():
        print(f"[SKIP] Card back already exists: {out_path}")
        return True
    print("[GENERATE] Card Back")
    return generate_image(client, CARD_BACK_PROMPT, out_path)


def generate_card_front(client: OpenAI, card: dict, meanings: dict, resume: bool, regenerate: bool = False) -> bool:
    cid = card["id"]
    out_path = DOCS_CARDS_DIR / f"{cid}.png"
    if resume and not regenerate and out_path.exists():
        return True

    info = meanings.get(cid, {})
    devops_name = info.get("name", cid.replace("-", " ").title())
    tarot_name = id_to_tarot_name(cid)
    scene = card.get("scene", "").strip().rstrip(". ")

    if not scene:
        print(f"[SKIP] {cid} has no scene description")
        return False

    prompt = CARD_FRONT_TEMPLATE.format(scene=scene, tarot_name=tarot_name, devops_name=devops_name)
    print(f"[GENERATE] {cid} — {devops_name} ({tarot_name})")
    return generate_image(client, prompt, out_path)


def worker_generate(card: dict, meanings: dict, resume: bool, regenerate: bool) -> tuple:
    """Thread worker: create a fresh OpenAI client and generate one card."""
    client = OpenAI()
    cid = card["id"]
    out_path = DOCS_CARDS_DIR / f"{cid}.png"

    if resume and not regenerate and out_path.exists():
        return (cid, "skipped")

    success = generate_card_front(client, card, meanings, resume=False, regenerate=regenerate)
    return (cid, "ok" if success else "fail")


def main():
    parser = argparse.ArgumentParser(description="Generate DevOps Tarot cards via OpenAI GPT-Image-2")
    parser.add_argument("--test", action="store_true", help="Generate only the card back + one test front (The Commit)")
    parser.add_argument("--resume", action="store_true", help="Skip cards that already exist")
    parser.add_argument("--regenerate", action="store_true", help="Force regeneration of all cards, overwriting existing files")
    parser.add_argument("--card-id", type=str, default=None, help="Regenerate only a specific card by ID (e.g., 00-the-fool)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts and cost estimate without calling the API")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt and proceed immediately")
    args = parser.parse_args()

    ensure_dirs()
    cards = load_cards()
    meanings = load_meanings()

    total = len(cards) + 1  # +1 for card back
    estimated_cost = total * COST_PER_IMAGE

    print(f"""
{'='*54}
  DevOps Tarot — OpenAI GPT-Image-2 Generator
{'='*54}
  Cards to generate: {len(cards)}
  Card back: 1
  Total images: {total}
  Size: {DALL_E_SIZE}
  Quality: {DALL_E_QUALITY}
  Workers: {MAX_WORKERS}
  Est. cost: ${estimated_cost:.2f}
  Budget: ~$10.00
{'='*54}
""")

    if args.dry_run:
        print("[DRY RUN] Would generate the following prompts:\n")
        print(f"Card back:\n{CARD_BACK_PROMPT}\n")
        first_card = cards[0]
        first_info = meanings.get(first_card["id"], {})
        first_name = first_info.get("name", first_card["id"].replace("-", " ").title())
        first_tarot = id_to_tarot_name(first_card["id"])
        print(f"First card ({first_card['id']}):\n{CARD_FRONT_TEMPLATE.format(scene=first_card.get('scene',''), tarot_name=first_tarot, devops_name=first_name)}\n")
        print("Dry run complete. No API calls made.")
        return

    # Filter to a single card if --card-id is specified
    if args.card_id:
        cards = [c for c in cards if c["id"] == args.card_id]
        if not cards:
            print(f"[ERROR] Card ID '{args.card_id}' not found in cards.yml")
            sys.exit(1)
        print(f"[FILTER] Regenerating only {args.card_id}\n")
        args.regenerate = True

    # Pre-flight confirmation for full batch
    if not args.test and not args.card_id and not args.yes:
        answer = input("This will call the OpenAI API and spend money. Type YES to proceed: ")
        if answer.strip().lower() != "yes":
            print("Aborted. Rerun with --test to generate a single sample.")
            return

    client = OpenAI()
    success_count = 0
    fail_count = 0
    skipped_count = 0

    # Generate card back first (unless --card-id is used)
    if not args.card_id:
        if generate_card_back(client, args.resume and not args.regenerate):
            success_count += 1
        else:
            fail_count += 1

    if args.test:
        # Also generate one test front (The Commit / 00-the-fool)
        test_card = cards[0]
        print(f"\n[Test front: {test_card['id']}]")
        if generate_card_front(client, test_card, meanings, args.resume, args.regenerate):
            success_count += 1
        else:
            fail_count += 1

        print("\n[Test complete — card back + one front generated.]")
        print(f"  Review {DOCS_CARDS_DIR}/card-back.png and {DOCS_CARDS_DIR}/{test_card['id']}.png")
        print("  Rerun without --test (and with --resume) to generate the remaining cards.")
        return

    # Full batch with threading
    print(f"\nStarting threaded generation with {MAX_WORKERS} workers...\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_card = {
            executor.submit(worker_generate, card, meanings, args.resume, args.regenerate): card
            for card in cards
        }
        for future in concurrent.futures.as_completed(future_to_card):
            card = future_to_card[future]
            try:
                cid, status = future.result()
                if status == "ok":
                    success_count += 1
                elif status == "skipped":
                    skipped_count += 1
                    print(f"[SKIP] {cid} already exists")
                else:
                    fail_count += 1
                    print(f"[FAIL] {cid}")
            except Exception as e:
                fail_count += 1
                print(f"[ERROR] {card['id']}: {e}")

    print(f"""
{'='*54}
            Generation Complete
{'='*54}
  Successful: {success_count}
  Skipped:    {skipped_count}
  Failed:     {fail_count}
  Est. cost:  ${(success_count * COST_PER_IMAGE):.2f}
{'='*54}
""")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Enhance cards.yml scene descriptions with sharper DevOps terminology."""

import yaml
import time
from pathlib import Path
from openai import OpenAI

from tarotgen.cards import CARDS_YML as INPUT_PATH

SYSTEM_PROMPT = (
    "You are a DevOps tarot artist. Given a card's DevOps name and current scene description, "
    "enhance the scene with more vivid, specific technical imagery. Add concrete tools, technologies, "
    "and SRE practices (e.g., Kubernetes, Prometheus, Grafana, Terraform, PagerDuty, Datadog, "
    "feature flags, canary deploys, eBPF traces, Jaeger spans, Vault secrets, etc.) where they fit naturally. "
    "Keep the description to 1-2 sentences. Maintain the existing artistic/comic tone. "
    "Return ONLY the enhanced scene description text, nothing else."
)


def enhance_scene(client: OpenAI, card_id: str, devops_name: str, current_scene: str) -> str:
    user_prompt = (
        f"Card ID: {card_id}\n"
        f"DevOps Name: {devops_name}\n"
        f"Current Scene: {current_scene}\n\n"
        f"Enhance this scene description with more vivid, specific DevOps/SRE technical imagery. "
        f"Return only the enhanced description text."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] {card_id}: {e}")
        return current_scene


def main():
    client = OpenAI()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cards = data.get("cards", [])
    total = len(cards)
    print(f"Enhancing {total} card scenes via OpenAI...\n")

    for idx, card in enumerate(cards, 1):
        card_id = card["id"]
        devops_name = card.get("name", card_id)
        current_scene = card.get("scene", "")

        print(f"[{idx}/{total}] {card_id} ({devops_name})...", end=" ")
        enhanced = enhance_scene(client, card_id, devops_name, current_scene)
        card["scene"] = enhanced
        print("done")
        time.sleep(0.2)  # Rate limit buffer

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"\nEnhanced scenes saved to {INPUT_PATH}")


if __name__ == "__main__":
    main()

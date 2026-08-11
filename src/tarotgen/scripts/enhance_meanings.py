#!/usr/bin/env python3
"""Enhance meanings.json with deeper DevOps/SRE terminology using OpenAI."""

import json
import time
from pathlib import Path
from openai import OpenAI

from tarotgen.cards import MEANINGS_ORIGINAL_JSON as INPUT_PATH, MEANINGS_JSON as OUTPUT_PATH

SYSTEM_PROMPT = (
    "You are a DevOps/SRE tarot expert. Given a card's DevOps-themed name and its current upright/reversed meanings, "
    "enhance the descriptions with more specific, technical DevOps/SRE terminology while keeping the same poetic tarot style. "
    "Add references to concrete tools, practices, and concepts (e.g., canary deployments, circuit breakers, blameless post-mortems, "
    "FinOps, chaos engineering, golden signals, SLOs/SLIs, feature flags, blue-green deploys, infrastructure as code, PagerDuty, "
    "Datadog, Prometheus, Terraform, Ansible, Kubernetes RBAC, service mesh, eBPF, etc.) where they fit naturally. "
    "Keep each meaning to 1-2 sentences. Return ONLY a JSON object with 'upright' and 'reversed' keys."
)


def enhance_card(client: OpenAI, card_id: str, name: str, upright: str, reversed: str) -> dict:
    user_prompt = (
        f"Card ID: {card_id}\n"
        f"DevOps Name: {name}\n"
        f"Current Upright: {upright}\n"
        f"Current Reversed: {reversed}\n\n"
        f"Enhance these with deeper DevOps/SRE terminology. Return JSON: {{\"upright\": \"...\", \"reversed\": \"...\"}}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"  [ERROR] {card_id}: {e}")
        return {"upright": upright, "reversed": reversed}


def main():
    client = OpenAI()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    print(f"Enhancing {total} card meanings via OpenAI...\n")

    for idx, (card_id, info) in enumerate(data.items(), 1):
        name = info.get("name", card_id)
        upright = info.get("upright", "")
        reversed_meaning = info.get("reversed", "")

        print(f"[{idx}/{total}] {card_id} ({name})...", end=" ")
        enhanced = enhance_card(client, card_id, name, upright, reversed_meaning)
        info["upright"] = enhanced.get("upright", upright)
        info["reversed"] = enhanced.get("reversed", reversed_meaning)
        print("done")
        time.sleep(0.2)  # Rate limit buffer

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nEnhanced meanings saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

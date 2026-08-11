# DevOps Tarot - GitHub Pages Site

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

# DevOps Tarot - GitHub Pages Site

This directory contains the production-ready static site deployment for **DevOps Tarot**.

## Features
- **78 Custom DevOps Tarot Cards**: Major & Minor Arcana (Code, Logs, Bugs, Servers).
- **Single Card Draw & 3-Card Spread**: Past (Legacy), Present (Production), Future (Deployment).
- **Upright & Reversed Interpretations**: Highlighting both optimal practices and technical debt/outages.
- **Original / DevOps Toggle**: Switch between classic Rider-Waite tarot meanings and enhanced DevOps/SRE interpretations.
- **Corporate Comic Style**: Bold line art, thick expressive outlines, bright cel-shaded colors, and playful cartoon energy.
- **Terminal Aesthetic**: Matrix particle background, terminal audio synthesis, and interactive modals.

## Build Instructions
1. Generate card graphics (GPT-Image-2):
   ```bash
   python generate_openai.py
   ```
2. Build static HTML site:
   ```bash
   python build_site.py
   ```

Deploy to GitHub Pages by configuring repository settings to serve from the `/docs` folder!

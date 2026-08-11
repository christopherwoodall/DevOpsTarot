#!/usr/bin/env python3
"""Simple HTTP server for local testing of the DevOps Tarot site."""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

from tarotgen.cards import DOCS_DIR

PORT = 8000


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress default logging noise; print only meaningful requests
        pass


def main():
    os.chdir(DOCS_DIR.parent)
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n{'='*50}")
        print(f"  DevOps Tarot local server running at {url}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*50}\n")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")


if __name__ == "__main__":
    main()

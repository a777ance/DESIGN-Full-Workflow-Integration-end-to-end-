#!/usr/bin/env python3
"""One-command launcher for the A777ance Operator Console.

From the repo, run:

    python3 console/serve.py

It serves the console folder at http://localhost:<port>/ and opens your browser
there. Serving (rather than double-clicking the file) is what lets the app
install to your home screen and work offline. Leave this window open while you
use it; press Ctrl+C to stop. No dependencies — standard library only.
"""
import http.server
import os
import socket
import socketserver
import webbrowser

DIR = os.path.dirname(os.path.abspath(__file__))  # the console/ folder


def free_port(preferred=8000):
    """Return the preferred port if nothing is listening on it, else the next free one."""
    for port in [preferred] + list(range(8001, 8051)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:  # connect failed => port is free
                return port
    return preferred


class Handler(http.server.SimpleHTTPRequestHandler):
    # Serve the console folder no matter where the script is run from.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, *args):
        pass  # keep the terminal quiet


# Make sure the manifest is served with a type browsers accept (older Pythons).
Handler.extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map)
Handler.extensions_map[".webmanifest"] = "application/manifest+json"


def main():
    port = free_port(8000)
    url = "http://localhost:%d/" % port
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("")
        print("  A777ance — Operator Console")
        print("  " + "-" * 30)
        print("  Open in your browser:  " + url)
        print("  (trying to open it for you now...)")
        print("")
        print("  To install it as an app once the page is open:")
        print("    - iPhone/iPad (Safari):  Share -> Add to Home Screen")
        print("    - Android (Chrome):      menu -> Add to Home screen / Install")
        print("    - Mac/Windows (Chrome/Edge): Install icon in the address bar")
        print("")
        print("  Leave this window open while you use it. Press Ctrl+C to stop.")
        print("")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Stopped.\n")


if __name__ == "__main__":
    main()

"""
Web server for Smart Lock DFA application.

Provides local HTTP server to interactively simulate the DFA lock
and compare its behavior with a naive lock through index.html.

Usage:
  python app.py
  python app.py --port 8002
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Ensure local imports resolve correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import main


def parse_numeric_param(query, name, max_len=6):
    """Validates and extracts a numeric query parameter."""
    values = query.get(name, [""])
    value = values[0] if values else ""
    if not value.isdigit() or len(value) > max_len:
        raise ValueError(f"Parameter '{name}' must be 1 to {max_len} numeric digits.")
    return value


class SmartLockHandler(BaseHTTPRequestHandler):
    """HTTP request handler for DFA web interface."""

    def send_response_data(self, data, content_type="application/json; charset=utf-8", status=200):
        body = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        try:
            # Serve main dashboard HTML
            if parsed.path in ("/", "/index.html"):
                html_path = os.path.join(BASE_DIR, "index.html")
                with open(html_path, "rb") as f:
                    return self.send_response_data(f.read(), "text/html; charset=utf-8")

            # Return DFA transition table for a given passcode
            if parsed.path == "/dfa":
                code = parse_numeric_param(query, "code", max_len=6)
                table = main.build_dfa(code)
                return self.send_response_data({"code": code, "table": table})

            # Simulate key presses on both DFA and naive locks
            if parsed.path == "/run":
                code = parse_numeric_param(query, "code", max_len=6)
                keys_list = query.get("keys", [""])
                keys = keys_list[0] if keys_list else ""
                if keys and (not keys.isdigit() or len(keys) > 40):
                    raise ValueError("Parameter 'keys' must be up to 40 numeric digits.")

                table = main.build_dfa(code)
                dfa_path, dfa_open = main.run_dfa(table, code, keys)
                naive_path, naive_open = main.run_naive(code, keys)
                should_open = main.ends_with_code(code, keys)

                return self.send_response_data({
                    "dfa": dfa_path,
                    "dfa_open": dfa_open,
                    "lazy": naive_path,
                    "lazy_open": naive_open,
                    "should_open": should_open,
                })

            self.send_error(404, "Endpoint not found")

        except ValueError as err:
            self.send_response_data({"error": str(err)}, status=400)
        except Exception as err:
            self.send_response_data({"error": f"Internal error: {err}"}, status=500)

    def log_message(self, format_str, *args):
        # Clean terminal logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format_str % args}\n")


def start_server(host="127.0.0.1", port=8002):
    server_address = (host, port)
    httpd = HTTPServer(server_address, SmartLockHandler)
    print("=" * 64)
    print(" Smart Lock DFA: Web Dashboard Running")
    print(f" URL: http://{host}:{port}")
    print(" Press Ctrl+C in terminal to stop.")
    print("=" * 64)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Lock DFA Web Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8002, help="Port (default: 8002)")
    args = parser.parse_args()
    start_server(host=args.host, port=args.port)

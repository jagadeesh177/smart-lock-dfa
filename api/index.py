"""
Vercel Serverless Function entry point for Smart Lock DFA.

Handles HTTP requests on Vercel:
- /dfa: Computes and returns the DFA transition table for a given passcode.
- /run: Simulates key sequences through both DFA and naive locks.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure project root is in sys.path so main.py can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import main


def parse_numeric_param(query, name, max_len=6):
    """Validates and extracts a numeric query parameter."""
    values = query.get(name, [""])
    value = values[0] if values else ""
    if not value.isdigit() or len(value) > max_len:
        raise ValueError(f"Parameter '{name}' must be 1 to {max_len} numeric digits.")
    return value


class handler(BaseHTTPRequestHandler):
    """Vercel serverless request handler."""

    def send_response_data(self, data, content_type="application/json; charset=utf-8", status=200):
        body = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        endpoint = query.get("endpoint", [""])[0]
        path = parsed.path.rstrip("/")

        try:
            # DFA transition table endpoint
            if endpoint == "dfa" or path.endswith("/dfa"):
                code = parse_numeric_param(query, "code", max_len=6)
                table = main.build_dfa(code)
                return self.send_response_data({"code": code, "table": table})

            # Lock execution/simulation endpoint
            if endpoint == "run" or path.endswith("/run"):
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

            # Root path fallback
            if path in ("", "/", "/index", "/index.html", "/api"):
                html_path = os.path.join(ROOT_DIR, "index.html")
                if os.path.exists(html_path):
                    with open(html_path, "rb") as f:
                        return self.send_response_data(f.read(), "text/html; charset=utf-8")

            self.send_error(404, "Endpoint not found")

        except ValueError as err:
            self.send_response_data({"error": str(err)}, status=400)
        except Exception as err:
            self.send_response_data({"error": f"Internal error: {err}"}, status=500)

    def log_message(self, format_str, *args):
        # Keep serverless logs concise
        sys.stderr.write(f"[{self.log_date_time_string()}] {format_str % args}\n")

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent
STATE_FILE = MCP_DIR.parent / ".workflow" / "state.json"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            html = (MCP_DIR / "index.html").read_text(encoding="utf-8")
            self.send(200, "text/html; charset=utf-8", html)
        elif self.path == "/state":
            if STATE_FILE.exists():
                state = STATE_FILE.read_text(encoding="utf-8")
            else:
                state = json.dumps({"agents": {}, "events": []})
            self.send(200, "application/json; charset=utf-8", state)
        else:
            self.send(404, "text/plain", "Not found")

    def do_POST(self):
        if self.path == "/reset":
            STATE_FILE.parent.mkdir(exist_ok=True)
            STATE_FILE.write_text(json.dumps({"agents": {}, "events": []}), encoding="utf-8")
            self.send(200, "application/json", '{"ok": true}')
        else:
            self.send(404, "text/plain", "Not found")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Dashboard: http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
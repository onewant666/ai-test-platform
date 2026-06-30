"""ZenTao Mock API — 模拟禅道 REST API v1 用于测试集成流程"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKENS = {}
PRODUCTS = [{"id": 1, "name": "测试产品"}]
TESTCASES = []
BUGS = []
NEXT_ID = 1


class ZentaoMockHandler(BaseHTTPRequestHandler):
    def _send(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_POST(self):
        body = self._read_body()
        if self.path == "/api.php/v1/tokens":
            token = f"mock-token-{abs(hash(str(body)))}"
            TOKENS[token] = body
            self._send({"token": token, "status": "success"})
        elif self.path.startswith("/api.php/v1/testcases") and "/results" not in self.path:
            global NEXT_ID
            tc = {"id": NEXT_ID, **body}
            NEXT_ID += 1
            TESTCASES.append(tc)
            self._send(tc, 201)
        elif "/results" in self.path:
            self._send({"status": "ok", "result": body.get("result", "pass")})
        elif "/bugs" in self.path:
            bug = {"id": len(BUGS) + 1, **body}
            BUGS.append(bug)
            self._send(bug, 201)
        else:
            self._send({"error": "not found"}, 404)

    def do_GET(self):
        if "/products" in self.path and "/bugs" not in self.path:
            self._send({"products": PRODUCTS})
        elif "/testcases" in self.path:
            self._send({"testcases": TESTCASES})
        elif "/projects" in self.path:
            self._send({"projects": [{"id": 1, "name": "测试项目"}]})
        elif "/bugs" in self.path:
            self._send({"bugs": BUGS})
        else:
            self._send({"error": "not found"}, 404)

    def do_PUT(self):
        body = self._read_body()
        self._send(body)

    def log_message(self, format, *args):
        print(f"[ZenTao Mock] {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8999), ZentaoMockHandler)
    print("ZenTao Mock API running on http://127.0.0.1:8999")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

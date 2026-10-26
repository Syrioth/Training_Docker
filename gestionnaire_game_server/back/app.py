import os
import sys
import json
import time
import signal
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8081"))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "backend-orchestrator-api")
GAME_SERVER_URL = os.environ.get("GAME_SERVER_URL", "http://game-server:8082")

START_TIME = time.time()
print(f"[{SERVICE_NAME}] Initialisation sur le port {PORT} (PID: {os.getpid()})...", flush=True)

class BackendRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def _call_game_server(self, endpoint, method="GET", payload=None):
        url = f"{GAME_SERVER_URL}{endpoint}"
        try:
            req_data = json.dumps(payload).encode('utf-8') if payload is not None else None
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"} if req_data else {}
            )
            req.method = method
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                content = resp.read().decode('utf-8')
                return json.loads(content), 200
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode('utf-8'))
                return err_data, e.code
            except Exception:
                return {"error": f"Erreur HTTP {e.code}"}, e.code
        except Exception as e:
            return {"error": f"Connexion impossible vers game-server: {str(e)}"}, 503

    def do_GET(self):
        path = self.path
        if path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": SERVICE_NAME,
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "pid": os.getpid()
            })
        elif path in ["/admin/status", "/api/admin/status", "/"]:
            game_data, game_code = self._call_game_server("/health")
            self._send_json(200, {
                "service": SERVICE_NAME,
                "role": "Orchestrateur & API Gateway",
                "status": "operational",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "game_server_status": "healthy" if game_code == 200 else "unreachable",
                "pid": os.getpid()
            })
        elif path in ["/admin/games", "/api/admin/games"]:
            data, code = self._call_game_server("/api/admin/games")
            self._send_json(code, data)
        else:
            self._send_json(404, {"error": f"Endpoint introuvable : {path}"})

    def do_POST(self):
        path = self.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path in ["/admin/action", "/api/admin/action"]:
            data, code = self._call_game_server("/api/admin/action", method="POST", payload=payload)
            self._send_json(code, data)
        else:
            self._send_json(404, {"error": f"Endpoint POST introuvable : {path}"})

    def log_message(self, format, *args):
        print(f"[{SERVICE_NAME}] {args[0]} - {args[1]}", flush=True)

httpd = HTTPServer(("0.0.0.0", PORT), BackendRequestHandler)

def shutdown_handler(signum, frame):
    print(f"\n[{SERVICE_NAME}] >>> Signal SIGTERM recu (code {signum}) ! Arret gracieux...", flush=True)
    httpd.server_close()
    print(f"[{SERVICE_NAME}] Passerelle API arretee proprement. Code de sortie : 0.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    httpd.serve_forever()
except Exception as e:
    print(f"[{SERVICE_NAME}] Erreur : {e}", flush=True)

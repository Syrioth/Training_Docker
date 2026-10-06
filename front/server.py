import os
import sys
import json
import time
import signal
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8080"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://back:8081")
APP_TITLE = os.environ.get("APP_TITLE", "Docker Cloud Dashboard M1")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
START_TIME = time.time()

print(f"==================================================", flush=True)
print(f"[FRONTEND-UI] Demarrage du Front-End : {APP_TITLE}", flush=True)
print(f"[FRONTEND-UI] Port d'ecoute : {PORT}", flush=True)
print(f"[FRONTEND-UI] URL Backend cible : {BACKEND_URL}", flush=True)
print(f"[FRONTEND-UI] Repertoire statique : {STATIC_DIR}", flush=True)
print(f"[FRONTEND-UI] PID en cours : {os.getpid()}", flush=True)
print(f"==================================================", flush=True)

class FrontRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, status_code, data):
        response_body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "front-dashboard",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "backend_url": BACKEND_URL,
                "pid": os.getpid()
            })
        elif self.path == "/api/proxy/cloud-status":
            try:
                with urllib.request.urlopen(f"{BACKEND_URL}/api/cloud-status", timeout=2.5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    self._send_json(200, data)
            except Exception as e:
                self._send_json(502, {"error": "Backend injoignable", "details": str(e)})
        elif self.path == "/api/proxy/game-status":
            try:
                with urllib.request.urlopen(f"{BACKEND_URL}/api/game-summary", timeout=2.5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    self._send_json(200, data)
            except Exception as e:
                self._send_json(502, {"error": "Backend ou game-server injoignable", "details": str(e)})
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"

        # Proxy dynamique des requetes de jeu vers le back
        if self.path.startswith("/api/proxy/game-"):
            game_endpoint = self.path.replace("/api/proxy/game-", "/api/game/")
            # Exemple : /api/proxy/game-start -> /api/game/start
            try:
                req = urllib.request.Request(
                    f"{BACKEND_URL}{game_endpoint}",
                    data=body.encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    self._send_json(resp.status, data)
            except urllib.error.HTTPError as e:
                try:
                    err_data = json.loads(e.read().decode('utf-8'))
                    self._send_json(e.code, err_data)
                except Exception:
                    self._send_json(e.code, {"error": f"Erreur HTTP {e.code}"})
            except Exception as e:
                self._send_json(502, {"error": "Erreur relai proxy", "details": str(e)})
        else:
            self._send_json(404, {"error": "Endpoint non trouve"})

    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [FRONTEND-UI] {args[0]} - {args[1]}", flush=True)

class ThreadedHTTPServer(HTTPServer):
    pass

httpd = ThreadedHTTPServer(("0.0.0.0", PORT), FrontRequestHandler)

def shutdown_handler(signum, frame):
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[FRONTEND-UI] >>> SIGNAL {sig_name} RECU (Signal code: {signum}) <<<", flush=True)
    
    def do_shutdown():
        httpd.shutdown()
        httpd.server_close()
        print(f"[FRONTEND-UI] Arret gracieux termine avec succes. Code sortie : 0", flush=True)
        sys.exit(0)

    threading.Thread(target=do_shutdown).start()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    print(f"[FRONTEND-UI] Interface Web prete sur le port {PORT}.", flush=True)
    httpd.serve_forever()
except Exception as e:
    print(f"[FRONTEND-UI] Erreur : {e}", flush=True)

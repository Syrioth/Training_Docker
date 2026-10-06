import os
import sys
import json
import time
import signal
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8081"))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "backend-core-api")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
GAME_SERVER_URL = os.environ.get("GAME_SERVER_URL", "http://game-server:8082")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

START_TIME = time.time()

print(f"==================================================", flush=True)
print(f"[BACKEND-API] Initialisation de {SERVICE_NAME}", flush=True)
print(f"[BACKEND-API] Environnement : {ENVIRONMENT}", flush=True)
print(f"[BACKEND-API] Port d'ecoute : {PORT}", flush=True)
print(f"[BACKEND-API] URL Serveur de jeu : {GAME_SERVER_URL}", flush=True)
print(f"[BACKEND-API] PID en cours : {os.getpid()}", flush=True)
print(f"==================================================", flush=True)

class BackendRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        response_body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def _forward_to_game(self, endpoint, method="GET", payload=None):
        url = f"{GAME_SERVER_URL}{endpoint}"
        try:
            req_data = json.dumps(payload).encode('utf-8') if payload is not None else None
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"} if req_data else {}
            )
            req.method = method
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                content = resp.read().decode('utf-8')
                return json.loads(content), 200
        except urllib.error.URLError as e:
            return {"error": f"Connexion impossible vers game-server: {str(e)}"}, 503
        except Exception as e:
            return {"error": f"Erreur inattendue: {str(e)}"}, 500

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": SERVICE_NAME,
                "environment": ENVIRONMENT,
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "game_server_configured": GAME_SERVER_URL,
                "pid": os.getpid()
            })
        elif self.path == "/api/info" or self.path == "/":
            self._send_json(200, {
                "service": SERVICE_NAME,
                "role": "Orchestrateur & Passerelle API",
                "status": "operational",
                "environment": ENVIRONMENT,
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "pid": os.getpid()
            })
        elif self.path == "/api/game-summary":
            data, code = self._forward_to_game("/api/game/status")
            self._send_json(code, {
                "backend_timestamp": time.time(),
                "game_server_connected": (code == 200),
                "game_data": data
            })
        elif self.path == "/api/cloud-status":
            game_data, game_code = self._forward_to_game("/health")
            self._send_json(200, {
                "cloud_cluster": "Docker-Cloud-Cluster-M1",
                "backend_status": "healthy",
                "game_server_status": "healthy" if game_code == 200 else "unreachable",
                "cluster_time": time.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            self._send_json(404, {"error": "Endpoint introuvable", "path": self.path})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path.startswith("/api/game/"):
            # Relayage direct au game server
            endpoint = self.path
            res, code = self._forward_to_game(endpoint, method="POST", payload=payload)
            self._send_json(code, res)
        elif self.path == "/api/action":
            # Retro-compatibilite
            res, code = self._forward_to_game("/api/game/miner", method="POST", payload=payload)
            self._send_json(code, res)
        else:
            self._send_json(404, {"error": "Endpoint POST introuvable"})

    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [BACKEND-API] {args[0]} - {args[1]}", flush=True)

class ThreadedHTTPServer(HTTPServer):
    pass

httpd = ThreadedHTTPServer(("0.0.0.0", PORT), BackendRequestHandler)

def shutdown_handler(signum, frame):
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[BACKEND-API] >>> SIGNAL {sig_name} RECU (Signal code: {signum}) <<<", flush=True)
    
    def do_shutdown():
        httpd.shutdown()
        httpd.server_close()
        print(f"[BACKEND-API] Arret gracieux termine avec succes. Code sortie : 0", flush=True)
        sys.exit(0)

    threading.Thread(target=do_shutdown).start()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    print(f"[BACKEND-API] Serveur pret sur le port {PORT}.", flush=True)
    httpd.serve_forever()
except Exception as e:
    print(f"[BACKEND-API] Erreur : {e}", flush=True)

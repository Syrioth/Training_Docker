import os
import sys
import json
import signal
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8081"))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "backend-core-api")
GAME_SERVER_URL = os.environ.get("GAME_SERVER_URL", "http://game-server:8082")

print(f"[{SERVICE_NAME}] Démarrage sur le port {PORT} (PID: {os.getpid()})...", flush=True)

class BackendRequestHandler(BaseHTTPRequestHandler):
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
                "service": SERVICE_NAME,
                "pid": os.getpid()
            })
        else:
            # Récupération du Hello World auprès du serveur web de jeu
            game_msg = "Injoignable"
            try:
                with urllib.request.urlopen(f"{GAME_SERVER_URL}/", timeout=3.0) as resp:
                    game_data = json.loads(resp.read().decode('utf-8'))
                    game_msg = game_data.get("message", "OK")
            except Exception as e:
                game_msg = f"Erreur connexion game-server: {str(e)}"

            self._send_json(200, {
                "message": "Hello World from Back-End API!",
                "service": SERVICE_NAME,
                "game_server_response": game_msg,
                "pid": os.getpid()
            })

    def log_message(self, format, *args):
        print(f"[{SERVICE_NAME}] {args[0]} - {args[1]}", flush=True)

httpd = HTTPServer(("0.0.0.0", PORT), BackendRequestHandler)

def shutdown_handler(signum, frame):
    print(f"\n[{SERVICE_NAME}] >>> Signal SIGTERM reçu (code {signum}) ! Arrêt gracieux...", flush=True)
    httpd.server_close()
    print(f"[{SERVICE_NAME}] Serveur arrêté proprement. Code de sortie : 0.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    httpd.serve_forever()
except Exception as e:
    print(f"[{SERVICE_NAME}] Erreur : {e}", flush=True)

import os
import sys
import json
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler

# Variables d'environnement (arguments au run)
PORT = int(os.environ.get("PORT", "8082"))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "game-web-server")

print(f"[{SERVICE_NAME}] Démarrage sur le port {PORT} (PID: {os.getpid()})...", flush=True)

class GameRequestHandler(BaseHTTPRequestHandler):
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
            # Healthcheck Docker
            self._send_json(200, {
                "status": "healthy",
                "service": SERVICE_NAME,
                "pid": os.getpid()
            })
        else:
            # Réponse Hello World du serveur web de jeu
            self._send_json(200, {
                "message": "Hello World from Game Web Server!",
                "service": SERVICE_NAME,
                "status": "running",
                "pid": os.getpid()
            })

    def log_message(self, format, *args):
        print(f"[{SERVICE_NAME}] {args[0]} - {args[1]}", flush=True)

httpd = HTTPServer(("0.0.0.0", PORT), GameRequestHandler)

def shutdown_handler(signum, frame):
    """Gestionnaire propre de SIGTERM / SIGINT pour arrêt gracieux (PID 1)"""
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

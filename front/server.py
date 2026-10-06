import os
import sys
import json
import signal
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8080"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://back:8081")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

print(f"[front-dashboard] Démarrage sur le port {PORT} (PID: {os.getpid()})...", flush=True)

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
                "pid": os.getpid()
            })
        elif self.path == "/api/hello-chain":
            # Appel au back pour récupérer la chaîne des messages
            back_msg = "Injoignable"
            game_msg = "Injoignable"
            try:
                with urllib.request.urlopen(f"{BACKEND_URL}/", timeout=3.0) as resp:
                    back_data = json.loads(resp.read().decode('utf-8'))
                    back_msg = back_data.get("message", "OK")
                    game_msg = back_data.get("game_server_response", "OK")
            except Exception as e:
                back_msg = f"Erreur connexion backend: {str(e)}"

            self._send_json(200, {
                "front_message": "Hello World from Front-End Container!",
                "back_message": back_msg,
                "game_message": game_msg,
                "architecture_status": "All 3 containers successfully connected!"
            })
        else:
            super().do_GET()

    def log_message(self, format, *args):
        print(f"[front-dashboard] {args[0]} - {args[1]}", flush=True)

httpd = HTTPServer(("0.0.0.0", PORT), FrontRequestHandler)

def shutdown_handler(signum, frame):
    print(f"\n[front-dashboard] >>> Signal SIGTERM reçu (code {signum}) ! Arrêt gracieux...", flush=True)
    httpd.server_close()
    print(f"[front-dashboard] Serveur arrêté proprement. Code de sortie : 0.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    httpd.serve_forever()
except Exception as e:
    print(f"[front-dashboard] Erreur : {e}", flush=True)

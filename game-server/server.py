import os
import sys
import json
import time
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8082"))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "game-server-engine")

# Etat en memoire des instances de jeux multi-sessions
GAME_INSTANCES = {
    "game-session-01": {
        "title": "PixelQuest",
        "genre": "RPG / Aventure",
        "status": "Running",
        "tick_rate": 60,
        "max_players": 16,
        "active_players": ["Joueur_Alpha", "Joueur_Beta"],
        "scores": {"Joueur_Alpha": 320, "Joueur_Beta": 180}
    },
    "game-session-02": {
        "title": "CyberArena",
        "genre": "Combat / Arcade",
        "status": "Running",
        "tick_rate": 128,
        "max_players": 8,
        "active_players": ["Neo_99"],
        "scores": {"Neo_99": 450}
    }
}

START_TIME = time.time()
print(f"[{SERVICE_NAME}] Demarrage du moteur de jeux sur le port {PORT} (PID: {os.getpid()})...", flush=True)

class GameRequestHandler(BaseHTTPRequestHandler):
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

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": SERVICE_NAME,
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "pid": os.getpid()
            })
        elif self.path == "/api/admin/games" or self.path == "/":
            self._send_json(200, {
                "service": SERVICE_NAME,
                "status": "operational",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "total_sessions": len(GAME_INSTANCES),
                "instances": GAME_INSTANCES,
                "pid": os.getpid()
            })
        else:
            self._send_json(404, {"error": "Endpoint introuvable"})

    def do_POST(self):
        if self.path == "/api/admin/action":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            session_id = payload.get("session_id", "game-session-01")
            player = payload.get("player", "Nouveau_Joueur")
            points = int(payload.get("points", 50))

            if session_id in GAME_INSTANCES:
                inst = GAME_INSTANCES[session_id]
                if player not in inst["active_players"]:
                    inst["active_players"].append(player)
                inst["scores"][player] = inst["scores"].get(player, 0) + points

                self._send_json(200, {
                    "message": f"Action d'administration validee pour {session_id}",
                    "session": inst
                })
            else:
                self._send_json(404, {"error": "Session introuvable"})
        else:
            self._send_json(404, {"error": "Endpoint POST introuvable"})

    def log_message(self, format, *args):
        print(f"[{SERVICE_NAME}] {args[0]} - {args[1]}", flush=True)

httpd = HTTPServer(("0.0.0.0", PORT), GameRequestHandler)

def shutdown_handler(signum, frame):
    print(f"\n[{SERVICE_NAME}] >>> Signal SIGTERM recu (code {signum}) ! Arret gracieux...", flush=True)
    print(f"[{SERVICE_NAME}] Sauvegarde de l'etat des sessions de jeu en memoire : {list(GAME_INSTANCES.keys())}", flush=True)
    httpd.server_close()
    print(f"[{SERVICE_NAME}] Serveur arrete proprement. Code de sortie : 0.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    httpd.serve_forever()
except Exception as e:
    print(f"[{SERVICE_NAME}] Erreur : {e}", flush=True)

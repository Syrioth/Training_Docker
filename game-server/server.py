import os
import sys
import json
import time
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Lecture des variables d'environnement (arguments au run)
PORT = int(os.environ.get("PORT", "8082"))
GAME_NAME = os.environ.get("GAME_NAME", "PixelQuest")
MAX_PLAYERS = int(os.environ.get("MAX_PLAYERS", "16"))
DIFFICULTY = os.environ.get("DIFFICULTY", "medium")

START_TIME = time.time()
ACTIVE_PLAYERS = 3
SCORES = {"player_1": 150, "player_2": 240, "player_3": 95}
SERVER_RUNNING = True

print(f"==================================================", flush=True)
print(f"[GAME-SERVER] Demarrage du serveur de jeu : {GAME_NAME}", flush=True)
print(f"[GAME-SERVER] Port d'ecoute : {PORT}", flush=True)
print(f"[GAME-SERVER] Capacite max : {MAX_PLAYERS} joueurs", flush=True)
print(f"[GAME-SERVER] Difficulte : {DIFFICULTY}", flush=True)
print(f"[GAME-SERVER] PID en cours : {os.getpid()}", flush=True)
print(f"==================================================", flush=True)

class GameRequestHandler(BaseHTTPRequestHandler):
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

    def do_GET(self):
        if self.path == "/health":
            # Verification de l'etat de sante du container
            self._send_json(200, {
                "status": "healthy",
                "service": "game-server",
                "game": GAME_NAME,
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "pid": os.getpid()
            })
        elif self.path == "/api/game/status" or self.path == "/":
            self._send_json(200, {
                "service": "game-server",
                "game_name": GAME_NAME,
                "status": "running",
                "difficulty": DIFFICULTY,
                "active_players": ACTIVE_PLAYERS,
                "max_players": MAX_PLAYERS,
                "scores": SCORES,
                "uptime_seconds": round(time.time() - START_TIME, 2)
            })
        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def do_POST(self):
        global ACTIVE_PLAYERS, SCORES
        if self.path == "/api/game/action":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}
            
            player = payload.get("player", f"player_{ACTIVE_PLAYERS + 1}")
            points = payload.get("points", 10)
            
            SCORES[player] = SCORES.get(player, 0) + points
            self._send_json(200, {
                "message": f"Action enregistree pour {player}",
                "new_score": SCORES[player],
                "all_scores": SCORES
            })
        else:
            self._send_json(404, {"error": "Endpoint POST introuvable"})

    def log_message(self, format, *args):
        # Format propre de logs avec timestamp
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [GAME-SERVER] {args[0]} - {args[1]}", flush=True)

class ThreadedHTTPServer(HTTPServer):
    pass

httpd = ThreadedHTTPServer(("0.0.0.0", PORT), GameRequestHandler)

def shutdown_handler(signum, frame):
    """
    Gestionnaire pour les signaux SIGTERM et SIGINT.
    Permet un arret gracieux (graceful shutdown) du conteneur Docker.
    """
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[GAME-SERVER] >>> SIGNAL {sig_name} RECU (Signal code: {signum}) <<<", flush=True)
    print(f"[GAME-SERVER] Fermeture propre des sessions de jeu en cours...", flush=True)
    print(f"[GAME-SERVER] Sauvegarde de l'etat des joueurs : {SCORES}", flush=True)
    print(f"[GAME-SERVER] Arret du serveur HTTP en cours...", flush=True)
    
    # Arret du serveur HTTP dans un thread separe pour ne pas bloquer le handler
    def do_shutdown():
        httpd.shutdown()
        httpd.server_close()
        print(f"[GAME-SERVER] Serveur HTTP arrete proprement. Code de sortie : 0.", flush=True)
        sys.exit(0)

    threading.Thread(target=do_shutdown).start()

# Enregistrement des signaux pour Docker
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    print(f"[GAME-SERVER] Serveur pret a recevoir des connexions sur le port {PORT}.", flush=True)
    httpd.serve_forever()
except Exception as e:
    print(f"[GAME-SERVER] Erreur lors de l'execution : {e}", flush=True)
finally:
    print(f"[GAME-SERVER] Fin de l'execution du processus.", flush=True)

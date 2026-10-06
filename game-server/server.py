import os
import sys
import json
import time
import random
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Variables d'environnement / Arguments de run
PORT = int(os.environ.get("PORT", "8082"))
GAME_NAME = os.environ.get("GAME_NAME", "PixelQuest_Cloud_M1")
MAX_PLAYERS = int(os.environ.get("MAX_PLAYERS", "32"))
DIFFICULTY = os.environ.get("DIFFICULTY", "medium")

START_TIME = time.time()

# Etat du jeu en memoire du serveur
GAMES_STATE = {
    "sessions": {},
    "leaderboard": [
        {"player": "CyberNeo", "score": 450, "games_won": 3},
        {"player": "DockerMaster", "score": 380, "games_won": 2},
        {"player": "CloudAdmin", "score": 210, "games_won": 1}
    ],
    "global_stats": {
        "total_actions": 0,
        "cores_hacked": 0,
        "bugs_eliminated": 0
    }
}

DIFFICULTY_CONFIG = {
    "easy": {"range_max": 50, "max_tries": 10, "multiplier": 1.0},
    "medium": {"range_max": 100, "max_tries": 7, "multiplier": 1.5},
    "hard": {"range_max": 200, "max_tries": 5, "multiplier": 2.0}
}

print(f"==================================================", flush=True)
print(f"[GAME-SERVER] Demarrage du moteur de jeu : {GAME_NAME}", flush=True)
print(f"[GAME-SERVER] Port d'ecoute : {PORT}", flush=True)
print(f"[GAME-SERVER] Mode difficulte : {DIFFICULTY}", flush=True)
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
                "difficulty": DIFFICULTY,
                "active_sessions": len(GAMES_STATE["sessions"]),
                "leaderboard": GAMES_STATE["leaderboard"],
                "global_stats": GAMES_STATE["global_stats"],
                "uptime_seconds": round(time.time() - START_TIME, 2)
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

        # 1. Demarrer une nouvelle session de jeu
        if self.path == "/api/game/start":
            player = payload.get("player", "Joueur_Anonyme").strip() or "Joueur_Anonyme"
            diff = payload.get("difficulty", DIFFICULTY)
            if diff not in DIFFICULTY_CONFIG:
                diff = "medium"
            cfg = DIFFICULTY_CONFIG[diff]

            secret_code = random.randint(1, cfg["range_max"])
            session_id = f"{player}_{int(time.time())}_{random.randint(100, 999)}"

            GAMES_STATE["sessions"][session_id] = {
                "player": player,
                "secret_code": secret_code,
                "range_max": cfg["range_max"],
                "max_tries": cfg["max_tries"],
                "tries_left": cfg["max_tries"],
                "multiplier": cfg["multiplier"],
                "guesses_history": [],
                "status": "in_progress",
                "score": 0,
                "started_at": time.time()
            }

            self._send_json(200, {
                "session_id": session_id,
                "player": player,
                "range_max": cfg["range_max"],
                "max_tries": cfg["max_tries"],
                "message": f"Partie lancee ! Devinez le code secret du Core entre 1 et {cfg['range_max']}."
            })

        # 2. Tenter de deviner le code secret du Cloud
        elif self.path == "/api/game/guess":
            session_id = payload.get("session_id")
            session = GAMES_STATE["sessions"].get(session_id)

            if not session:
                self._send_json(404, {"error": "Session invalide ou terminee. Veuillez recommencer."})
                return

            if session["status"] != "in_progress":
                self._send_json(400, {"error": "Cette partie est deja achevee.", "status": session["status"]})
                return

            try:
                guess = int(payload.get("guess"))
            except (ValueError, TypeError):
                self._send_json(400, {"error": "Veuillez fournir un nombre valide."})
                return

            session["tries_left"] -= 1
            GAMES_STATE["global_stats"]["total_actions"] += 1

            secret = session["secret_code"]
            result = {}

            if guess == secret:
                # Victoire !
                session["status"] = "won"
                duration = max(1, round(time.time() - session["started_at"], 1))
                # Calcul de points : base + bonus tentatives restantes + bonus temps
                points = int((100 + (session["tries_left"] * 25)) * session["multiplier"])
                session["score"] += points
                GAMES_STATE["global_stats"]["cores_hacked"] += 1

                # Mise a jour du leaderboard
                self._update_leaderboard(session["player"], session["score"], won=True)

                result = {
                    "verdict": "CORE_HACKED",
                    "feedback": f"🎉 BRAVO ! Le code secret etait bien {secret} !",
                    "points_earned": points,
                    "final_score": session["score"],
                    "duration_seconds": duration,
                    "tries_left": session["tries_left"],
                    "leaderboard": GAMES_STATE["leaderboard"]
                }
            elif session["tries_left"] <= 0:
                # Defaite
                session["status"] = "lost"
                result = {
                    "verdict": "SYSTEM_LOCKED",
                    "feedback": f"💥 ECHEC ! Pare-feu active. Le code secret etait {secret}.",
                    "secret_was": secret,
                    "points_earned": 0,
                    "final_score": session["score"],
                    "tries_left": 0,
                    "leaderboard": GAMES_STATE["leaderboard"]
                }
            else:
                hint = "TROP GRAND 🔽" if guess > secret else "TROP PETIT 🔼"
                # Calcul de distance pour indice chaud/froid
                diff_val = abs(guess - secret)
                temperature = "BRULANT 🔥" if diff_val <= 3 else ("CHAUD ☀️" if diff_val <= 10 else "FROID ❄️")

                result = {
                    "verdict": "TRY_AGAIN",
                    "feedback": f"{hint} (Indice: {temperature})",
                    "tries_left": session["tries_left"],
                    "guess": guess
                }

            session["guesses_history"].append({"guess": guess, "result": result["verdict"]})
            self._send_json(200, result)

        # 3. Action arcade "Collecter des ressources Cloud / Neutraliser un bug"
        elif self.path == "/api/game/miner":
            session_id = payload.get("session_id")
            session = GAMES_STATE["sessions"].get(session_id)
            player = session["player"] if session else payload.get("player", "Joueur_Anonyme")

            action_type = payload.get("action_type", "mine") # 'mine' ou 'debug'
            points = 10 if action_type == "mine" else 25

            if action_type == "debug":
                GAMES_STATE["global_stats"]["bugs_eliminated"] += 1
            GAMES_STATE["global_stats"]["total_actions"] += 1

            if session:
                session["score"] += points

            self._update_leaderboard(player, points, won=False)

            self._send_json(200, {
                "message": f"Action '{action_type}' effectuee par {player}",
                "points_added": points,
                "global_stats": GAMES_STATE["global_stats"],
                "leaderboard": GAMES_STATE["leaderboard"]
            })

        else:
            self._send_json(404, {"error": "Endpoint POST introuvable"})

    def _update_leaderboard(self, player_name, points, won=False):
        found = False
        for entry in GAMES_STATE["leaderboard"]:
            if entry["player"].lower() == player_name.lower():
                entry["score"] += points
                if won:
                    entry["games_won"] = entry.get("games_won", 0) + 1
                found = True
                break
        if not found:
            GAMES_STATE["leaderboard"].append({
                "player": player_name,
                "score": points,
                "games_won": 1 if won else 0
            })
        # Tri decroissant par score
        GAMES_STATE["leaderboard"].sort(key=lambda x: x["score"], reverse=True)
        GAMES_STATE["leaderboard"] = GAMES_STATE["leaderboard"][:10]

    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [GAME-SERVER] {args[0]} - {args[1]}", flush=True)

class ThreadedHTTPServer(HTTPServer):
    pass

httpd = ThreadedHTTPServer(("0.0.0.0", PORT), GameRequestHandler)

def shutdown_handler(signum, frame):
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[GAME-SERVER] >>> SIGNAL {sig_name} RECU (Signal code: {signum}) <<<", flush=True)
    print(f"[GAME-SERVER] Sauvegarde finale du classement joueurs : {GAMES_STATE['leaderboard']}", flush=True)
    
    def do_shutdown():
        httpd.shutdown()
        httpd.server_close()
        print(f"[GAME-SERVER] Serveur de jeu coupe proprement. Code sortie : 0", flush=True)
        sys.exit(0)

    threading.Thread(target=do_shutdown).start()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

try:
    print(f"[GAME-SERVER] Moteur pret sur le port {PORT}.", flush=True)
    httpd.serve_forever()
except Exception as e:
    print(f"[GAME-SERVER] Erreur : {e}", flush=True)

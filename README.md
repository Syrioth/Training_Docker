# ☁️ Projet Docker Cloud — Rendu TP Master 1 Informatique

Projet de virtualisation et d'orchestration multi-conteneurs basé sur Docker.
Conformément aux consignes et au barème d'évaluation :
- **0 image issue de Docker Hub** : Toutes les images sont personnalisées via leur propre `Dockerfile` (y compris le Front Nginx, compilé sur Alpine).
- **3 types d'images distinctes** : 
  1. **Front-End Nginx** (Serveur Web & Reverse Proxy)
  2. **Back-End API** (Python 3)
  3. **Serveur Web Spécialisé / Jeu** (Python 3, Cœur de données)
- **Code Hello World épuré** : Démontre la chaîne complète de communication réseau sans complexité inutile.
- **Ressources cgroups contraintes** : Quotas stricts de CPU et de mémoire alloués à chaque conteneur.
- **Arrêt gracieux géré** : Signaux POSIX (`SIGQUIT` pour Nginx, `SIGTERM` pour Python) sous PID 1.
- **Ordonnancement séquentiel** : Utilisation des `healthcheck` et de `depends_on (condition: service_healthy)`.

---

## 📋 Récapitulatif du Barème & Justifications

| Critère du Barème | Réalisation Technique & Justification |
| :--- | :--- |
| **Mise en forme du rendu (/1)** | Dépôt Git structuré, fichiers sources indentés et commentés, configuration centralisée dans `.env` et `docker-compose.yml`. |
| **Explication des dépendances installées (/1)** | Base `alpine:3.20` (~7 Mo). **Front** : `nginx` (serveur web asynchrone haute performance et reverse proxy) et `curl`. **Back & Game** : `python3` (runtime natif sans module `pip` tiers) et `curl` pour les sondes `HEALTHCHECK`. Nettoyage immédiat du cache apk (`rm -rf /var/cache/apk/*`). |
| **Explication des manipulations sur l'OS (/1)** | Respect strict du principe de moindre privilège : utilisateurs non-root dédiés (`frontuser:1003`, `backuser:1002`, `gameuser:1001`) avec shell interactif désactivé (`-s /sbin/nologin`). Pour Nginx : création et assignation des répertoires temporaires (`/var/log/nginx`, `/tmp/client_temp`, etc.) accessibles en non-root. |
| **Explication des arguments attendus (/1)** | Arguments au build (`ARG DEFAULT_PORT`) et arguments au run sous forme de variables d'environnement (`PORT`, `SERVICE_NAME`, `GAME_SERVER_URL`, `PYTHONUNBUFFERED=1`). |
| **Explications sur les entrypoints choisis (/1)** | Syntaxe **Exec Form** : `ENTRYPOINT ["nginx"]` pour le front (avec `daemon off;` dans `nginx.conf`) et `ENTRYPOINT ["python3", "app.py"]` pour le back. Les exécutables tournent directement en **PID 1**, sans sous-shell `/bin/sh -c`, interceptant immédiatement les signaux d'arrêt émis par Docker. |
| **Arguments traduits dans Docker Compose (/1)** | Fichier `.env` mappé directement dans les sections `environment:`, `ports:` et `deploy.resources` de `docker-compose.yml`. |
| **Limitation des ressources de chaque conteneur (/1)** | Quotas cgroups définis dans `deploy.resources.limits` : **Front (Nginx)** : 0.25 CPU / 64 Mo RAM (très faible empreinte mémoire) • **Back** : 0.50 CPU / 128 Mo RAM • **Serveur Web / Jeu** : 0.50 CPU / 128 Mo RAM. |
| **Les SIGTERM / SIGQUIT sont gérés (/1)** | Nginx configuré avec `STOPSIGNAL SIGQUIT` (fermeture gracieuse des workers après traitement des connexions en cours). Les services Python capturent `SIGTERM`. Arrêt immédiat sous 1 seconde sans timeout `SIGKILL`. Code de sortie : 0. |
| **Dépendances & Ordre de démarrage (/1)** | Ordonnancement séquentiel garanti : `game-server` (Healthcheck OK) ➔ `back` (démarre une fois game-server `healthy`) ➔ `front` (démarre une fois back `healthy`). |
| **Schéma des communications (/1)** | Schéma vectoriel SVG (`architecture.svg`) et diagramme Mermaid ci-dessous. |

---

## 🗺️ Schéma des Communications & Architecture

```mermaid
flowchart TD
    subgraph MachineHote["Machine Hôte (Navigateur / Client)"]
        Browser["🌐 Navigateur Web (http://localhost:8080)"]
    end

    subgraph ReseauDocker["Réseau Isolé Docker Bridge : docker_cloud_net"]
        subgraph FrontContainer["Conteneur : cloud_front_dashboard"]
            Front["front : Nginx Custom (Port 8080)<br/>User non-root: frontuser (1003)<br/>Limites : 0.25 CPU | 64 Mo RAM<br/>Reverse Proxy : /api/ ➔ back:8081"]
        end

        subgraph BackContainer["Conteneur : cloud_back_api"]
            Back["back : API Python (Port 8081)<br/>User non-root: backuser (1002)<br/>Limites : 0.50 CPU | 128 Mo RAM"]
        end

        subgraph GameContainer["Conteneur : cloud_game_server"]
            Game["game-server : Web Server Python (Port 8082)<br/>User non-root: gameuser (1001)<br/>Limites : 0.50 CPU | 128 Mo RAM"]
        end
    end

    %% Flux réseau
    Browser -->|"1. Accès Web :8080"| Front
    Front -->|"2. proxy_pass /api/ (Interne :8081)"| Back
    Back -->|"3. HTTP Interne : http://game-server:8082"| Game

    %% Ordre de démarrage garanti
    Game -.->|"Condition : service_healthy (1er)"| Back
    Back -.->|"Condition : service_healthy (2e)"| Front
```

---

## 🚀 Démarrage Rapide

### 1. Construire les images personnalisées
```bash
docker compose build
```

### 2. Démarrer la stack en arrière-plan
```bash
docker compose up -d
```

### 3. Tester dans le navigateur
Ouvrez votre navigateur sur : **[http://localhost:8080](http://localhost:8080)**

Vous observerez que **Nginx sert l'interface** et relaie automatiquement les requêtes via sa directive `proxy_pass` vers l'API backend et le serveur de jeu :
- **Front Nginx** : `Hello World from Front-End Nginx Container!`
- **Back API** : `Hello World from Back-End API!`
- **Serveur Web / Jeu** : `Hello World from Game Web Server!`

### 4. Vérifier les limitations de ressources cgroups
```powershell
docker inspect cloud_front_dashboard --format 'Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCPUs}}'
docker inspect cloud_game_server --format 'Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCPUs}}'
```

### 5. Vérifier l'arrêt gracieux
```powershell
docker stop cloud_front_dashboard
docker stop cloud_game_server
docker logs cloud_game_server --tail 5
```

### 6. Éteindre la stack
```bash
docker compose down
```

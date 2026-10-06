# ==============================================================================
# Dockerfile : game-server
# Serveur de jeux / web-service spécialisé pour l'architecture Docker Cloud
# ==============================================================================

# 1. Choix de l'image de base :
# Utilisation d'Alpine Linux 3.20 : image minimale, sécurisée et légère (~7 Mo).
FROM alpine:3.20

# Métadonnées du build
LABEL maintainer="Étudiant Master M1" \
      description="Serveur de jeu personnalisé - Module Docker Cloud" \
      version="1.0"

# 2. Variables de build (ARG) et d'exécution (ENV)
# Définition des valeurs par défaut configurables au run via docker-compose
ARG DEFAULT_PORT=8082
ENV PORT=${DEFAULT_PORT} \
    GAME_NAME="PixelQuest" \
    MAX_PLAYERS="16" \
    DIFFICULTY="medium" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances :
# - Mise à jour des dépôts de paquets
# - Installation de python3 (runtime d'exécution de notre serveur)
# - Installation de curl (requis par le HEALTHCHECK de Docker)
# - Nettoyage du cache apk pour minimiser la taille de l'image finale
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Création d'un utilisateur système non-root
# Ne jamais exécuter un conteneur en root en production (principe du moindre privilège).
# UID 1001 / GID 1001
RUN addgroup -g 1001 -S gamesquad && \
    adduser -u 1001 -S -D -h /app -s /sbin/nologin -G gamesquad gameuser

# 5. Définition du répertoire de travail
WORKDIR /app

# 6. Copie du code applicatif et configuration des permissions
COPY server.py /app/server.py
RUN chown -R gameuser:gamesquad /app && \
    chmod 755 /app/server.py

# 7. Passage à l'utilisateur non-root
USER gameuser

# 8. Exposition du port réseau (documentation du port utilisé)
EXPOSE 8082

# 9. Healthcheck intégré à l'image
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8082/health || exit 1

# 10. Choix de l'ENTRYPOINT :
# Utilisation impérative de la syntaxe Exec Form ["executable", "param"]
# pour que python3 devienne le PID 1 à l'intérieur du conteneur.
# Cela permet la réception directe des signaux système (SIGTERM / SIGINT)
# et garantit un arrêt gracieux (graceful shutdown) sans forcer un SIGKILL.
ENTRYPOINT ["python3", "/app/server.py"]

# ==============================================================================
# Dockerfile : back
# API Backend / Orchestrateur de services pour l'architecture Docker Cloud
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (légèreté et sécurité)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="API Backend personnalisée - Architecture Docker Cloud" \
      version="1.0"

# 2. Arguments de build et variables d'environnement au run
ARG DEFAULT_PORT=8081
ENV PORT=${DEFAULT_PORT} \
    SERVICE_NAME="backend-core-api" \
    ENVIRONMENT="production" \
    GAME_SERVER_URL="http://game-server:8082" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances
# - Mise à jour de l'index des paquets
# - Installation de python3 et curl (indispensable pour les healthchecks)
# - Purge du cache des paquets pour réduire la taille de l'image
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Création de l'utilisateur non-root backuser
# UID 1002 / GID 1002
RUN addgroup -g 1002 -S backgroup && \
    adduser -u 1002 -S -D -h /app -s /sbin/nologin -G backgroup backuser

# 5. Définition du répertoire de travail
WORKDIR /app

# 6. Copie des fichiers sources et configuration des droits
COPY app.py /app/app.py
RUN chown -R backuser:backgroup /app && \
    chmod 755 /app/app.py

# 7. Changement d'utilisateur (exécution sans privilèges root)
USER backuser

# 8. Exposition du port réseau interne
EXPOSE 8081

# 9. Healthcheck Docker
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1

# 10. ENTRYPOINT en exec form ["executable", "param"]
# Garantit que python3 reçoit directement les signaux SIGTERM / SIGINT
# émis par docker stop ou docker compose down
ENTRYPOINT ["python3", "/app/app.py"]

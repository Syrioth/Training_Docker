# ==============================================================================
# Dockerfile : front
# Serveur Web Frontend / Dashboard pour l'architecture Docker Cloud
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (légèreté et sécurité)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="Dashboard Frontend personnalisé - Architecture Docker Cloud" \
      version="1.0"

# 2. Arguments de build et variables d'environnement au run
ARG DEFAULT_PORT=8080
ENV PORT=${DEFAULT_PORT} \
    BACKEND_URL="http://back:8081" \
    APP_TITLE="Docker Cloud Dashboard M1" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances
# - Installation de python3 et curl (indispensable pour les healthchecks)
# - Purge du cache des paquets apk
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Création de l'utilisateur non-root frontuser
# UID 1003 / GID 1003
RUN addgroup -g 1003 -S frontgroup && \
    adduser -u 1003 -S -D -h /app -s /sbin/nologin -G frontgroup frontuser

# 5. Définition du répertoire de travail
WORKDIR /app

# 6. Copie des fichiers sources (serveur + assets statiques) et configuration des droits
COPY server.py /app/server.py
COPY static /app/static
RUN chown -R frontuser:frontgroup /app && \
    chmod 755 /app/server.py

# 7. Changement d'utilisateur (exécution sans privilèges root)
USER frontuser

# 8. Exposition du port réseau public
EXPOSE 8080

# 9. Healthcheck Docker
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# 10. ENTRYPOINT en exec form ["executable", "param"]
# Garantit que python3 reçoit directement les signaux SIGTERM / SIGINT
ENTRYPOINT ["python3", "/app/server.py"]

# ==============================================================================
# Dockerfile : front (Serveur Web & Reverse Proxy Nginx Personnalisé)
# Architecture Docker Cloud - Master 1 Informatique
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (légèreté et sécurité, ~7 Mo)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="Serveur Front-End Nginx personnalisé (0 image Docker Hub)"

# 2. Manipulations sur l'OS et installation des dépendances
# - Installation explicite du serveur HTTP Nginx et de cURL pour le healthcheck
# - Suppression du cache des paquets apk pour optimiser la taille de l'image
RUN apk update && \
    apk add --no-cache nginx curl && \
    rm -rf /var/cache/apk/*

# 3. Sécurité OS : Création d'un utilisateur et d'un groupe non-root
# UID 1003 / GID 1003 avec shell interactif désactivé (/sbin/nologin)
RUN addgroup -g 1003 -S frontgroup && \
    adduser -u 1003 -S -D -h /usr/share/nginx/html -s /sbin/nologin -G frontgroup frontuser

# 4. Configuration des dossiers nécessaires à Nginx avec les bons droits non-root
RUN mkdir -p /var/log/nginx /var/lib/nginx /tmp/client_temp /tmp/proxy_temp_path /run/nginx && \
    chown -R frontuser:frontgroup /var/log/nginx /var/lib/nginx /tmp /run/nginx /etc/nginx

# 5. Injection de notre configuration Nginx personnalisée et des fichiers statiques
COPY nginx.conf /etc/nginx/nginx.conf
COPY static/ /usr/share/nginx/html/

RUN chown -R frontuser:frontgroup /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# 6. Bascule sur l'utilisateur non-root (principe du moindre privilège)
USER frontuser

# 7. Exposition du port réseau (8080 : port non-privilégié)
EXPOSE 8080

# 8. Healthcheck Docker pour garantir l'ordre de démarrage séquentiel
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# 9. Gestion des signaux : Nginx s'arrête gracieusement sur SIGQUIT ou SIGTERM
STOPSIGNAL SIGQUIT

# 10. ENTRYPOINT en Exec Form ["executable", "param"] pour être PID 1
# La directive 'daemon off;' est déjà intégrée dans nginx.conf
ENTRYPOINT ["nginx"]

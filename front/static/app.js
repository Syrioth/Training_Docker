function updateClock() {
    const el = document.getElementById('clock');
    if (el) el.textContent = new Date().toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

function logToTerminal(message, type = 'info') {
    const terminal = document.getElementById('terminal-logs');
    if (!terminal) return;
    const line = document.createElement('div');
    line.className = `log-line log-${type}`;
    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

document.getElementById('btn-clear-logs')?.addEventListener('click', () => {
    const terminal = document.getElementById('terminal-logs');
    if (terminal) terminal.innerHTML = '<div class="log-line log-info">[SYSTEM] Console reinitialisee.</div>';
});

async function checkCloudStatus() {
    try {
        const resp = await fetch('/api/proxy/cloud-status');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        // Update badges
        const globalBadge = document.getElementById('global-status-badge');
        const backStatus = document.getElementById('status-back');
        const gameStatus = document.getElementById('status-game');

        if (globalBadge) {
            globalBadge.className = 'badge pill-green';
            globalBadge.textContent = 'Cluster Opérationnel (3/3)';
        }

        if (backStatus) {
            backStatus.className = 'pill pill-green';
            backStatus.textContent = 'En ligne (Healthy)';
        }

        if (gameStatus) {
            if (data.game_server_status === 'healthy') {
                gameStatus.className = 'pill pill-green';
                gameStatus.textContent = 'En ligne (Healthy)';
            } else {
                gameStatus.className = 'pill pill-red';
                gameStatus.textContent = 'Injoignable';
            }
        }
    } catch (err) {
        const globalBadge = document.getElementById('global-status-badge');
        const backStatus = document.getElementById('status-back');
        if (globalBadge) {
            globalBadge.className = 'badge pill-red';
            globalBadge.textContent = 'Erreur Cluster';
        }
        if (backStatus) {
            backStatus.className = 'pill pill-red';
            backStatus.textContent = 'Déconnecté';
        }
        logToTerminal(`Erreur verification statut cluster: ${err.message}`, 'err');
    }
}

async function loadGameData() {
    try {
        const resp = await fetch('/api/proxy/game-status');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const result = await resp.json();
        const data = result.game_data;

        if (data && !data.error) {
            document.getElementById('game-name').textContent = data.game_name || 'PixelQuest';
            document.getElementById('game-players').textContent = `${data.active_players || 0} / ${data.max_players || 16}`;
            document.getElementById('game-diff').textContent = (data.difficulty || 'Normal').toUpperCase();
            document.getElementById('game-uptime').textContent = `${data.uptime_seconds}s`;

            const scoresList = document.getElementById('scores-list');
            if (scoresList && data.scores) {
                scoresList.innerHTML = '';
                for (const [p, s] of Object.entries(data.scores)) {
                    const chip = document.createElement('span');
                    chip.className = 'chip';
                    chip.innerHTML = `${p}: <span>${s} pts</span>`;
                    scoresList.appendChild(chip);
                }
            }
        }
    } catch (err) {
        logToTerminal(`Impossible de charger les donnees de jeu: ${err.message}`, 'warn');
    }
}

document.getElementById('btn-refresh')?.addEventListener('click', () => {
    logToTerminal('Actualisation manuelle demandee par l\'utilisateur...', 'info');
    checkCloudStatus();
    loadGameData();
});

document.getElementById('btn-action')?.addEventListener('click', async () => {
    const player = document.getElementById('player-input').value.trim() || 'Joueur_Anonyme';
    const points = parseInt(document.getElementById('points-input').value, 10) || 10;

    logToTerminal(`Transmission de l'action: ${player} (+${points} pts)...`, 'info');

    try {
        const resp = await fetch('/api/proxy/game-action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player, points })
        });
        const res = await resp.json();
        if (resp.ok) {
            logToTerminal(`Succes : Action validee par le Game-Server ! Nouveau score : ${res.new_score}`, 'success');
            loadGameData();
        } else {
            logToTerminal(`Erreur de traitement : ${res.error || 'Inconnue'}`, 'err');
        }
    } catch (e) {
        logToTerminal(`Erreur reseau lors de l'envoi de l'action : ${e.message}`, 'err');
    }
});

// Initialisation et boucle de rafraichissement
checkCloudStatus();
loadGameData();
setInterval(checkCloudStatus, 5000);
setInterval(loadGameData, 5000);
logToTerminal('Connexion etablie avec front-app sur http://localhost:8080', 'success');

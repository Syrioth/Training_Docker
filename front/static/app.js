// ==============================================================================
// PixelQuest : Cloud Heist - Frontend Game Client
// ==============================================================================

// Synthese sonore retro via Web Audio API (0 dependance externe)
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(type) {
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (type === 'click') {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.05);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
    } else if (type === 'win') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.1);
        osc.frequency.setValueAtTime(783.99, now + 0.2);
        osc.frequency.setValueAtTime(1046.50, now + 0.3);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
        osc.start(now);
        osc.stop(now + 0.5);
    } else if (type === 'lose') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(300, now);
        osc.frequency.exponentialRampToValueAtTime(120, now + 0.3);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
    } else if (type === 'hint') {
        osc.frequency.setValueAtTime(600, now);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        osc.start(now);
        osc.stop(now + 0.1);
    }
}

// Variables d'etat de la session de jeu
let currentSessionId = null;
let currentScore = 0;
let minerCredits = 0;

// Log dans le terminal
function logMini(msg, type = 'info') {
    const term = document.getElementById('mini-terminal');
    if (!term) return;
    const row = document.createElement('div');
    row.className = `log-row ${type}`;
    const time = new Date().toLocaleTimeString();
    row.textContent = `[${time}] ${msg}`;
    term.appendChild(row);
    term.scrollTop = term.scrollHeight;
}

document.getElementById('btn-clear-console')?.addEventListener('click', () => {
    const term = document.getElementById('mini-terminal');
    if (term) term.innerHTML = '<div class="log-row info">[SYS] Console réinitialisée.</div>';
});

// Horloge
function updateClock() {
    const el = document.getElementById('clock');
    if (el) el.textContent = new Date().toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

// Gestion des onglets
const tabHeist = document.getElementById('tab-btn-heist');
const tabMiner = document.getElementById('tab-btn-miner');
const contentHeist = document.getElementById('tab-content-heist');
const contentMiner = document.getElementById('tab-content-miner');

tabHeist?.addEventListener('click', () => {
    tabHeist.classList.add('active');
    tabMiner.classList.remove('active');
    contentHeist.classList.remove('hidden');
    contentMiner.classList.add('hidden');
});

tabMiner?.addEventListener('click', () => {
    tabMiner.classList.add('active');
    tabHeist.classList.remove('active');
    contentMiner.classList.remove('hidden');
    contentHeist.classList.add('hidden');
});

// ------------------------------------------------------------------------------
// MODE 1 : HACK THE CLOUD CORE
// ------------------------------------------------------------------------------
const setupPanel = document.getElementById('heist-setup');
const playPanel = document.getElementById('heist-play');
const btnStart = document.getElementById('btn-start-game');
const btnGuess = document.getElementById('btn-submit-guess');
const btnAbort = document.getElementById('btn-abort-game');
const inputGuess = document.getElementById('guess-input');

btnStart?.addEventListener('click', async () => {
    const player = document.getElementById('player-name').value.trim() || 'Hacker_M1';
    const difficulty = document.getElementById('game-difficulty').value;

    playSound('click');
    logMini(`Infiltration du Core par ${player} [Mode: ${difficulty}]...`, 'info');

    try {
        const resp = await fetch('/api/proxy/game-start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player, difficulty })
        });
        const data = await resp.json();

        if (resp.ok) {
            currentSessionId = data.session_id;
            setupPanel.classList.add('hidden');
            playPanel.classList.remove('hidden');

            document.getElementById('current-player-display').textContent = data.player;
            document.getElementById('tries-left-display').textContent = data.max_tries;
            document.getElementById('core-range-hint').textContent = `Le code secret se situe entre 1 et ${data.range_max}`;
            document.getElementById('guess-feedback').className = 'feedback-banner';
            document.getElementById('guess-feedback').textContent = "Système prêt. Entrez votre première proposition.";
            document.getElementById('attempts-list').innerHTML = '';
            inputGuess.value = '';
            inputGuess.focus();
            logMini(`Session ${currentSessionId.slice(0, 12)}... validée par game-server`, 'success');
        } else {
            alert(`Erreur: ${data.error}`);
        }
    } catch (e) {
        logMini(`Erreur réseau: ${e.message}`, 'err');
    }
});

btnGuess?.addEventListener('click', submitGuess);
inputGuess?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitGuess();
});

async function submitGuess() {
    const val = parseInt(inputGuess.value, 10);
    if (isNaN(val)) return;

    playSound('click');
    inputGuess.value = '';
    inputGuess.focus();

    try {
        const resp = await fetch('/api/proxy/game-guess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, guess: val })
        });
        const data = await resp.json();

        if (!resp.ok) {
            alert(data.error || 'Erreur lors du test');
            return;
        }

        const feedbackEl = document.getElementById('guess-feedback');
        feedbackEl.textContent = data.feedback;

        // Historique des chips
        const attemptsList = document.getElementById('attempts-list');
        const chip = document.createElement('span');
        chip.className = 'guess-chip';
        chip.textContent = `${val}`;
        attemptsList.appendChild(chip);

        document.getElementById('tries-left-display').textContent = data.tries_left;

        if (data.verdict === 'CORE_HACKED') {
            playSound('win');
            feedbackEl.className = 'feedback-banner feedback-win';
            document.getElementById('player-score-display').textContent = data.final_score;
            logMini(`VICTOIRE ! Core piraté en ${data.duration_seconds}s ! (+${data.points_earned} pts)`, 'success');
            renderLeaderboard(data.leaderboard);
            setTimeout(() => {
                if (confirm(`🏆 BRAVO ! Vous avez piraté le Core Cloud !\nPoints gagnés : ${data.points_earned}\nRejouer ?`)) {
                    btnAbort.click();
                }
            }, 500);
        } else if (data.verdict === 'SYSTEM_LOCKED') {
            playSound('lose');
            feedbackEl.className = 'feedback-banner feedback-lose';
            logMini(`ECHEC ! Système verrouillé. Code: ${data.secret_was}`, 'err');
            renderLeaderboard(data.leaderboard);
            setTimeout(() => {
                if (confirm(`💥 Échec de l'infiltration !\nLe code était ${data.secret_was}.\nRecommencer ?`)) {
                    btnAbort.click();
                }
            }, 500);
        } else {
            playSound('hint');
            if (data.feedback.includes('BRULANT') || data.feedback.includes('CHAUD')) {
                feedbackEl.className = 'feedback-banner feedback-hot';
            } else {
                feedbackEl.className = 'feedback-banner feedback-cold';
            }
            logMini(`Test ${val} -> ${data.feedback}`, 'warn');
        }
    } catch (e) {
        logMini(`Erreur transmission: ${e.message}`, 'err');
    }
}

btnAbort?.addEventListener('click', () => {
    currentSessionId = null;
    playPanel.classList.add('hidden');
    setupPanel.classList.remove('hidden');
    logMini('Session de hack abandonnée par l\'utilisateur.', 'info');
});

// ------------------------------------------------------------------------------
// MODE 2 : CLOUD DATA MINER (ARCADE)
// ------------------------------------------------------------------------------
function initMinerGrid() {
    const grid = document.getElementById('server-cluster-grid');
    if (!grid) return;
    grid.innerHTML = '';

    for (let i = 1; i <= 8; i++) {
        const node = document.createElement('div');
        node.className = 'server-node';
        node.dataset.id = i;
        node.innerHTML = `
            <span class="node-icon">🖥️</span>
            <span class="node-label">Cluster-Node-#0${i}</span>
        `;

        node.addEventListener('click', async () => {
            playSound('click');
            const isAlert = node.classList.contains('alert');
            const actionType = isAlert ? 'debug' : 'mine';

            if (isAlert) {
                node.classList.remove('alert');
                node.querySelector('.node-icon').textContent = '🖥️';
                playSound('win');
            }

            const player = document.getElementById('player-name').value.trim() || 'Miner_M1';

            try {
                const resp = await fetch('/api/proxy/game-miner', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId, player, action_type: actionType })
                });
                const data = await resp.json();
                if (resp.ok) {
                    minerCredits += data.points_added;
                    document.getElementById('miner-total-pts').textContent = `${minerCredits} pts`;
                    logMini(`Action [${actionType.toUpperCase()}] sur Node-#0${i} (+${data.points_added} pts)`, isAlert ? 'success' : 'info');
                    renderLeaderboard(data.leaderboard);
                    updateStatsDisplay(data.global_stats);
                }
            } catch (e) {
                logMini(`Erreur miner: ${e.message}`, 'err');
            }
        });

        grid.appendChild(node);
    }
}
initMinerGrid();

// Apparition aléatoire d'alertes DDoS à neutraliser
setInterval(() => {
    const nodes = document.querySelectorAll('.server-node');
    if (nodes.length === 0) return;
    const randomIdx = Math.floor(Math.random() * nodes.length);
    const target = nodes[randomIdx];
    if (!target.classList.contains('alert')) {
        target.classList.add('alert');
        target.querySelector('.node-icon').textContent = '⚠️';
        logMini(`🚨 ALERTE DDoS détectée sur Node-#0${randomIdx + 1} ! Neutralisez-la !`, 'err');
    }
}, 8000);

// ------------------------------------------------------------------------------
// ACTUALISATION LEADERBOARD & METRIQUES CLOUD
// ------------------------------------------------------------------------------
async function fetchGameStatus() {
    try {
        const resp = await fetch('/api/proxy/game-status');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const result = await resp.json();
        const data = result.game_data;

        if (data && !data.error) {
            renderLeaderboard(data.leaderboard);
            updateStatsDisplay(data.global_stats);
            document.getElementById('stat-uptime').textContent = `${data.uptime_seconds}s`;
        }
    } catch (e) {
        logMini(`Sync game-server: ${e.message}`, 'warn');
    }
}

function renderLeaderboard(list) {
    const container = document.getElementById('leaderboard-container');
    if (!container || !list) return;

    container.innerHTML = '';
    list.forEach((item, idx) => {
        const row = document.createElement('div');
        row.className = `leaderboard-row rank-${idx + 1}`;
        const medal = idx === 0 ? '🥇' : (idx === 1 ? '🥈' : (idx === 2 ? '🥉' : `#${idx + 1}`));
        row.innerHTML = `
            <div>
                <span class="player-rank">${medal}</span>
                <strong>${item.player}</strong>
                ${item.games_won ? `<small style="color: #94a3b8"> (${item.games_won} victoires)</small>` : ''}
            </div>
            <span class="player-score-tag">${item.score} pts</span>
        `;
        container.appendChild(row);
    });
}

function updateStatsDisplay(stats) {
    if (!stats) return;
    document.getElementById('stat-total-actions').textContent = stats.total_actions || 0;
    document.getElementById('stat-cores-hacked').textContent = stats.cores_hacked || 0;
    document.getElementById('stat-bugs-eliminated').textContent = stats.bugs_eliminated || 0;
}

document.getElementById('btn-refresh-scores')?.addEventListener('click', () => {
    playSound('click');
    fetchGameStatus();
});

// Verification globale du cluster
async function fetchCloudClusterHealth() {
    try {
        const resp = await fetch('/api/proxy/cloud-status');
        if (!resp.ok) throw new Error();
        const badge = document.getElementById('global-status-badge');
        if (badge) {
            badge.className = 'badge pill-green';
            badge.textContent = 'Cluster Opérationnel (3/3)';
        }
    } catch (e) {
        const badge = document.getElementById('global-status-badge');
        if (badge) {
            badge.className = 'badge pill-red';
            badge.textContent = 'Cluster Injoignable';
        }
    }
}

// Boucle de rafraichissement automatique
fetchCloudClusterHealth();
fetchGameStatus();
setInterval(fetchCloudClusterHealth, 6000);
setInterval(fetchGameStatus, 6000);

(function() {
const TOKEN = localStorage.getItem('darkx_token');

/* ─── FALLBACK RESPONSES (works without WebSocket) ─── */
const AGENT_INTROS = [
    'BLADE: Blade stands ready. Target acquisition protocols online.',
    'SHADOW: Shadow here. The army awaits your command.',
    'HUNTER: Hunter tracking systems active.',
    'SENTRY: Sentry perimeter established. All defenses operational.',
    'INFERNO: INFERNO ACTIVE. Brute force modules ready.',
    'SPECTER: Specter fading into the shadows. Stealth protocols engaged.',
    'NULL: Null interface loaded. Data structures analyzed.',
    'PHANTOM: Phantom intelligence network live.',
    'ASSASSIN: Assassin awaiting orders.',
    'TITAN: Titan defense matrix activated.',
    'WARLOCK: Warlock channeling arcane protocols.',
    'RANGER: Ranger at your service.',
    'ENGINEER: Engineer online. Tool crafting ready.',
    'SUMMONER: Summoner here. I call forth entities from the digital abyss.',
    'OVERLORD: Overlord addressing the Shadow Monarch. All agents report.',
];

function writeTerminal(text, className = '') {
    const body = document.getElementById('terminal-body');
    if (!body) return;
    const line = document.createElement('div');
    line.className = 'terminal-line' + (className ? ' ' + className : '');
    line.textContent = text;
    body.appendChild(line);
    body.scrollTop = body.scrollHeight;
}

function getFallbackResponse(cmd) {
    if (cmd === '/arise') {
        const msgs = ['S-SYSTEM: Awakening the Shadow Army...', 'S-SYSTEM: Neural links synchronizing...', 'S-SYSTEM: All systems nominal.'];
        return msgs.concat(AGENT_INTROS).concat(['S-SYSTEM: All 15 agents active. Ready to serve.']);
    }
    if (cmd === '/rest') {
        return ['S-SYSTEM: Deactivating agents...', 'SHADOW: Until next time, Monarch.', 'S-SYSTEM: All agents dormant.'];
    }
    if (cmd === '/status') {
        return ['S-SYSTEM STATUS: Neural Link: Stable | Memory: 98% Optimized | Agents: 15/15 Online | Uptime: Operational'];
    }
    if (cmd === '/stats') {
        const username = (JSON.parse(localStorage.getItem('darkx_user') || '{}')).username || 'Shadow';
        return [`CURRENT STATS: User: ${username} | Level: 1 | Rank: Shadow Initiate | Total XP: 0 | Streak: 0 Days`];
    }
    if (cmd === '/power') {
        return ['UNLOCKED POWERS: [None] - Complete tasks to gain XP and level up.'];
    }
    if (cmd === '/daily') {
        return ['DAILY QUESTS: Available. Switch to the Tasks tab to begin your trials.'];
    }
    if (cmd.startsWith('/')) {
        const name = cmd.slice(1).toLowerCase();
        const match = AGENT_INTROS.find(i => i.startsWith(name.toUpperCase() + ':'));
        if (match) return [match];
        // Try to find by partial name
        const partial = AGENT_INTROS.filter(i => i.toLowerCase().includes(name));
        if (partial.length > 0) return partial;
        return [`Unknown command: ${cmd}. Type /help for available commands.`];
    }
    return [null];
}

/* ─── WEBSOCKET ─── */
let ws = null;
let wsConnected = false;

function connectTerminal() {
    if (!TOKEN) return;
    try {
        const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${proto}//${window.location.host}/api/agents/ws`;
        ws = new WebSocket(wsUrl);
        ws.onopen = () => {
            ws.send(`Bearer ${TOKEN}`);
            wsConnected = true;
            writeTerminal('S-SYSTEM: WebSocket terminal connected.', 'system');
            const dot = document.getElementById('sys-status-dot');
            const text = document.getElementById('sys-status-text');
            if (dot) dot.className = 'status-dot online';
            if (text) text.textContent = 'All systems operational';
        };
        ws.onmessage = (event) => {
            const msg = event.data || '';
            let className = '';
            if (msg.startsWith('S-SYSTEM')) className = 'system';
            else if (msg.includes('ERROR') || msg.includes('Error')) className = 'error';
            else if (msg.includes('success') || msg.includes('ready')) className = 'success';
            else if (msg.includes('STATUS') || msg.includes('STATS') || msg.includes('POWER') || msg.includes('DAILY')) className = 'system';
            writeTerminal(msg, className);
        };
        ws.onclose = () => {
            wsConnected = false;
            setTimeout(connectTerminal, 5000);
        };
        ws.onerror = () => {
            wsConnected = false;
        };
    } catch (e) {
        wsConnected = false;
    }
}

/* ─── INIT ─── */
const input = document.getElementById('terminal-input');
const body = document.getElementById('terminal-body');

if (!input || !body) {
    // Terminal not on this page
} else {
    connectTerminal();

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const cmd = this.value.trim();
            this.value = '';
            if (!cmd) return;

            writeTerminal(`dark-x> ${cmd}`);

            // Handle local-only commands
            if (cmd === '/help') {
                writeTerminal('COMMANDS:\n  /arise   - Activate all agents\n  /rest    - Deactivate all agents\n  /status  - System status\n  /stats   - Your current stats\n  /power   - List unlocked powers\n  /daily   - Today\'s quests\n  /clear   - Clear terminal\n  /agent   - Chat with agent (e.g. /blade)', 'system');
            } else if (cmd === '/clear') {
                body.innerHTML = '<div class="terminal-line welcome">DARK-X v1.0 — Terminal cleared</div>';
            } else if (cmd.startsWith('/') && wsConnected && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(cmd);
            } else if (cmd.startsWith('/')) {
                const responses = getFallbackResponse(cmd);
                if (responses && responses[0]) {
                    responses.forEach(r => writeTerminal(r, r.startsWith('S-SYSTEM') ? 'system' : ''));
                }
            }

            body.scrollTop = body.scrollHeight;
        }
    });

    // Ctrl+` toggles terminal
    document.addEventListener('keydown', function(e) {
        const container = document.getElementById('terminal-container');
        const toggle = document.getElementById('terminal-toggle');
        if (e.ctrlKey && e.key === '`') {
            e.preventDefault();
            if (container) {
                container.classList.toggle('hidden');
                if (toggle) toggle.style.display = container.classList.contains('hidden') ? 'flex' : 'none';
            }
            if (input && !container?.classList.contains('hidden')) input.focus();
        }
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const search = document.getElementById('global-search');
            if (search) search.focus();
        }
    });
}

// Terminal toggle button
(function() {
    const toggle = document.getElementById('terminal-toggle');
    const container = document.getElementById('terminal-container');
    const minimize = document.getElementById('term-minimize');
    const closeBtn = document.getElementById('term-close');
    const clearBtn = document.getElementById('term-clear');

    if (toggle && container) {
        toggle.addEventListener('click', function() {
            container.classList.toggle('hidden');
            this.style.display = container.classList.contains('hidden') ? 'flex' : 'none';
            if (!container.classList.contains('hidden')) input?.focus();
        });
    }
    if (minimize && container) {
        minimize.addEventListener('click', function() {
            container.classList.toggle('minimized');
            if (!container.classList.contains('minimized')) input?.focus();
        });
    }
    if (closeBtn && container && toggle) {
        closeBtn.addEventListener('click', function() {
            container.classList.add('hidden');
            toggle.style.display = 'flex';
        });
    }
    if (clearBtn && body) {
        clearBtn.addEventListener('click', function() {
            body.innerHTML = '<div class="terminal-line welcome">DARK-X v1.0 — Terminal cleared</div>';
        });
    }
})();

// Auto-focus terminal input on page load
setTimeout(function() {
    const ti = document.getElementById('terminal-input');
    if (ti) ti.focus();
}, 500);

})();

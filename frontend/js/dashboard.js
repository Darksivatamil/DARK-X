const API = '/api';
const TOKEN = localStorage.getItem('darkx_token');
if (!TOKEN) { window.location.href = '/static/index.html'; }

/* ─── STATE ─── */
const state = {
    user: null, progress: null, agents: [],
    tasks: [], submissions: [], news: { hacking: [], ai: [] },
    powers: [], modules: [], ws: null, chatAgent: null,
    chatHistory: []
};

/* ─── UTILITY ─── */
async function api(url, opts = {}) {
    opts.headers = opts.headers || {};
    opts.headers['Authorization'] = `Bearer ${TOKEN}`;
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.body = JSON.stringify(opts.body);
        opts.headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'API Error');
    }
    return res.json();
}

function showLoading(el) { if (el) el.innerHTML = '<div class="loading-spinner"></div>'; }
function showError(el, msg) { if (el) el.innerHTML = `<div class="error-state"><div class="error-icon">&#9888;</div><div>${msg}</div><button class="retry-btn" onclick="location.reload()">Retry</button></div>`; }
function showEmpty(el, msg) { if (el) el.innerHTML = `<div class="empty-state"><div class="empty-icon">&#128123;</div><div>${msg || 'Nothing here yet.'}</div></div>`; }

function getFirstLetter(name) { return (name || 'S')[0].toUpperCase(); }

const RANKS = [
    { min: 1, max: 5, name: 'Shadow Initiate', color: '#5a6478', icon: '🟤' },
    { min: 6, max: 15, name: 'Cyber Scout', color: '#22c55e', icon: '🟢' },
    { min: 16, max: 30, name: 'Data Hunter', color: '#3b82f6', icon: '🔵' },
    { min: 31, max: 50, name: 'Code Assassin', color: '#7c3aed', icon: '🟣' },
    { min: 51, max: 70, name: 'System Breaker', color: '#ef4444', icon: '🔴' },
    { min: 71, max: 85, name: 'Ghost Operative', color: '#f97316', icon: '🟠' },
    { min: 86, max: 95, name: 'Phantom Elite', color: '#cbd5e1', icon: '⚪' },
    { min: 96, max: 100, name: 'Shadow Monarch', color: '#eab308', icon: '👑' },
];

function getRank(level) {
    for (const r of RANKS) {
        if (level >= r.min && level <= r.max) return r;
    }
    return RANKS[0];
}

/* ─── TABS ─── */
function switchTab(tab) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const navEl = document.querySelector(`.nav-item[data-tab="${tab}"]`);
    const panel = document.getElementById(`tab-${tab}`);
    if (navEl) navEl.classList.add('active');
    if (panel) panel.classList.add('active');

    const titles = { dashboard: ['Dashboard', 'Welcome back'], agents: ['Shadow Army', 'Your awakened agents'], tasks: ['Daily Quests', 'Complete tasks to earn XP'], modules: ['Security Modules', '10 AI-powered tools'], stats: ['Statistics', 'Your progression metrics'], powers: ['Powers', 'Unlockable abilities'], tutorials: ['Interactive Tutorials', 'Learn security tools step-by-step'], snippets: ['Code Snippets', 'Your exploit & tool library'], vulns: ['Vulnerability DB', 'CVE search & intelligence'], warroom: ['War Room', 'Red vs Blue cyber battle simulation'], news: ['News Feed', 'Latest from the underground'], settings: ['Settings', 'Configure your system'] };
    const t = titles[tab] || ['Dashboard', 'Welcome back'];
    document.getElementById('page-title').textContent = t[0];
    document.getElementById('page-subtitle').innerHTML = `${t[1]}, <span id="welcome-name">${state.user?.username || 'Hunter'}</span>`;

    // lazy load tab content
    if (tab === 'agents') renderAgentsTab();
    if (tab === 'tasks') renderTasksTab();
    if (tab === 'modules') renderModulesTab();
    if (tab === 'stats') renderStatsTab();
    if (tab === 'powers') renderPowersTab();
    if (tab === 'warroom') renderWarRoomTab();
    if (tab === 'news') renderNewsTab();
    if (tab === 'tutorials') renderTutorialsTab();
    if (tab === 'snippets') renderSnippetsTab();
    if (tab === 'vulns') renderVulnsTab();
    if (tab === 'settings') renderSettingsTab();
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
});
document.querySelectorAll('.view-all-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

/* ─── LOAD USER ─── */
async function loadUser() {
    try {
        const data = await api(`${API}/auth/me`);
        state.user = data.user;
        state.progress = data.progress;
        updateUI();
    } catch (e) {
        localStorage.clear();
        window.location.href = '/static/index.html';
    }
}

function updateUI() {
    const u = state.user;
    const p = state.progress;
    const username = u?.username || 'Shadow';
    const level = p?.overall_level || 1;
    const rank = getRank(level);
    const xp = p?.total_xp || 0;
    const xpNext = level * 500;

    document.getElementById('welcome-name').textContent = username;
    document.getElementById('display-username').textContent = username;
    document.getElementById('display-email').textContent = u?.email || `${username}@dark-x.dev`;
    const initial = getFirstLetter(username);
    document.getElementById('sidebar-avatar').textContent = initial;
    document.getElementById('header-avatar').textContent = initial;
    document.getElementById('display-rank').textContent = rank.name;
    document.getElementById('display-rank').style.color = rank.color;

    // stats row
    renderStatsRow(p);
}

/* ─── STATS ROW ─── */
function renderStatsRow(p) {
    const el = document.getElementById('stats-row');
    if (!el) return;
    const level = p?.overall_level || 1;
    const rank = getRank(level);
    const xp = p?.total_xp || 0;
    const unlocked = p?.powers_unlocked?.length || 0;
    const streak = p?.streak_days || 0;
    const tasksDone = p?.tasks_completed || 0;
    const xpPct = Math.min(100, Math.round((xp % (level * 500)) / (level * 500) * 100));

    el.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon blue"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-7 8-7s8 3 8 7"/></svg></div>
            <div class="stat-info">
                <div class="stat-label">Active Agents</div>
                <div class="stat-value"><span id="active-agents">15</span> / 15</div>
                <div class="stat-sub green">All systems operational</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon cyan"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg></div>
            <div class="stat-info">
                <div class="stat-label">Daily Tasks</div>
                <div class="stat-value"><span>${tasksDone}</span> / 12</div>
                <div class="stat-sub">${Math.round(tasksDone/12*100)}% completed</div>
                <div class="stat-progress"><div class="stat-progress-fill" style="width:${Math.min(100, tasksDone/12*100)}%"></div></div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon purple"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10"/></svg></div>
            <div class="stat-info">
                <div class="stat-label">Powers Unlocked</div>
                <div class="stat-value"><span>${unlocked}</span> / 100</div>
                <div class="stat-sub purple">${unlocked === 100 ? 'Mastered' : `${level} / 100 levels`}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon green"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 8l-4 4-4-4"/><path d="M12 12v6"/></svg></div>
            <div class="stat-info">
                <div class="stat-label">System Points</div>
                <div class="stat-value">${xp.toLocaleString()}</div>
                <div class="stat-sub green">Level ${level} &middot; ${xpPct}% to next</div>
            </div>
        </div>
        <div class="stat-card rank-card">
            <div class="stat-icon gold"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4.5L6 21l1.5-7.5L2 9h7z"/></svg></div>
            <div class="stat-info">
                <div class="stat-label">Rank</div>
                <div class="stat-value rank-title" style="color:${rank.color}">${rank.name}</div>
                <div class="stat-sub">Level ${level}</div>
                <div class="rank-progress"><div class="rank-progress-fill" style="width:${level}%"></div></div>
            </div>
        </div>
    `;
}

/* ─── DASHBOARD AGENTS ─── */
function renderDashboardAgents() {
    const el = document.getElementById('dashboard-agents');
    if (!el) return;
    const names = ['Blade','Shadow','Hunter','Sentry','Inferno','Specter','Null','Phantom','Assassin','Titan','Warlock','Ranger','Engineer','Summoner','Overlord'];
    const types = ['Assassin','Leader','Scout','Defense','Destroyer','Stealth','Support','Intel','Execution','Tank','Magic','Range','Tech','Special','Ultimate'];
    const gradients = ['t1','t2','t2','t3','t3','t1','t2','t1','t3','t4','t1','t2','t5','t1','t5'];
    el.innerHTML = names.slice(0, 9).map((n, i) => `
        <div class="agent-item" data-agent="${n.toLowerCase()}">
            <div class="agent-icon ${gradients[i]}">${n[0]}</div>
            <div>
                <div class="agent-name">${n}</div>
                <div class="agent-type">${types[i]} Type</div>
            </div>
            <div class="agent-status active"></div>
        </div>
    `).join('');
}

/* ─── LOAD TASKS ─── */
async function loadTasks() {
    try {
        const tasks = await api(`${API}/tasks/daily`);
        state.tasks = tasks || [];
    } catch (e) {
        state.tasks = [];
    }
}

/* ─── DASHBOARD TASKS ─── */
function renderDashboardTasks() {
    const el = document.getElementById('dashboard-tasks');
    if (!el) return;
    const tasks = state.tasks || [];
    const names = tasks.length > 0 ? tasks.map(t => t.title) : ['Complete Hacking Missions','Read Hacking News','Train Powers','System Scan','Online Challenge','Upgrade Agent'];
    const icons = ['&#128126;','&#128240;','&#9889;','&#128269;','&#127942;','&#11015;'];
    const colors = ['green','cyan','purple','cyan','gray','green'];
    const progress = tasks.length > 0 ? tasks.map((t, i) => Math.min(10, Math.ceil((i+1)*1.5))) : [7,1,2,1,0,1];
    const total = tasks.length > 0 ? tasks.map(t => 10) : [10,1,3,1,1,1];
    const xp = tasks.length > 0 ? tasks.map(t => t.xp_reward || 100) : [500,100,300,150,400,250];
    const count = Math.min(6, tasks.length || 6);
    el.innerHTML = names.slice(0, count).map((t, i) => {
        const pct = Math.round((progress[i]/total[i])*100);
        const done = progress[i] >= total[i];
        return `
        <div class="task-item">
            <div class="task-icon ${colors[i]}">${icons[i]}</div>
            <div class="task-info">
                <div class="task-title">${t}</div>
                <div class="task-progress"><div class="task-progress-fill ${colors[i]}" style="width:${pct}%"></div></div>
            </div>
            <div class="task-right">${done ? '<span class="task-check">&#10003;</span>' : `<span class="task-xp">XP ${xp[i]}</span>`}</div>
        </div>`;
    }).join('');
}

/* ─── DASHBOARD NEWS ─── */
function renderDashboardNews(items, id) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!items || items.length === 0) {
        el.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;padding:8px 0;">No news available</div>';
        return;
    }
    el.innerHTML = items.slice(0, 3).map(n => {
        const isCritical = n.priority === 'critical';
        return `
        <div class="news-item ${isCritical ? 'news-critical' : ''}">
            <div class="news-bullet ${isCritical ? 'critical' : ''}"></div>
            <div class="news-title ${isCritical ? 'critical-text' : ''}">${isCritical ? '🚨 ' : ''}${n.title}</div>
            <div class="news-time">${n.time || 'recent'}</div>
        </div>`;
    }).join('');
}

/* ─── POWER CHART ─── */
function renderPowerChart() {
    const canvas = document.getElementById('powerChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cx = 90, cy = 90, r = 70, lw = 14;
    const p = state.progress;
    const unlocked = p?.powers_unlocked?.length || 0;
    const pct = Math.min(1, unlocked / 100);
    const segments = [
        { pct: Math.min(0.25, pct * 0.35), color: '#7c3aed', label: 'Offensive' },
        { pct: Math.min(0.25, pct * 0.25), color: '#06b6d4', label: 'Defensive' },
        { pct: Math.min(0.25, pct * 0.25), color: '#22c55e', label: 'Support' },
        { pct: Math.min(0.25, pct * 0.15), color: '#eab308', label: 'Utility' },
    ];
    ctx.clearRect(0, 0, 180, 180);
    let start = -Math.PI / 2;
    segments.forEach(s => {
        const end = start + s.pct * Math.PI * 2;
        ctx.beginPath();
        ctx.arc(cx, cy, r, start, end);
        ctx.strokeStyle = s.color;
        ctx.lineWidth = lw;
        ctx.lineCap = 'butt';
        ctx.stroke();
        start = end;
    });
    // center circle
    ctx.beginPath();
    ctx.arc(cx, cy, r - lw - 2, 0, Math.PI * 2);
    ctx.fillStyle = '#13131f';
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${Math.round(pct * 100)}%`, cx, cy - 6);
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#8892a4';
    ctx.fillText('Powers', cx, cy + 14);

    const legend = document.getElementById('power-legend');
    if (legend) {
        legend.innerHTML = segments.map(s => `
            <div class="legend-item"><span class="legend-dot" style="background:${s.color}"></span> ${s.label} <span class="legend-val">${Math.round(s.pct * 400)}%</span></div>
        `).join('');
    }
}

/* ─── ACTIVITY CHART ─── */
function renderActivityChart() {
    const canvas = document.getElementById('activityChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.offsetWidth || canvas.parentElement.offsetWidth || 400;
    const h = 160;
    canvas.width = w;
    canvas.height = h;

    const day = new Date().getDay();
    const base = [30, 25, 50, 45, 55, 40, 65];
    const data = base.map((v, i) => Math.max(5, v + (i === day ? 10 : 0) + Math.floor(Math.random() * 10 - 5)));
    const labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const max = Math.max(...data) * 1.3;
    const px = w / (data.length - 1);
    const pad = 20;
    const chartH = h - pad * 2;

    ctx.clearRect(0, 0, w, h);

    // grid
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad + (chartH / 4) * i;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // gradient fill
    const gradient = ctx.createLinearGradient(0, pad, 0, h);
    gradient.addColorStop(0, 'rgba(124,58,237,0.3)');
    gradient.addColorStop(1, 'rgba(124,58,237,0)');
    ctx.beginPath();
    ctx.moveTo(0, h);
    data.forEach((v, i) => {
        const x = i * px;
        const y = pad + chartH * (1 - v / max);
        if (i === 0) ctx.lineTo(x, y);
        else {
            const prev = data[i - 1];
            const cpx = x - px / 2;
            ctx.bezierCurveTo(cpx, pad + chartH * (1 - prev / max), cpx, y, x, y);
        }
    });
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // line
    ctx.beginPath();
    data.forEach((v, i) => {
        const x = i * px;
        const y = pad + chartH * (1 - v / max);
        if (i === 0) ctx.moveTo(x, y);
        else {
            const prev = data[i - 1];
            const cpx = x - px / 2;
            ctx.bezierCurveTo(cpx, pad + chartH * (1 - prev / max), cpx, y, x, y);
        }
    });
    ctx.strokeStyle = '#7c3aed';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // dots & labels
    data.forEach((v, i) => {
        const x = i * px;
        const y = pad + chartH * (1 - v / max);
        ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#7c3aed'; ctx.fill();
        ctx.beginPath(); ctx.arc(x, y, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = '#fff'; ctx.fill();
        ctx.fillStyle = '#5a6478';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(labels[i], x, h - 4);
    });

    const total = data.reduce((a, b) => a + b, 0);
    const avg = Math.round(total / data.length);
    document.getElementById('activity-badge').textContent = `+${avg}%`;
}

/* ─── QUICK TOOLS ─── */
function renderQuickTools() {
    const el = document.getElementById('quick-tools');
    if (!el) return;
    const tools = [
        { name: 'Port Scanner', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>' },
        { name: 'HTTP Fuzzer', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>' },
        { name: 'SQLi Checker', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>' },
        { name: 'Hash Cracker', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>' },
        { name: 'Payload Gen', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>' },
        { name: 'Recon Tool', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' },
    ];
    el.innerHTML = tools.map(t => `
        <button class="tool-btn" onclick="switchTab('modules')">${t.icon} ${t.name}</button>
    `).join('');
}

/* ─── AGENTS TAB ─── */
function renderAgentsTab() {
    const el = document.getElementById('agents-full-grid');
    if (!el) return;
    const names = ['Blade','Shadow','Hunter','Sentry','Inferno','Specter','Null','Phantom','Assassin','Titan','Warlock','Ranger','Engineer','Summoner','Overlord'];
    const types = ['Assassin Type','Leader Type','Scout Type','Defense Type','Destroyer Type','Stealth Type','Support Type','Intelligence Type','Execution Type','Tank Type','Magic Type','Long Range Type','Tech Type','Special Type','Ultimate Type'];
    const descs = ['Precision strikes and surgical exploits','Commands the shadow army','Reconnaissance and target acquisition','Defensive countermeasures','Brute force and destruction','Stealth and infiltration','Data manipulation and analysis','Intelligence gathering','Target elimination','Immovable defense','Arcane and obscure techniques','Distance operations','Tool and script crafting','Entity summoning','Absolute command'];
    const gradients = ['t1','t2','t2','t3','t3','t1','t2','t1','t3','t4','t1','t2','t5','t1','t5'];
    el.innerHTML = names.map((n, i) => `
        <div class="agent-full-card" onclick="openAgentChat('${n.toLowerCase()}')">
            <div class="agent-full-header">
                <div class="agent-full-icon ${gradients[i]}">${n[0]}</div>
                <div class="agent-full-info">
                    <div class="agent-full-name">${n}</div>
                    <div class="agent-full-type">${types[i]}</div>
                </div>
                <div class="agent-full-status active" title="Active"></div>
            </div>
            <p class="agent-full-desc">${descs[i]}</p>
            <button class="agent-chat-btn" onclick="event.stopPropagation();openAgentChat('${n.toLowerCase()}')">&#128172; Chat</button>
        </div>
    `).join('');
}

function openAgentChat(name) {
    state.chatAgent = name;
    document.getElementById('chat-agent-name').textContent = name.charAt(0).toUpperCase() + name.slice(1);
    document.getElementById('agent-chat-panel').style.display = 'block';
    const box = document.getElementById('chat-box');
    box.innerHTML = `<div class="chat-msg agent-msg"><strong>${name.toUpperCase()}</strong>: I am awake. How may I assist?</div>`;
    document.getElementById('chat-input').focus();
}

document.getElementById('close-chat')?.addEventListener('click', () => {
    document.getElementById('agent-chat-panel').style.display = 'none';
    state.chatAgent = null;
});

document.getElementById('chat-send')?.addEventListener('click', sendChatMessage);
document.getElementById('chat-input')?.addEventListener('keydown', e => { if (e.key === 'Enter') sendChatMessage(); });

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || !state.chatAgent) return;
    input.value = '';
    const box = document.getElementById('chat-box');
    box.innerHTML += `<div class="chat-msg user-msg"><strong>You</strong>: ${msg}</div>`;
    box.innerHTML += `<div class="chat-msg agent-msg"><strong>${state.chatAgent.toUpperCase()}</strong>: <em>Processing...</em></div>`;
    box.scrollTop = box.scrollHeight;

    try {
        const res = await api(`${API}/agents/chat`, { method: 'POST', body: { agent: state.chatAgent, message: msg } });
        const lines = box.querySelectorAll('.chat-msg');
        const last = lines[lines.length - 1];
        if (last) last.innerHTML = `<strong>${state.chatAgent.toUpperCase()}</strong>: ${res.reply || res.response || 'Command received.'}`;
    } catch (e) {
        const lines = box.querySelectorAll('.chat-msg');
        const last = lines[lines.length - 1];
        if (last) last.innerHTML = `<strong>${state.chatAgent.toUpperCase()}</strong>: <span style="color:var(--accent-red)">Error: ${e.message}</span>`;
    }
    box.scrollTop = box.scrollHeight;
}

/* ─── TASKS TAB ─── */
function renderTasksTab() {
    const tracks = ['python', 'kali', 'ai', 'skill'];
    const trackNames = { python: 'Python Engineering', kali: 'Kali Linux Mastery', ai: 'AI & Machine Learning', skill: 'Industry Skill Upgrader' };
    const trackIcons = { python: '🐍', kali: '🐉', ai: '🧠', skill: '🚀' };
    const colors = ['purple', 'cyan', 'green', 'gold'];

    const tasksByTrack = {};
    (state.tasks || []).forEach(t => {
        if (!tasksByTrack[t.track]) tasksByTrack[t.track] = [];
        tasksByTrack[t.track].push(t);
    });

    tracks.forEach((track, ti) => {
        const el = document.getElementById(`track-${track}`);
        if (!el) return;
        const trackTasks = tasksByTrack[track] || [];
        const total = document.getElementById(`track-total-${track}`);
        const count = document.getElementById(`track-count-${track}`);
        if (total) total.textContent = trackTasks.length || 1;
        if (count) {
            const done = trackTasks.filter(t => t.completed).length || 0;
            count.textContent = done;
        }

        if (trackTasks.length === 0) {
            el.innerHTML = `<div class="track-task-card" style="border-left:3px solid var(--accent-${colors[ti]});opacity:0.6;">
                <div class="track-task-desc" style="padding:12px;">No tasks available. Generate new tasks from the API.</div>
            </div>`;
            return;
        }

        el.innerHTML = trackTasks.map((task, i) => `
            <div class="track-task-card" onclick="openTaskDetail(${task.id || i})" style="border-left:3px solid var(--accent-${colors[ti]});">
                <div class="track-task-header">
                    <span class="task-diff ${colors[ti]}">${task.difficulty || 'Intermediate'}</span>
                    <span class="task-xp-badge">+${task.xp_reward || 100} XP</span>
                    ${task.is_random_event ? '<span class="task-xp-badge" style="background:var(--accent-gold);color:#000;">⚡ EVENT</span>' : ''}
                </div>
                <div class="track-task-title">${task.title || 'Security Challenge'}</div>
                <div class="track-task-desc">${(task.description || task.full_question || '').substring(0, 100)}${(task.description || task.full_question || '').length > 100 ? '...' : ''}</div>
                <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;">
                    <span style="font-size:0.7rem;color:var(--text-muted);">⏱ ${task.time_estimate || '30 min'}</span>
                    <span style="font-size:0.7rem;color:var(--text-muted);">📊 ${task.ease_rating || 'Medium'}</span>
                    ${(task.tags || []).slice(0, 3).map(t => `<span style="font-size:0.65rem;padding:1px 6px;background:rgba(124,58,237,0.15);border-radius:8px;color:var(--accent-purple);">${t}</span>`).join('')}
                </div>
            </div>
        `).join('');
    });
}

function openTaskDetail(taskId) {
    const panel = document.getElementById('task-detail-panel');
    panel.style.display = 'block';
    const task = (state.tasks || []).find(t => t.id === taskId) || state.tasks[0] || {};
    document.getElementById('task-detail-title').textContent = task.title || 'Security Challenge';
    document.getElementById('task-detail-body').innerHTML = `
        <div style="padding:16px 0;">
            <h3 style="color:#fff;margin-bottom:8px;">${task.title || 'Security Challenge'}</h3>
            <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
                <span style="font-size:0.75rem;color:var(--text-muted);background:rgba(124,58,237,0.1);padding:2px 10px;border-radius:12px;">🎯 ${task.difficulty || 'Intermediate'}</span>
                <span style="font-size:0.75rem;color:var(--text-muted);background:rgba(34,197,94,0.1);padding:2px 10px;border-radius:12px;">+${task.xp_reward || 100} XP</span>
                <span style="font-size:0.75rem;color:var(--text-muted);background:rgba(6,182,212,0.1);padding:2px 10px;border-radius:12px;">⏱ ${task.time_estimate || '30 min'}</span>
            </div>
            <p style="color:var(--text-secondary);margin-bottom:16px;line-height:1.6;">${task.full_question || task.description || 'Complete this challenge.'}</p>
            ${task.what_wanted ? `<div style="background:rgba(124,58,237,0.08);border-left:2px solid var(--accent-purple);padding:10px 14px;margin-bottom:16px;border-radius:4px;">
                <div style="font-size:0.75rem;color:var(--accent-purple);font-weight:600;margin-bottom:4px;">WHAT WE WANT</div>
                <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.5;">${task.what_wanted}</div>
            </div>` : ''}
            ${task.what_we_learn ? `<div style="margin-bottom:16px;">
                <div style="font-size:0.75rem;color:var(--text-muted);font-weight:600;margin-bottom:4px;">SKILLS YOU WILL LEARN</div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;">${task.what_we_learn.split(',').map(s => `<span style="font-size:0.7rem;padding:2px 8px;background:rgba(34,197,94,0.1);color:var(--accent-green);border-radius:8px;">${s.trim()}</span>`).join('')}</div>
            </div>` : ''}
            <div style="margin-bottom:16px;">
                <label style="display:block;font-size:0.85rem;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">Your Solution</label>
                <textarea class="code-editor" id="task-code-input" rows="10" placeholder="Write your code or solution here..." style="width:100%;padding:14px;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);font-family:'Courier New',monospace;font-size:0.82rem;resize:vertical;outline:none;"></textarea>
            </div>
            <button class="settings-save" onclick="submitTask(${task.id || 1})">Submit for Grading</button>
            <div id="task-result" style="margin-top:16px;display:none;"></div>
        </div>
    `;
}

async function submitTask(taskId) {
    const code = document.getElementById('task-code-input').value;
    if (!code.trim()) return;
    const resultEl = document.getElementById('task-result');
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div class="loading-spinner"></div>';
    try {
        const res = await api(`${API}/tasks/submit`, { method: 'POST', body: { task_id: taskId, code } });
        resultEl.innerHTML = `
            <div style="padding:16px;background:var(--bg-input);border-radius:var(--radius-sm);border:1px solid var(--border);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <span style="font-weight:700;font-size:1.1rem;">Score: ${res.score || 85}/100</span>
                    <span style="color:var(--accent-green);font-weight:700;">+${res.xp_earned || 100} XP</span>
                </div>
                <div style="color:var(--text-secondary);font-size:0.85rem;line-height:1.6;">${res.feedback || 'Good work! Your solution is correct.'}</div>
                ${res.leveled_up ? '<div style="margin-top:12px;padding:8px 12px;background:rgba(124,58,237,0.2);border-radius:var(--radius-sm);text-align:center;font-weight:700;color:var(--accent-purple);">⬆ LEVEL UP! You reached level ' + res.new_level + '</div>' : ''}
            </div>
        `;
        if (res.new_power) {
            triggerLevelUp(res.new_level, res.new_power);
        }
        // Reload user progress
        loadUser();
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--accent-red);">Error: ${e.message}</div>`;
    }
}

document.getElementById('close-task-detail')?.addEventListener('click', () => {
    document.getElementById('task-detail-panel').style.display = 'none';
});

/* ─── MODULES TAB ─── */
let currentToolId = null;
let currentToolOptions = {};

function renderModulesTab() {
    loadModulesList();
    setupModuleViewSwitcher();
}

async function loadModulesList() {
    const el = document.getElementById('modules-full-grid');
    if (!el) return;
    showLoading(el);
    try {
        const tools = await api(`${API}/modules/list`);
        const aiStatus = document.getElementById('module-ai-status-text');
        if (aiStatus) aiStatus.textContent = tools.length > 0 ? 'Online' : 'Limited';

        el.innerHTML = tools.map(t => `
            <div class="module-card" onclick="openToolWorkspace('${t.id}')" style="border-left:3px solid ${t.color};">
                <div class="module-card-header">
                    <span class="module-card-icon">${t.icon || '🔧'}</span>
                    <span class="module-card-name">${t.name}</span>
                </div>
                <p class="module-card-desc">${t.desc}</p>
                <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
                    <span style="font-size:0.6rem;padding:1px 6px;background:rgba(124,58,237,0.12);border-radius:6px;color:var(--text-muted);">${t.options_count || 0} options</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        showError(el, 'Failed to load modules. ' + e.message);
    }
}

function setupModuleViewSwitcher() {
    document.querySelectorAll('.modules-view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.modules-view-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const view = this.dataset.view;
            document.getElementById('modules-tools-view').style.display = view === 'tools' ? '' : 'none';
            document.getElementById('modules-workspace-view').style.display = view === 'workspace' ? '' : 'none';
            document.getElementById('modules-history-view').style.display = view === 'history' ? '' : 'none';
            if (view === 'history') loadModuleHistory();
            if (view === 'workspace' && currentToolId) loadToolOptions(currentToolId);
        });
    });
    document.getElementById('workspace-close')?.addEventListener('click', () => {
        currentToolId = null;
        document.querySelector('[data-view="tools"]')?.click();
    });
    document.getElementById('workspace-run-all')?.addEventListener('click', runWorkspaceTool);
    document.getElementById('refresh-history')?.addEventListener('click', loadModuleHistory);
}

async function openToolWorkspace(toolId) {
    currentToolId = toolId;
    document.querySelector('[data-view="workspace"]')?.click();
    await loadToolOptions(toolId);
}

async function loadToolOptions(toolId) {
    const container = document.getElementById('workspace-options');
    const terminal = document.getElementById('workspace-terminal');
    const analysis = document.getElementById('workspace-analysis');
    const nameEl = document.getElementById('workspace-tool-name');
    if (!container) return;

    analysis.style.display = 'none';
    terminal.innerHTML = '<span style="color:var(--text-muted);">Loading tool configuration...</span>';

    try {
        const tool = await api(`${API}/modules/${toolId}/options`);
        nameEl.textContent = `${tool.icon || '🔧'} ${tool.name}`;
        currentToolOptions = {};

        container.innerHTML = `
            <div class="tool-options-form">
                <div class="tool-desc" style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:14px;line-height:1.5;">${tool.desc}</div>
                ${Object.entries(tool.options || {}).map(([key, opt]) => {
                    const val = opt.default || '';
                    currentToolOptions[key] = val;
                    if (opt.type === 'text') {
                        return `<div class="mod-option">
                            <label class="mod-option-label">${opt.label}${opt.required ? ' <span style="color:var(--accent-red);">*</span>' : ''}</label>
                            <input type="text" class="mod-option-input" data-key="${key}" value="${val}" placeholder="${opt.placeholder || ''}">
                        </div>`;
                    } else if (opt.type === 'select') {
                        return `<div class="mod-option">
                            <label class="mod-option-label">${opt.label}</label>
                            <select class="mod-option-select" data-key="${key}">
                                ${(opt.options || []).map(o => `<option value="${o}" ${o === val ? 'selected' : ''}>${o}</option>`).join('')}
                            </select>
                        </div>`;
                    } else if (opt.type === 'checkbox') {
                        return `<div class="mod-option mod-option-inline">
                            <label class="mod-option-label">
                                <input type="checkbox" class="mod-option-checkbox" data-key="${key}" ${val ? 'checked' : ''}>
                                ${opt.label}
                            </label>
                        </div>`;
                    } else if (opt.type === 'range') {
                        return `<div class="mod-option">
                            <label class="mod-option-label">${opt.label}: <span class="range-val" id="range-${key}">${val}</span></label>
                            <input type="range" class="mod-option-range" data-key="${key}" min="${opt.min}" max="${opt.max}" value="${val}" oninput="document.getElementById('range-${key}').textContent=this.value">
                        </div>`;
                    }
                    return '';
                }).join('')}
                <button class="settings-save" onclick="runWorkspaceTool()" style="margin-top:12px;width:100%;padding:10px;">▶ Run ${tool.name}</button>
            </div>
        `;

        // Bind input changes to collect values
        container.querySelectorAll('input[data-key], select[data-key]').forEach(el => {
            el.addEventListener('change', () => collectToolOptions());
            el.addEventListener('input', () => collectToolOptions());
        });

        terminal.innerHTML = '<span style="color:var(--text-muted);">Configure options above and click Run to execute.</span>';
    } catch (e) {
        container.innerHTML = `<div class="error-state">Failed to load tool: ${e.message}</div>`;
    }
}

function collectToolOptions() {
    const options = {};
    document.querySelectorAll('.mod-option-input').forEach(el => options[el.dataset.key] = el.value);
    document.querySelectorAll('.mod-option-select').forEach(el => options[el.dataset.key] = el.value);
    document.querySelectorAll('.mod-option-checkbox').forEach(el => options[el.dataset.key] = el.checked);
    document.querySelectorAll('.mod-option-range').forEach(el => options[el.dataset.key] = parseInt(el.value));
    currentToolOptions = options;
    return options;
}

async function runWorkspaceTool() {
    if (!currentToolId) return;
    const terminal = document.getElementById('workspace-terminal');
    const analysis = document.getElementById('workspace-analysis');
    const timer = document.getElementById('workspace-timer');
    if (!terminal) return;

    const options = collectToolOptions();
    const target = options['target'] || '';
    if (!target) {
        terminal.innerHTML = '<span style="color:var(--accent-red);">Error: Target is required.</span>';
        return;
    }

    analysis.style.display = 'none';
    terminal.innerHTML = '<div class="loading-spinner"></div>';
    timer.textContent = 'Running...';

    const startTime = Date.now();
    try {
        const body = { target, ...options };
        delete body['target'];
        const res = await api(`${API}/modules/${currentToolId}/run`, { method: 'POST', body: { target, ...body } });
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        timer.textContent = `Completed in ${elapsed}s`;

        terminal.innerHTML = '';
        const lines = (res.output || 'No output').split('\n');
        lines.forEach((line, i) => {
            setTimeout(() => {
                const div = document.createElement('div');
                div.textContent = line;
                div.style.opacity = '0';
                div.style.transition = 'opacity 0.15s';
                terminal.appendChild(div);
                requestAnimationFrame(() => div.style.opacity = '1');
                terminal.scrollTop = terminal.scrollHeight;
            }, i * 30);
        });

        if (res.analysis && res.analysis.findings) {
            analysis.style.display = 'block';
            const a = res.analysis;
            const riskColors = { 'Critical': 'var(--accent-red)', 'High': '#ff6b35', 'Medium': 'var(--accent-gold)', 'Low': 'var(--accent-green)' };
            analysis.innerHTML = `
                <div class="analysis-header">AI Analysis</div>
                <div class="analysis-score">
                    <div class="score-ring" style="border-color:${a.score > 70 ? 'var(--accent-green)' : a.score > 40 ? 'var(--accent-gold)' : 'var(--accent-red)'}">
                        <span class="score-value">${a.score || '?'}</span>
                        <span class="score-label">Score</span>
                    </div>
                    <div class="score-details">
                        <div class="score-risk" style="color:${riskColors[a.risk_level] || 'var(--text-secondary)'}">Risk: ${a.risk_level || 'Unknown'}</div>
                        <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:4px;">${a.risk_reasoning || ''}</div>
                    </div>
                </div>
                <div class="analysis-findings">
                    <div class="analysis-section-title">Key Findings</div>
                    <ul>${(a.findings || []).map(f => `<li>${f}</li>`).join('')}</ul>
                </div>
                ${a.recommendations ? `
                <div class="analysis-recommendations">
                    <div class="analysis-section-title">Recommendations</div>
                    <ol>${a.recommendations.map(r => `<li>${r}</li>`).join('')}</ol>
                </div>` : ''}
            `;
        }
    } catch (e) {
        terminal.innerHTML = `<span style="color:var(--accent-red);">Error: ${e.message}</span>`;
        timer.textContent = 'Failed';
    }
}

async function loadModuleHistory() {
    const el = document.getElementById('module-history-list');
    if (!el) return;
    showLoading(el);
    try {
        const history = await api(`${API}/modules/history?limit=30`);
        if (!history || history.length === 0) {
            showEmpty(el, 'No module runs yet. Execute a tool to see history here.');
            return;
        }
        const toolNames = { network_scanner: 'Port Scanner', fuzzer: 'HTTP Fuzzer', sqli_checker: 'SQLi Checker', hash_cracker: 'Hash Cracker', payload_gen: 'Payload Gen', subdomain_finder: 'Subdomain Finder', network_mapper: 'Network Mapper', dns_analyzer: 'DNS Analyzer', ssl_checker: 'SSL Checker', whois_lookup: 'Whois Lookup' };
        el.innerHTML = history.map(r => `
            <div class="history-item" onclick="openToolWorkspace('${r.module_id}')">
                <div class="history-icon" style="color:${r.score > 70 ? 'var(--accent-green)' : r.score > 40 ? 'var(--accent-gold)' : 'var(--accent-red)'}">${toolNames[r.module_id] || r.module_id}</div>
                <div class="history-info">
                    <div class="history-target">${r.target}</div>
                    <div class="history-meta">${r.created_at ? new Date(r.created_at).toLocaleString() : 'recent'} · ${(r.duration_ms / 1000).toFixed(1)}s · Score: ${r.score}</div>
                </div>
                <div class="history-status ${r.status}">${r.status}</div>
            </div>
        `).join('');
    } catch (e) {
        showError(el, 'Failed to load history');
    }
}

/* ─── STATS TAB ─── */
function renderStatsTab() {
    const p = state.progress;
    const level = p?.overall_level || 1;
    const rank = getRank(level);
    const xp = p?.total_xp || 0;
    const xpNext = level * 500;
    const xpPct = Math.min(100, Math.round((xp % xpNext) / xpNext * 100));

    document.getElementById('stats-level').textContent = level;
    document.getElementById('stats-rank').textContent = rank.name;
    document.getElementById('stats-rank').style.color = rank.color;
    document.getElementById('stats-xp-fill').style.width = xpPct + '%';
    document.getElementById('stats-xp').textContent = (xp % xpNext).toLocaleString();
    document.getElementById('stats-xp-next').textContent = xpNext.toLocaleString();
    document.getElementById('stat-tasks-done').textContent = p?.tasks_completed || 0;
    document.getElementById('stat-total-xp').textContent = xp.toLocaleString();
    document.getElementById('stat-streak').textContent = p?.streak_days || 0;
    document.getElementById('stat-powers').textContent = p?.powers_unlocked?.length || 0;

    // skill bars
    const el = document.getElementById('skill-bars');
    if (el) {
        el.innerHTML = [
            { name: 'Overall', level, xp, color: '#7c3aed' },
            { name: 'Python', level: p?.python_level || 1, xp: p?.python_xp || 0, color: '#3b82f6' },
            { name: 'Kali Linux', level: p?.kali_level || 1, xp: p?.kali_xp || 0, color: '#22c55e' },
            { name: 'AI', level: p?.ai_level || 1, xp: p?.ai_xp || 0, color: '#06b6d4' },
        ].map(s => {
            const pct = Math.min(100, Math.round((s.xp % (s.level * 500)) / (s.level * 500) * 100));
            return `
            <div class="skill-bar-item">
                <div class="skill-bar-header"><span>${s.name}</span><span>Level ${s.level}</span></div>
                <div class="skill-bar-track"><div class="skill-bar-fill" style="width:${pct}%;background:${s.color}"></div></div>
            </div>`;
        }).join('');
    }
}

/* ─── POWERS TAB ─── */
function renderPowersTab() {
    const el = document.getElementById('powers-grid');
    if (!el) return;
    const p = state.progress;
    const unlocked = p?.powers_unlocked || [];
    const level = p?.overall_level || 1;

    const allPowers = [
        'Shadow Sight','Echo Memory','Binary Whisper','Ghost Ping','Data Leech','Neon Aura','Dual Cast','Void Walker','Cipher Eye','Neural Link',
        'Time Freeze','Shadow Clone','Electric Storm','Iron Code','Mind Read','Stealth Mode','Quantum Leap','Dragon Eye','Shadow Army','Omega Compile',
        'Dark Sight','Phantom Step','Venom Strike','Arcane Shield','Net Surge','Crystal Wall','Storm Call','Blade Dance','Soul Harvest','Void Gate',
        'Thunder Clap','Mirage Walk','Bone Spear','Shadow Step','Plasma Bolt','Iron Will','Frost Nova','Inferno Blast','Chain Lightning','Time Distortion',
        'Gravity Well','Astral Projection','Phantom Slash','Demon Fang','Sacred Barrier','Lightning Rod','Dark Matter','Rage Mode','Soul Steal','Mana Burst',
        'Shadow Bind','Crimson Edge','Void Strike','Titan Guard','Storm Shield','Echo Location','Phantom Pain','Shadow Weave','Dark Pulse','Vortex Shield',
        'Soul Barrier','Blade Storm','Shadow Dance','Nether Ward','Crystal Shield','Phantom Guard','Void Armor','Lightning Field','Storm Ward','Flame Shield',
        'Ice Barrier','Venom Shield','Arcane Ward','Shadow Resistance','Dark Fortitude','Mana Shield','Soul Armor','Dragon Scale','Demon Hide','Angel Wing',
        'Phoenix Down','Shadow Mend','Void Heal','Dark Regen','Soul Drain','Life Steal','Blood Pact','Sacrifice','Revival','Reincarnation',
        'Shadow Lord','Void Emperor','Storm King','Blade Master','Phantom Lord','Dark Overlord','Soul King','Dragon Lord','Demon King','Archangel'
    ];

    document.getElementById('powers-counter').textContent = `${unlocked.length} / ${allPowers.length}`;

    el.innerHTML = allPowers.map((pow, i) => {
        const lvl = i + 1;
        const isUnlocked = level >= lvl;
        return `
        <div class="power-card ${isUnlocked ? 'unlocked' : 'locked'}">
            <div class="power-icon">${isUnlocked ? '&#9889;' : '&#128274;'}</div>
            <div class="power-name">${pow}</div>
            <div class="power-level">Lv. ${lvl}</div>
            ${!isUnlocked ? '<div class="power-lock">&#128274;</div>' : ''}
        </div>`;
    }).join('');
}

/* ─── NEWS TAB ─── */
async function renderNewsTab() {
    const el = document.getElementById('news-full-list');
    if (!el) return;
    showLoading(el);
    try {
        const [hacking, ai] = await Promise.all([
            api(`${API}/news/hacking`).catch(() => ({ articles: [] })),
            api(`${API}/news/ai`).catch(() => ({ articles: [] }))
        ]);
        state.news.hacking = (hacking.articles || []).map(a => ({ ...a, cat: 'hacking' }));
        state.news.ai = (ai.articles || []).map(a => ({ ...a, cat: 'ai' }));
        renderNewsFiltered('all');
    } catch (e) {
        showError(el, 'Failed to load news');
    }
}

function renderNewsFiltered(category) {
    const el = document.getElementById('news-full-list');
    if (!el) return;
    let items = [];
    if (category === 'all' || category === 'hacking') items = items.concat(state.news.hacking);
    if (category === 'all' || category === 'ai') items = items.concat(state.news.ai);

    if (items.length === 0) { showEmpty(el, 'No news articles'); return; }

    // Sort: critical first, then important, then normal
    const priorityOrder = { critical: 0, important: 1, normal: 2 };
    items.sort((a, b) => (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2));

    el.innerHTML = items.map(n => {
        const isCritical = n.priority === 'critical';
        return `
        <div class="news-full-item ${isCritical ? 'news-critical' : ''}">
            <span class="news-cat-badge ${n.cat}">${n.cat === 'hacking' ? 'HACK' : 'AI'}</span>
            <div class="news-full-content">
                <div class="news-full-title ${isCritical ? 'critical-text' : ''}">
                    ${isCritical ? '🚨 ' : ''}${n.priority === 'important' ? '⚠ ' : ''}${n.title}
                    ${n.priority === 'critical' ? '<span class="critical-badge">CRITICAL</span>' : ''}
                    ${n.priority === 'important' ? '<span class="important-badge">IMPORTANT</span>' : ''}
                </div>
                <div class="news-full-meta">${n.source || 'Unknown'} &middot; ${n.time || 'recent'}</div>
                <div class="news-full-summary">${n.summary || ''}</div>
            </div>
        </div>`;
    }).join('');
}

document.querySelectorAll('.news-filter').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.news-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderNewsFiltered(btn.dataset.category);
    });
});

/* ─── SETTINGS TAB ─── */
function renderSettingsTab() {
    const u = state.user;
    if (u?.settings?.api_keys) {
        if (document.getElementById('set-openai')) document.getElementById('set-openai').value = u.settings.api_keys.openai || '';
        if (document.getElementById('set-gemini')) document.getElementById('set-gemini').value = u.settings.api_keys.gemini || '';
    }
    if (document.getElementById('set-username')) document.getElementById('set-username').value = u?.username || '';
    if (document.getElementById('set-email')) document.getElementById('set-email').value = u?.email || '';
    loadProviders();
    loadAgentPersonalities();
}

document.getElementById('save-api-keys')?.addEventListener('click', async () => {
    const openai = document.getElementById('set-openai')?.value || '';
    const gemini = document.getElementById('set-gemini')?.value || '';
    try {
        await api(`${API}/auth/settings`, { method: 'PUT', body: { api_keys: { openai, gemini } } });
        showToast('API keys saved successfully');
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
});

document.getElementById('save-profile')?.addEventListener('click', async () => {
    // profile save
    showToast('Profile updated');
});

document.getElementById('export-pdf')?.addEventListener('click', async () => {
    window.open(`${API}/export/report/pdf?token=${TOKEN}`, '_blank');
});

document.getElementById('export-json')?.addEventListener('click', async () => {
    try {
        const data = await api(`${API}/export/backup/json`);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'dark-x-backup.json'; a.click();
        URL.revokeObjectURL(url);
        showToast('JSON backup downloaded');
    } catch (e) {
        showToast('Export failed: ' + e.message, 'error');
    }
});

document.getElementById('reset-progress')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset all progress? This cannot be undone.')) return;
    try {
        await api(`${API}/gamification/reset`, { method: 'POST' });
        showToast('Progress reset');
        location.reload();
    } catch (e) {
        showToast('Reset failed: ' + e.message, 'error');
    }
});

/* ─── TOAST ─── */
function showToast(msg, type = 'success') {
    let t = document.querySelector('.toast');
    if (!t) {
        t = document.createElement('div');
        t.className = 'toast';
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.className = 'toast ' + type;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
}

/* ─── LOGOUT ─── */
document.getElementById('logout-btn')?.addEventListener('click', async () => {
    try { await api(`${API}/auth/logout`, { method: 'POST' }); } catch (e) {}
    localStorage.clear();
    window.location.href = '/static/index.html';
});

/* ─── SEARCH ─── */
document.getElementById('global-search')?.addEventListener('input', function() {
    const q = this.value.toLowerCase().trim();
    if (!q) { document.querySelectorAll('.agent-full-card').forEach(c => c.style.display = ''); return; }
    document.querySelectorAll('.agent-full-card').forEach(c => {
        const name = c.querySelector('.agent-full-name')?.textContent?.toLowerCase() || '';
        c.style.display = name.includes(q) ? '' : 'none';
    });
});

/* ─── LEVEL UP OVERLAY ─── */
function triggerLevelUp(newLevel, powerName) {
    const overlay = document.getElementById('level-up-overlay');
    if (!overlay) return;
    document.getElementById('level-up-detail').textContent = `Level ${newLevel}`;
    document.getElementById('level-up-power').textContent = powerName ? `New Power: ${powerName}` : '';
    overlay.classList.add('show');
    setTimeout(() => overlay.classList.remove('show'), 3500);
}

document.getElementById('level-up-overlay')?.addEventListener('click', function() {
    this.classList.remove('show');
});

/* ─── THEME TOGGLE ─── */
document.getElementById('theme-toggle')?.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
});

/* ─── TUTORIALS TAB ─── */
async function renderTutorialsTab() {
    const grid = document.getElementById('tutorials-grid');
    if (!grid) return;
    showLoading(grid);
    try {
        const tutorials = await api(`${API}/tutorials/list`);
        grid.innerHTML = tutorials.map(t => `
            <div class="tutorial-card" onclick="openTutorial(${t.id})">
                <div class="tutorial-icon">${t.icon || '📚'}</div>
                <div class="tutorial-info">
                    <div class="tutorial-title">${t.title}</div>
                    <div class="tutorial-meta">${t.difficulty} · ${t.steps_count} steps · ${t.xp_reward} XP</div>
                    <div class="tutorial-desc">${t.description}</div>
                    <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap;">
                        ${(t.tags || []).slice(0, 3).map(tag => `<span class="tutorial-tag">${tag}</span>`).join('')}
                    </div>
                </div>
                <div class="tutorial-status ${t.completed ? 'done' : ''}">${t.completed ? '✓ Completed' : `${((t.current_step || 0) / t.steps_count * 100).toFixed(0)}%`}</div>
            </div>
        `).join('');
    } catch (e) {
        showError(grid, 'Failed to load tutorials');
    }
}

async function openTutorial(id) {
    const panel = document.getElementById('tutorial-detail-panel');
    const body = document.getElementById('tutorial-detail-body');
    const title = document.getElementById('tutorial-detail-title');
    panel.style.display = 'block';
    body.innerHTML = '<div class="loading-spinner"></div>';
    try {
        const data = await api(`${API}/tutorials/${id}`);document.querySelector('.vtl')?.setAttribute('content','');
        const t = data.tutorial;
        const p = data.progress;
        title.textContent = `${t.icon} ${t.title}`;
        const step = p.current_step || 0;
        const isComplete = p.completed;
        body.innerHTML = `
            <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
                <span class="tutorial-tag" style="background:rgba(124,58,237,0.15);color:var(--accent-purple);padding:3px 10px;">${t.difficulty}</span>
                <span class="tutorial-tag" style="background:rgba(34,197,94,0.15);color:var(--accent-green);padding:3px 10px;">${t.xp_reward} XP</span>
                <span class="tutorial-tag" style="background:rgba(6,182,212,0.15);color:var(--accent-cyan);padding:3px 10px;">${t.steps.length} steps</span>
            </div>
            <div class="tutorial-progress-bar"><div class="tutorial-progress-fill" style="width:${isComplete ? 100 : (step / t.steps.length * 100)}%"></div></div>
            <div class="tutorial-progress-text">${isComplete ? 'Complete!' : `Step ${Math.min(step + 1, t.steps.length)} of ${t.steps.length}`}</div>
            ${t.steps.map((s, i) => `
                <div class="tutorial-step ${i < step ? 'done' : i === step && !isComplete ? 'active' : ''}">
                    <div class="step-number">${i < step ? '✓' : i + 1}</div>
                    <div class="step-content">
                        <div class="step-title">${s.title}</div>
                        <div class="step-instruction">${s.instruction}</div>
                        ${s.command ? `<div class="step-command"><span class="step-prompt">$</span> ${s.command}</div>` : ''}
                        ${s.expected ? `<div class="step-expected">Expected: ${s.expected}</div>` : ''}
                    </div>
                </div>
            `).join('')}
            ${!isComplete && step < t.steps.length ? `<button class="settings-save" onclick="advanceTutorial(${id})" style="margin-top:16px;width:100%;">Complete Step ${step + 1} & Continue</button>` : ''}
            ${isComplete ? '<div style="margin-top:16px;padding:12px;background:rgba(34,197,94,0.1);border-radius:var(--radius-sm);text-align:center;color:var(--accent-green);font-weight:700;">✓ Tutorial Complete! +' + t.xp_reward + ' XP earned</div>' : ''}
        `;
    } catch (e) {
        body.innerHTML = `<div class="error-state">Error: ${e.message}</div>`;
    }
}

async function advanceTutorial(id) {
    try {
        await api(`${API}/tutorials/${id}/step`, { method: 'POST', body: {} });
        openTutorial(id);
        loadUser();
        showToast('Step completed!');
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

document.getElementById('close-tutorial')?.addEventListener('click', () => {
    document.getElementById('tutorial-detail-panel').style.display = 'none';
});

/* ─── SNIPPETS TAB ─── */
async function renderSnippetsTab() {
    const grid = document.getElementById('snippets-grid');
    if (!grid) return;
    showLoading(grid);
    try {
        const snippets = await api(`${API}/snippets/list`);
        grid.innerHTML = snippets.map(s => `
            <div class="snippet-card" onclick="openSnippet(${s.id})">
                <div class="snippet-lang ${s.language}">${s.language}</div>
                <div class="snippet-card-title">${s.title}</div>
                <div class="snippet-card-desc">${s.description || ''}</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;">${(s.tags || []).map(t => `<span class="tutorial-tag">${t}</span>`).join('')}</div>
            </div>
        `).join('');
        document.getElementById('snippet-search')?.addEventListener('input', function() {
            const q = this.value.toLowerCase();
            document.querySelectorAll('.snippet-card').forEach(c => {
                const text = c.textContent.toLowerCase();
                c.style.display = text.includes(q) ? '' : 'none';
            });
        });
    } catch (e) {
        showError(grid, 'Failed to load snippets');
    }
}

async function openSnippet(id) {
    const panel = document.getElementById('snippet-detail-panel');
    const body = document.getElementById('snippet-detail-body');
    const title = document.getElementById('snippet-detail-title');
    panel.style.display = 'block';
    body.innerHTML = '<div class="loading-spinner"></div>';
    try {
        const s = await api(`${API}/snippets/${id}`);
        title.textContent = s.title;
        body.innerHTML = `
            <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
                <span class="tutorial-tag" style="background:rgba(124,58,237,0.15);color:var(--accent-purple);">${s.language}</span>
                ${(s.tags || []).map(t => `<span class="tutorial-tag">${t}</span>`).join('')}
            </div>
            ${s.description ? `<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">${s.description}</p>` : ''}
            <pre class="snippet-code" id="snippet-code-block"><code>${s.code}</code></pre>
            <button class="settings-save" onclick="copySnippetCode()" style="margin-top:8px;">📋 Copy Code</button>
        `;
    } catch (e) {
        body.innerHTML = `<div class="error-state">Error: ${e.message}</div>`;
    }
}

function copySnippetCode() {
    const block = document.getElementById('snippet-code-block');
    if (!block) return;
    navigator.clipboard.writeText(block.textContent).then(() => {
        showToast('Code copied to clipboard');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

document.getElementById('close-snippet')?.addEventListener('click', () => {
    document.getElementById('snippet-detail-panel').style.display = 'none';
});

document.getElementById('add-snippet-btn')?.addEventListener('click', () => {
    const body = document.getElementById('snippet-detail-body');
    document.getElementById('snippet-detail-panel').style.display = 'block';
    document.getElementById('snippet-detail-title').textContent = 'New Snippet';
    body.innerHTML = `
        <div class="snippet-add-form">
            <div class="mod-option"><label class="mod-option-label">Title</label><input type="text" class="mod-option-input" id="new-snippet-title" placeholder="My Snippet"></div>
            <div class="mod-option"><label class="mod-option-label">Description</label><input type="text" class="mod-option-input" id="new-snippet-desc" placeholder="What does this do?"></div>
            <div class="mod-option"><label class="mod-option-label">Language</label>
                <select class="mod-option-select" id="new-snippet-lang">
                    <option value="python">Python</option><option value="bash">Bash</option><option value="php">PHP</option>
                    <option value="javascript">JavaScript</option><option value="powershell">PowerShell</option><option value="go">Go</option>
                </select>
            </div>
            <div class="mod-option"><label class="mod-option-label">Code</label>
                <textarea class="mod-option-input" id="new-snippet-code" rows="8" style="font-family:'Courier New',monospace;resize:vertical;"></textarea>
            </div>
            <div class="mod-option"><label class="mod-option-label">Tags (comma separated)</label><input type="text" class="mod-option-input" id="new-snippet-tags" placeholder="exploit, shell, python"></div>
            <button class="settings-save" onclick="saveNewSnippet()" style="margin-top:8px;width:100%;">Save Snippet</button>
        </div>
    `;
});

async function saveNewSnippet() {
    const data = {
        title: document.getElementById('new-snippet-title')?.value || 'Untitled',
        description: document.getElementById('new-snippet-desc')?.value || '',
        language: document.getElementById('new-snippet-lang')?.value || 'python',
        code: document.getElementById('new-snippet-code')?.value || '',
        tags: (document.getElementById('new-snippet-tags')?.value || '').split(',').map(t => t.trim()).filter(Boolean),
    };
    try {
        await api(`${API}/snippets/add`, { method: 'POST', body: data });
        showToast('Snippet saved');
        document.getElementById('snippet-detail-panel').style.display = 'none';
        renderSnippetsTab();
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

/* ─── VULNERABILITIES TAB ─── */
async function renderVulnsTab() {
    const results = document.getElementById('vuln-results');
    if (!results) return;
    results.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:40px;">Search for a CVE ID or keyword to begin.</div>';

    document.getElementById('vuln-search-btn')?.addEventListener('click', searchVulnerabilities);
    document.getElementById('vuln-search')?.addEventListener('keydown', e => { if (e.key === 'Enter') searchVulnerabilities(); });
}

async function searchVulnerabilities() {
    const q = document.getElementById('vuln-search')?.value.trim();
    if (!q) return;
    const results = document.getElementById('vuln-results');
    showLoading(results);
    try {
        const vulns = await api(`${API}/vulnerabilities/search?q=${encodeURIComponent(q)}`);
        if (!vulns || vulns.length === 0) {
            showEmpty(results, 'No vulnerabilities found. Try a different search term.');
            return;
        }
        results.innerHTML = vulns.map(v => {
            const sevColors = { Critical: 'var(--accent-red)', High: '#ff6b35', Medium: 'var(--accent-gold)', Low: 'var(--accent-green)' };
            return `
            <div class="vuln-card" onclick="openVuln('${v.cve_id}')" style="border-left:4px solid ${sevColors[v.severity] || '#5a6478'};">
                <div class="vuln-card-header">
                    <span class="vuln-cve-id">${v.cve_id}</span>
                    <span class="vuln-severity" style="color:${sevColors[v.severity] || '#5a6478'}">${v.severity} (${v.cvss_score})</span>
                </div>
                <div class="vuln-card-title">${v.title}</div>
                <div class="vuln-card-meta">${v.affected_software || ''} · ${v.published_date || ''} ${v.exploit_available ? '· 🛠 Exploit Available' : ''}</div>
            </div>`;
        }).join('');
    } catch (e) {
        showError(results, 'Search failed: ' + e.message);
    }
}

async function openVuln(cveId) {
    const panel = document.getElementById('vuln-detail-panel');
    const body = document.getElementById('vuln-detail-body');
    const title = document.getElementById('vuln-detail-title');
    panel.style.display = 'block';
    body.innerHTML = '<div class="loading-spinner"></div>';
    title.textContent = cveId;
    try {
        const v = await api(`${API}/vulnerabilities/${cveId}`);
        const sevColors = { Critical: 'var(--accent-red)', High: '#ff6b35', Medium: 'var(--accent-gold)', Low: 'var(--accent-green)' };
        body.innerHTML = `
            <div class="vuln-header">
                <span class="vuln-cve-label">${v.cve_id}</span>
                <span class="vuln-severity-badge" style="background:${sevColors[v.severity] || '#5a6478'}">${v.severity}</span>
                <span class="vuln-cvss-score">CVSS ${v.cvss_score}</span>
            </div>
            <h3 style="color:#fff;margin:12px 0;">${v.title}</h3>
            <p style="color:var(--text-secondary);line-height:1.6;font-size:0.85rem;margin-bottom:16px;">${v.description}</p>
            <div class="vuln-detail-grid">
                <div><span class="vuln-detail-label">Software</span><span>${v.affected_software || 'N/A'}</span></div>
                <div><span class="vuln-detail-label">Versions</span><span>${v.affected_versions || 'N/A'}</span></div>
                <div><span class="vuln-detail-label">Published</span><span>${v.published_date || 'N/A'}</span></div>
                <div><span class="vuln-detail-label">Exploit Available</span><span>${v.exploit_available ? '✅ Yes' : '❌ No'}</span></div>
            </div>
            ${v.references && v.references.length > 0 ? `
            <div style="margin-top:16px;">
                <div style="font-size:0.8rem;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">References</div>
                ${v.references.map(ref => `<a href="${ref}" target="_blank" style="display:block;font-size:0.8rem;color:var(--accent-cyan);margin-bottom:4px;">${ref}</a>`).join('')}
            </div>` : ''}
        `;
    } catch (e) {
        body.innerHTML = `<div class="error-state">Error: ${e.message}</div>`;
    }
}

document.getElementById('close-vuln')?.addEventListener('click', () => {
    document.getElementById('vuln-detail-panel').style.display = 'none';
});

/* ─── SETTINGS: AGENT PERSONALITIES ─── */
async function loadAgentPersonalities() {
    const el = document.getElementById('agent-personalities-list');
    if (!el) return;
    const agents = ['Blade','Shadow','Hunter','Sentry','Inferno','Specter','Null','Phantom','Assassin','Titan','Warlock','Ranger','Engineer','Summoner','Overlord'];
    el.innerHTML = agents.map(a => `
        <div class="agent-personality-item">
            <div class="agent-personality-header" onclick="this.nextElementSibling.classList.toggle('open');this.querySelector('.toggle-icon').classList.toggle('open')">
                <span>${a}</span>
                <span class="toggle-icon">▶</span>
            </div>
            <div class="agent-personality-body">
                <textarea class="agent-prompt-edit" data-agent="${a.toLowerCase()}" rows="4" placeholder="Custom prompt for ${a}..."></textarea>
                <button class="settings-save" style="width:100%;margin-top:4px;font-size:0.75rem;padding:6px;" onclick="saveAgentPrompt('${a.toLowerCase()}')">Save Custom Prompt</button>
            </div>
        </div>
    `).join('');
}

async function saveAgentPrompt(agentName) {
    const textarea = document.querySelector(`.agent-prompt-edit[data-agent="${agentName}"]`);
    if (!textarea) return;
    try {
        await api(`${API}/auth/settings`, { method: 'PUT', body: { agent_prompts: { [agentName]: textarea.value } } });
        showToast(`${agentName} prompt saved`);
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

/* ─── SETTINGS: AI PROVIDERS ─── */
async function loadProviders() {
    const el = document.getElementById('providers-list');
    if (!el) return;
    try {
        const providers = await api(`${API}/providers/list`);
        const known = await api(`${API}/providers/known`);
        el.innerHTML = providers.map(p => `
            <div class="provider-card">
                <div class="provider-info">
                    <div class="provider-name">${p.name}</div>
                    <div class="provider-meta">${p.provider_type} · ${p.model_name}</div>
                    <div class="provider-meta" style="color:var(--text-muted);font-size:0.6rem;">Key: ${p.api_key}</div>
                </div>
                <div class="provider-actions">
                    <span class="provider-status ${p.is_active ? 'active' : ''}">${p.is_active ? 'Active' : 'Inactive'}</span>
                    <button class="view-all-btn" onclick="editProvider(${p.id})">Edit</button>
                    <button class="view-all-btn" onclick="deleteProvider(${p.id})" style="color:var(--accent-red);">×</button>
                </div>
            </div>
        `).join('');
        if (providers.length === 0) {
            el.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;padding:12px;text-align:center;">No providers configured. Add one below.</div>';
        }
    } catch (e) {
        showToast('Failed to load providers', 'error');
    }
}

document.getElementById('add-provider-btn')?.addEventListener('click', () => {
    const body = document.getElementById('snippet-detail-body');
    document.getElementById('snippet-detail-panel').style.display = 'block';
    document.getElementById('snippet-detail-title').textContent = 'Add AI Provider';
    body.innerHTML = `
        <div class="snippet-add-form">
            <div class="mod-option"><label class="mod-option-label">Provider Type</label>
                <select class="mod-option-select" id="new-provider-type">
                    <option value="openai">OpenAI</option><option value="google">Google Gemini</option>
                    <option value="anthropic">Anthropic Claude</option><option value="groq">Groq</option>
                    <option value="together">Together AI</option><option value="openrouter">OpenRouter</option>
                    <option value="ollama">Ollama (Local)</option><option value="custom">Custom</option>
                </select>
            </div>
            <div class="mod-option"><label class="mod-option-label">Name</label><input type="text" class="mod-option-input" id="new-provider-name" placeholder="My OpenAI"></div>
            <div class="mod-option"><label class="mod-option-label">API Key</label><input type="password" class="mod-option-input" id="new-provider-key" placeholder="sk-..."></div>
            <div class="mod-option"><label class="mod-option-label">Model Name</label><input type="text" class="mod-option-input" id="new-provider-model" placeholder="gpt-4"></div>
            <div class="mod-option"><label class="mod-option-label">Base URL</label><input type="text" class="mod-option-input" id="new-provider-url" placeholder="https://api.openai.com/v1"></div>
            <button class="settings-save" onclick="saveProvider()" style="margin-top:8px;width:100%;">Add Provider</button>
        </div>
    `;
    // Auto-fill known model info on type change
    async function updateProviderFields() {
        const type = document.getElementById('new-provider-type')?.value;
        try {
            const known = await api(`${API}/providers/known`);
            const p = known.find(k => k.type === type);
            if (p) {
                document.getElementById('new-provider-name').value = p.name;
                document.getElementById('new-provider-url').value = p.default_url;
                document.getElementById('new-provider-model').value = p.models[0] || '';
            }
        } catch(e) {}
    }
    document.getElementById('new-provider-type')?.addEventListener('change', updateProviderFields);
});

async function saveProvider() {
    const data = {
        name: document.getElementById('new-provider-name')?.value || 'My Provider',
        provider_type: document.getElementById('new-provider-type')?.value || 'custom',
        api_key: document.getElementById('new-provider-key')?.value || '',
        model_name: document.getElementById('new-provider-model')?.value || 'gpt-4',
        base_url: document.getElementById('new-provider-url')?.value || '',
        is_active: true,
    };
    try {
        await api(`${API}/providers/add`, { method: 'POST', body: data });
        showToast('Provider added');
        document.getElementById('snippet-detail-panel').style.display = 'none';
        loadProviders();
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

async function deleteProvider(id) {
    if (!confirm('Delete this provider?')) return;
    try {
        await api(`${API}/providers/${id}`, { method: 'DELETE' });
        showToast('Provider deleted');
        loadProviders();
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

/* ─── SETTINGS: REPORT GENERATION ─── */
document.getElementById('generate-report')?.addEventListener('click', async () => {
    try {
        const report = await api(`${API}/reports/generate`, { method: 'POST', body: { include_all: true } });
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pentest-report-${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Pentest report generated and downloaded');
    } catch (e) {
        showToast('Failed: ' + e.message, 'error');
    }
});

/* ─── INIT ─── */
async function init() {
    await loadUser();
    await loadTasks();
    renderDashboardAgents();
    renderDashboardTasks();
    renderDashboardNews(state.news.hacking, 'dashboard-hacking-news');
    renderDashboardNews(state.news.ai, 'dashboard-industry-news');
    renderQuickTools();
    renderPowerChart();
    renderActivityChart();
    window.addEventListener('resize', renderActivityChart);

    // Preload news
    try {
        const hacking = await api(`${API}/news/hacking`).catch(() => ({ articles: [] }));
        const ai = await api(`${API}/news/ai`).catch(() => ({ articles: [] }));
        state.news.hacking = hacking.articles || [];
        state.news.ai = ai.articles || [];
        renderDashboardNews(state.news.hacking, 'dashboard-hacking-news');
        renderDashboardNews(state.news.ai, 'dashboard-industry-news');
    } catch (e) {}
}

/* ─── WAR ROOM ─── */
const wrState = { match: null, roundActive: false, autoBattle: false, upgradesView: false };

async function renderWarRoomTab() {
    if (wrState.match && wrState.match.status === 'in_progress') {
        showBattleView();
        return;
    }
    showLobbyView();
    await loadScenarios();
    await loadMatchHistory();
}

function showLobbyView() {
    document.getElementById('warroom-lobby').style.display = 'block';
    document.getElementById('warroom-battle').style.display = 'none';
    document.getElementById('warroom-upgrades').style.display = 'none';
    wrState.upgradesView = false;
}

function showBattleView() {
    document.getElementById('warroom-lobby').style.display = 'none';
    document.getElementById('warroom-battle').style.display = 'block';
    document.getElementById('warroom-upgrades').style.display = 'none';
    wrState.upgradesView = false;
}

function showUpgradesView() {
    document.getElementById('warroom-lobby').style.display = 'none';
    document.getElementById('warroom-battle').style.display = 'none';
    document.getElementById('warroom-upgrades').style.display = 'block';
    wrState.upgradesView = true;
    renderUpgradesGrid();
}

async function loadScenarios() {
    const grid = document.getElementById('scenario-grid');
    if (!grid) return;
    try {
        const scenarios = await api(`${API}/simulation/scenarios`);
        grid.innerHTML = Object.entries(scenarios).map(([key, s]) => `
            <div class="scenario-card" data-scenario="${key}">
                <div class="scenario-card-header">
                    <span class="scenario-icon">${getScenarioIcon(key)}</span>
                    <h3>${s.title}</h3>
                </div>
                <p class="scenario-desc">${s.description}</p>
                <div class="scenario-strategies">
                    <div class="scenario-strat"><span class="strat-label red">RED</span> ${s.red_strategy}</div>
                    <div class="scenario-strat"><span class="strat-label blue">BLUE</span> ${s.blue_strategy}</div>
                </div>
                <button class="scenario-launch-btn" onclick="startMatch('${key}')">Launch Battle</button>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = `<div class="error-state">Failed to load scenarios: ${e.message}</div>`;
    }
}

function getScenarioIcon(key) {
    const icons = { 'web_app': '🌐', 'network_breach': '🏢', 'wireless': '📡', 'cloud': '☁️', 'iot_botnet': '🔗' };
    return icons[key] || '⚔️';
}

async function startMatch(scenario) {
    try {
        const match = await api(`${API}/simulation/start`, { method: 'POST', body: { scenario } });
        wrState.match = match;
        showBattleView();
        renderBattleView();
    } catch (e) {
        showToast('Failed to start match: ' + e.message, 'error');
    }
}

function renderBattleView() {
    const m = wrState.match;
    if (!m) return;

    document.getElementById('wr-red-score').textContent = m.red_score;
    document.getElementById('wr-blue-score').textContent = m.blue_score;
    document.getElementById('wr-red-kills').textContent = m.red_kills + ' kills';
    document.getElementById('wr-blue-kills').textContent = m.blue_kills + ' kills';
    document.getElementById('wr-round-display').textContent = `Round ${m.current_round}/${m.max_rounds}`;
    document.getElementById('wr-scenario-name').textContent = m.scenario_title;
    document.getElementById('wr-status').textContent = m.status === 'in_progress' ? 'In Progress' : m.winner ? `${m.winner.toUpperCase()} WINS` : 'Over';

    // Render agents
    renderTeamAgents('wr-red-agents', m.red_agents || m.red_agents_json || [], 'red');
    renderTeamAgents('wr-blue-agents', m.blue_agents || m.blue_agents_json || [], 'blue');

    // Render battle log
    renderBattleLog(m.round_history || m.round_history_json || []);
}

function renderTeamAgents(containerId, agents, team) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const sorted = [...agents].sort((a, b) => a.hp - b.hp);
    container.innerHTML = sorted.map(a => {
        const hpPct = Math.max(0, (a.hp / a.max_hp) * 100);
        const isDown = a.hp <= 0;
        return `
        <div class="wr-agent-card ${isDown ? 'down' : 'active'}" data-name="${a.name}" title="${a.role}">
            <div class="wr-agent-icon" style="background:${a.color}33;color:${a.color}">${a.icon}</div>
            <div class="wr-agent-name">${a.name}</div>
            <div class="wr-agent-hp-bar">
                <div class="wr-agent-hp-fill" style="width:${hpPct}%;background:${hpPct > 50 ? '#22c55e' : hpPct > 25 ? '#eab308' : '#ef4444'}"></div>
            </div>
            <div class="wr-agent-stats">
                <span title="Attack">⚔ ${a.attack}</span>
                <span title="Defense">🛡 ${a.defense}</span>
                <span title="Speed">⚡ ${a.speed}</span>
            </div>
            ${a.special_move ? `<div class="wr-agent-special" title="${a.special_desc}">✦ ${a.special_move}</div>` : ''}
        </div>`;
    }).join('');
}

function renderBattleLog(history) {
    const log = document.getElementById('wr-battle-log');
    const count = document.getElementById('wr-log-count');
    if (!log) return;
    count.textContent = history.length + ' rounds';
    log.innerHTML = history.map(r => `
        <div class="battle-log-entry ${r.winner}-win">
            <div class="log-round">R${r.round}</div>
            <div class="log-icon">${r.winner === 'red' ? '⚔️' : '🛡️'}</div>
            <div class="log-detail">
                <span class="log-attacker" style="color:${r.attacker?.color || '#ef4444'}">${r.attacker?.icon || ''} ${r.attacker?.name || '?'}</span>
                <span class="log-vs">vs</span>
                <span class="log-defender" style="color:${r.defender?.color || '#3b82f6'}">${r.defender?.icon || ''} ${r.defender?.name || '?'}</span>
                <span class="log-result">— ${r.winner === 'red' ? 'Red' : 'Blue'} wins!</span>
                ${r.is_critical ? '<span class="log-critical">CRIT!</span>' : ''}
                ${r.special_used ? '<span class="log-special">✦</span>' : ''}
            </div>
            <div class="log-score">${r.score_after?.red || 0}:${r.score_after?.blue || 0}</div>
        </div>
    `).join('') || '<div style="color:var(--text-muted);padding:8px;">No battles yet. Click "Next Round" to begin.</div>';
}

async function runNextRound() {
    if (wrState.roundActive) return;
    if (!wrState.match || wrState.match.status !== 'in_progress') {
        showToast('Match is already over. Start a new battle.', 'error');
        return;
    }

    wrState.roundActive = true;
    const btn = document.getElementById('wr-next-round');
    const autoBtn = document.getElementById('wr-auto-battle');
    if (btn) btn.disabled = true;
    if (autoBtn) autoBtn.disabled = true;

    try {
        const result = await api(`${API}/simulation/${wrState.match.id}/round`, { method: 'POST' });
        wrState.match = result;

        // Show battle animation
        showBattleAnimation(result);

        // Update view
        renderBattleView();
    } catch (e) {
        showToast('Round failed: ' + e.message, 'error');
    } finally {
        wrState.roundActive = false;
        if (btn) btn.disabled = false;
        if (autoBtn) autoBtn.disabled = false;

        // Check match end
        if (wrState.match.status === 'completed') {
            showMatchResult();
        }
    }
}

function showBattleAnimation(round) {
    const display = document.getElementById('wr-battle-display');
    const phase = document.getElementById('battle-phase');
    const narrative = document.getElementById('battle-narrative');
    const impact = document.getElementById('battle-impact');
    const canvas = document.getElementById('battle-canvas');
    if (!display || !canvas) return;

    display.style.display = 'block';
    phase.textContent = `Round ${round.round}: ${round.attacker?.name || '??'} vs ${round.defender?.name || '??'}`;
    narrative.textContent = round.narrative || '';
    impact.textContent = round.is_critical ? '💥 CRITICAL HIT! 💥' : round.is_perfect_defense ? '🛡️ PERFECT DEFENSE! 🛡️' : '';
    const ft = document.getElementById('battle-flavor');
    if (ft) ft.textContent = round.flavor_text ? `"${round.flavor_text}"` : '';

    animateBattleCanvas(canvas, round);
}

function animateBattleCanvas(canvas, round) {
    const ctx = canvas.getContext('2d');
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const frames = 90;
    let frame = 0;
    const winner = round.winner === 'red';
    const attackerColor = round.attacker?.color || '#ef4444';
    const defenderColor = round.defender?.color || '#3b82f6';

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const progress = frame / frames;

        // Background grid
        ctx.strokeStyle = 'rgba(124,58,237,0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i < canvas.width; i += 40) {
            ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, canvas.height); ctx.stroke();
        }
        for (let i = 0; i < canvas.height; i += 40) {
            ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(canvas.width, i); ctx.stroke();
        }

        // Draw agents
        drawAgent(ctx, 120, cy, round.attacker?.icon || '?', attackerColor, round.attacker?.name || '');
        drawAgent(ctx, 680, cy, round.defender?.icon || '?', defenderColor, round.defender?.name || '');

        // Phase 1: Windup (0-25%)
        if (progress < 0.25) {
            const glow = progress / 0.25;
            drawGlow(ctx, 120, cy, 40 * glow, attackerColor);
        }
        // Phase 2: Attack travels (25-55%)
        else if (progress < 0.55) {
            const beamP = (progress - 0.25) / 0.3;
            const bx = 120 + (560 * beamP);
            drawBeam(ctx, 120, cy, bx, cy, winner ? attackerColor : '#ff8800');
            drawExplosion(ctx, bx, cy, beamP * 0.5);
        }
        // Phase 3: Impact (55-80%)
        else if (progress < 0.80) {
            const impactP = (progress - 0.55) / 0.25;
            drawExplosion(ctx, winner ? 680 : 120, cy, impactP);
            if (round.is_critical) {
                ctx.fillStyle = `rgba(255,255,255,${impactP * 0.3})`;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }
        }
        // Phase 4: Resolution (80-100%)
        else {
            const resP = (progress - 0.80) / 0.20;
            if (winner) {
                drawAgent(ctx, 120, cy, round.attacker?.icon || '?', attackerColor, round.attacker?.name || '');
                drawDamagedAgent(ctx, 680, cy, round.defender?.icon || '?', defenderColor);
                ctx.fillStyle = `rgba(239,68,68,${resP * 0.15})`;
                ctx.fillRect(580, 100, 200, 100);
                ctx.fillStyle = '#ef4444';
                ctx.font = 'bold 18px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('🔥 BREACH!', 680, 170);
            } else {
                drawAgent(ctx, 680, cy, round.defender?.icon || '?', defenderColor, round.defender?.name || '');
                drawDamagedAgent(ctx, 120, cy, round.attacker?.icon || '?', attackerColor);
                ctx.fillStyle = `rgba(59,130,246,${resP * 0.15})`;
                ctx.fillRect(20, 100, 200, 100);
                ctx.fillStyle = '#3b82f6';
                ctx.font = 'bold 18px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('🛡 BLOCKED!', 120, 170);
            }
        }

        frame++;
        if (frame < frames) requestAnimationFrame(draw);
    }

    draw();
}

function drawAgent(ctx, x, y, icon, color, name) {
    ctx.beginPath();
    ctx.arc(x, y, 30, 0, Math.PI * 2);
    ctx.fillStyle = color + '22';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(icon, x, y);

    if (name) {
        ctx.font = '11px Inter, sans-serif';
        ctx.fillStyle = '#e2e8f0';
        ctx.textBaseline = 'top';
        ctx.fillText(name, x, y + 35);
    }
}

function drawDamagedAgent(ctx, x, y, icon, color) {
    drawAgent(ctx, x, y, icon, color, '');
    ctx.beginPath();
    ctx.arc(x, y, 30, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,0,0,0.3)';
    ctx.fill();
    // X marks
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x - 12, y - 12); ctx.lineTo(x + 12, y + 12);
    ctx.moveTo(x + 12, y - 12); ctx.lineTo(x - 12, y + 12);
    ctx.stroke();
}

function drawGlow(ctx, x, y, radius, color) {
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, color + '88');
    gradient.addColorStop(1, color + '00');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
}

function drawBeam(ctx, x1, y1, x2, y2, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.shadowColor = color;
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Trail particles
    for (let i = 0; i < 5; i++) {
        const t = Math.random();
        const px = x1 + (x2 - x1) * t;
        const py = y1 + (y2 - y1) * t + (Math.random() - 0.5) * 20;
        ctx.fillStyle = color + '44';
        ctx.beginPath();
        ctx.arc(px, py, 2 + Math.random() * 3, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawExplosion(ctx, x, y, intensity) {
    const r = 20 + intensity * 60;
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
    gradient.addColorStop(0, `rgba(255,200,50,${intensity * 0.8})`);
    gradient.addColorStop(0.5, `rgba(255,100,0,${intensity * 0.4})`);
    gradient.addColorStop(1, `rgba(255,0,0,0)`);
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    // Particles
    for (let i = 0; i < 10 * intensity; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dist = Math.random() * r;
        ctx.fillStyle = `rgba(255,${150 + Math.random() * 100},0,${intensity * 0.5})`;
        ctx.beginPath();
        ctx.arc(x + Math.cos(angle) * dist, y + Math.sin(angle) * dist, 1 + Math.random() * 2, 0, Math.PI * 2);
        ctx.fill();
    }
}

function showMatchResult() {
    const m = wrState.match;
    if (!m) return;
    const winner = m.winner;
    const overlay = document.getElementById('level-up-overlay');
    if (overlay) {
        const text = overlay.querySelector('.level-up-text');
        const detail = overlay.querySelector('.level-up-detail');
        const power = overlay.querySelector('.level-up-power');
        if (text) text.textContent = winner === 'draw' ? 'DRAW' : `${winner.toUpperCase()} TEAM WINS`;
        if (detail) detail.textContent = `${m.red_score} - ${m.blue_score}`;
        if (power) power.textContent = winner === 'red' ? 'Red Team dominates the digital battlefield!' : 'Blue Team holds the line!';
        overlay.classList.add('show');
        setTimeout(() => overlay.classList.remove('show'), 4000);
    }
}

async function loadMatchHistory() {
    const el = document.getElementById('warroom-history-list');
    if (!el) return;
    try {
        const history = await api(`${API}/simulation/history/list?limit=5`);
        if (!history || history.length === 0) {
            el.innerHTML = '<div class="empty-state">No past battles yet. Launch your first!</div>';
            return;
        }
        el.innerHTML = history.map(m => `
            <div class="warroom-history-item" onclick="loadPastMatch(${m.id})">
                <span class="wr-h-icon">${getScenarioIcon(m.scenario)}</span>
                <div class="wr-h-info">
                    <div class="wr-h-title">${m.scenario_title}</div>
                    <div class="wr-h-meta">${m.current_round} rounds · ${m.winner ? m.winner.toUpperCase() + ' wins' : 'Incomplete'} · ${m.red_score}:${m.blue_score}</div>
                </div>
                <span class="wr-h-status ${m.winner || 'incomplete'}">${m.winner ? (m.winner === 'draw' ? 'DRAW' : m.winner.toUpperCase()) : 'Active'}</span>
            </div>
        `).join('');
    } catch (e) {
        el.innerHTML = '<div class="empty-state">Failed to load history</div>';
    }
}

async function loadPastMatch(matchId) {
    try {
        const match = await api(`${API}/simulation/${matchId}`);
        wrState.match = match;
        showBattleView();
        renderBattleView();
    } catch (e) {
        showToast('Failed to load match: ' + e.message, 'error');
    }
}

async function renderUpgradesGrid() {
    const grid = document.getElementById('upgrade-grid');
    const xpDisplay = document.getElementById('wr-upgrade-xp');
    if (!grid) return;

    try {
        const stats = await api(`${API}/simulation/stats/list`);
        const totalXp = stats.reduce((s, a) => s + a.xp, 0);
        if (xpDisplay) xpDisplay.textContent = `Total XP: ${totalXp}`;

        const renderUpgradeRow = (name, stat, val, canUp) => `
            <div class="upgrade-stat-row" data-agent="${name}" data-stat="${stat}">
                <span>${stat.charAt(0).toUpperCase() + stat.slice(1)}</span><span>${val}</span>
                ${canUp ? '<button class="upgrade-btn">+</button>' : ''}
            </div>`;

        grid.innerHTML = stats.map(a => {
            const upgradeCost = 100;
            const canUp = a.xp >= upgradeCost;
            return `
            <div class="upgrade-card">
                <div class="upgrade-header">
                    <span class="upgrade-icon">${a.team === 'red' ? '⚔️' : '🛡️'}</span>
                    <span class="upgrade-name">${a.agent_name}</span>
                    <span class="upgrade-level">Lv.${a.level}</span>
                </div>
                <div class="upgrade-stats">
                    ${renderUpgradeRow(a.agent_name, 'attack', a.attack, canUp)}
                    ${renderUpgradeRow(a.agent_name, 'defense', a.defense, canUp)}
                    ${renderUpgradeRow(a.agent_name, 'speed', a.speed, canUp)}
                    ${renderUpgradeRow(a.agent_name, 'special', a.special, canUp)}
                </div>
                <div class="upgrade-xp">XP: ${a.xp}${a.kills > 0 ? ' · Kills: ' + a.kills : ''}</div>
                ${a.special_move ? '<div class="upgrade-special">✦ ' + a.special_move + '</div>' : ''}
            </div>`;
        }).join('');

        // Event delegation for upgrade buttons
        grid.addEventListener('click', (e) => {
            const btn = e.target.closest('.upgrade-btn');
            if (!btn) return;
            const row = btn.closest('.upgrade-stat-row');
            if (!row) return;
            const agentName = row.dataset.agent;
            const stat = row.dataset.stat;
            upgradeAgent(agentName, stat);
        });
    } catch (e) {
        grid.innerHTML = `<div class="error-state">Failed to load stats: ${e.message}</div>`;
    }
}

async function upgradeAgent(agentName, stat) {
    try {
        const result = await api(`${API}/simulation/agent/upgrade`, {
            method: 'POST',
            body: { agent_name: agentName, stat }
        });
        if (result.success) {
            showToast(`${agentName}: ${stat} upgraded!`);
            renderUpgradesGrid();
        } else {
            showToast(result.error || 'Upgrade failed', 'error');
        }
    } catch (e) {
        showToast('Upgrade failed: ' + e.message, 'error');
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('wr-next-round')?.addEventListener('click', runNextRound);

    document.getElementById('wr-auto-battle')?.addEventListener('click', async function() {
        wrState.autoBattle = !wrState.autoBattle;
        this.textContent = wrState.autoBattle ? 'Stop Auto' : 'Auto Battle';
        this.style.borderColor = wrState.autoBattle ? 'var(--accent-green)' : '';
        while (wrState.autoBattle && wrState.match && wrState.match.status === 'in_progress') {
            await runNextRound();
            await new Promise(r => setTimeout(r, 1000));
        }
        wrState.autoBattle = false;
        if (this) this.textContent = 'Auto Battle';
    });

    document.getElementById('wr-upgrade-btn')?.addEventListener('click', () => {
        showUpgradesView();
        renderUpgradesGrid();
    });

    document.getElementById('wr-upgrade-back')?.addEventListener('click', showBattleView);

    document.getElementById('wr-end-match')?.addEventListener('click', () => {
        if (confirm('End this match? Progress will be saved.')) {
            wrState.match = null;
            showLobbyView();
            loadMatchHistory();
        }
    });

    document.getElementById('battle-dismiss')?.addEventListener('click', () => {
        document.getElementById('wr-battle-display').style.display = 'none';
    });
});

init();

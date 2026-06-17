(function() {
const TOKEN = localStorage.getItem('darkx_token');

window.loadModules = async function() {
    try {
        const response = await fetch('/api/modules/list', {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        const modules = await response.json();
        const grid = document.getElementById('modules-grid');
        if (!grid) return;
        grid.innerHTML = modules.map(mod => `
            <div class="module-card" onclick="openModule('${mod.id}')">
                <div class="module-header">
                    <h3 style="font-size:0.92rem; font-weight:600;">${mod.name}</h3>
                    <span class="module-agent-badge">${mod.agent}</span>
                </div>
                <p>${mod.desc}</p>
                <button class="module-action-btn">INITIALIZE</button>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load modules:', err);
    }
};

window.openModule = async function(moduleId) {
    const modal = document.createElement('div');
    modal.className = 'module-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Module: ${moduleId}</h3>
                <button class="modal-close" onclick="this.closest('.module-modal').remove()">&#10005;</button>
            </div>
            <div class="modal-body" id="module-output">
                <div style="color:var(--text-muted);">> Initializing module ${moduleId}...</div>
                <div style="color:var(--text-muted);">> Requesting agent authorization...</div>
            </div>
            <div class="modal-footer">
                <input type="text" id="mod-input" placeholder="Enter target or parameters...">
                <button onclick="runModule('${moduleId}')">RUN</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
};

window.runModule = async function(moduleId) {
    const input = document.getElementById('mod-input').value;
    const output = document.getElementById('module-output');
    if (!output) return;
    output.innerHTML += `\n<span style="color:var(--text-primary);">> Running ${moduleId} on ${input}...</span>`;
    try {
        const response = await fetch(`/api/modules/${moduleId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${TOKEN}`
            },
            body: JSON.stringify({ target: input || '127.0.0.1' })
        });
        const data = await response.json();
        output.innerHTML += `\n<span style="color:var(--accent-green);">--- Results ---</span>`;
        output.innerHTML += `\n${data.results?.data || data.output || 'No output'}`;
        if (data.results?.ai_analysis) {
            output.innerHTML += `\n<span style="color:var(--accent-gold);">AI Analysis: ${data.results.ai_analysis}</span>`;
        }
    } catch (err) {
        output.innerHTML += `\n<span style="color:var(--accent-red);">Error: ${err.message}</span>`;
    }
    output.scrollTop = output.scrollHeight;
};
})();

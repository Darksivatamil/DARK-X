async function loadDAO() {
    const panel = document.getElementById('main-panel');
    panel.innerHTML = `
        <h2 class="animate-awaken">Shadow DAO Identity</h2>
        <div class="agent-card" style="max-width:600px; margin: 0 auto; text-align:left;">
            <div id="did-info" style="margin-bottom:20px;">
                <p class="tech-font" style="color:var(--accent-secondary)">Loading DID...</p>
            </div>
            <hr style="border:0; border-top:1px solid rgba(0,212,255,0.2); margin:20px 0;">
            <h3>Guild Affiliation</h3>
            <div id="guild-info" style="margin-bottom:20px;">
                <p>No guild affiliation detected.</p>
            </div>
            <div class="input-group">
                <input type="text" id="guild-name" style="width:70%; padding:10px; background:black; color:white; border:1px solid var(--border-glow);" placeholder="Enter Guild Name...">
                <button class="btn-primary" style="width:auto; padding:10px 20px;" onclick="joinGuild()">JOIN GUILD</button>
            </div>
        </div>
    `;

    try {
        const response = await fetch('/api/dao/my-id', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('darkx_token')}` }
        });
        const data = await response.json();
        
        document.getElementById('did-info').innerHTML = `
            <p><strong>DID:</strong> <span style="color:var(--accent-secondary)">${data.did}</span></p>
            <p><strong>Reputation:</strong> <span style="color:var(--accent-warning)">${data.profile.reputation} XP</span></p>
            <p><strong>Username:</strong> ${data.profile.username}</p>
        `;

        if (data.profile.guild) {
            document.getElementById('guild-info').innerHTML = `
                <p>Current Guild: <span class="tech-font" style="color:var(--accent-primary)">${data.profile.guild}</span></p>
            `;
        }
    } catch (err) {
        console.error('DAO Load Error:', err);
    }
}

async function joinGuild() {
    const guildName = document.getElementById('guild-name').value;
    if (!guildName) return alert('Enter a guild name');

    try {
        const response = await fetch(`/api/dao/guild/join?guild_name=${encodeURIComponent(guildName)}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('darkx_token')}` }
        });
        if (response.ok) {
            alert(`Successfully joined ${guildName}!`);
            loadDAO();
        }
    } catch (err) {
        alert('Failed to join guild: ' + err.message);
    }
}

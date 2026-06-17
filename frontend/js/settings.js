(function() {
const TOKEN = localStorage.getItem('darkx_token');

window.loadSettings = async function() {
    const openai = document.getElementById('set-openai');
    const gemini = document.getElementById('set-gemini');
    const username = document.getElementById('set-username');
    const email = document.getElementById('set-email');
    try {
        const res = await fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${TOKEN}` } });
        const data = await res.json();
        const u = data.user || {};
        const keys = u.settings?.api_keys || {};
        if (openai) openai.value = keys.openai || '';
        if (gemini) gemini.value = keys.gemini || '';
        if (username) username.value = u.username || '';
        if (email) email.value = u.email || '';
    } catch (e) { console.error(e); }
};
})();

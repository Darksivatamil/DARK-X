(function() {
const TOKEN = localStorage.getItem('darkx_token');
if (!TOKEN && !window.location.pathname.includes('index.html')) {
    window.location.href = '/static/index.html';
}
})();

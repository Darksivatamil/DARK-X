let isRegisterMode = false;

function showError(msg) {
    const box = document.getElementById('error-box');
    box.style.display = 'block';
    box.innerText = msg;
}

function hideError() {
    document.getElementById('error-box').style.display = 'none';
}

document.getElementById('toggle-register').addEventListener('click', () => {
    hideError();
    isRegisterMode = !isRegisterMode;
    const btn = document.getElementById('btn-login');
    const emailGroup = document.getElementById('email-group');
    const confirmGroup = document.getElementById('confirm-group');
    const toggleText = document.getElementById('toggle-text');

    if (isRegisterMode) {
        btn.innerText = 'Create Identity';
        emailGroup.style.display = 'block';
        confirmGroup.style.display = 'block';
        toggleText.innerHTML = 'Already have an identity? <span id="toggle-register">Awaken System</span>';
    } else {
        btn.innerText = 'Awaken System';
        emailGroup.style.display = 'none';
        confirmGroup.style.display = 'none';
        toggleText.innerHTML = 'No account? <span id="toggle-register">Register Identity</span>';
    }
});

document.getElementById('btn-login').addEventListener('click', async () => {
    hideError();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showError('Username and Access Code are required.');
        return;
    }

    if (isRegisterMode) {
        const email = document.getElementById('email').value.trim();
        const confirmPass = document.getElementById('confirm-password').value;

        if (!email) {
            showError('Email is required for registration.');
            return;
        }
        if (password !== confirmPass) {
            showError('Access Codes do not match.');
            return;
        }
        if (password.length < 6) {
            showError('Access Code must be at least 6 characters.');
            return;
        }

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, email })
            });

            if (!response.ok) {
                const err = await response.json();
                showError(err.detail || 'Registration failed.');
                return;
            }

            const data = await response.json();
            alert(`Identity created successfully, ${data.username}. You can now awaken.`);
            isRegisterMode = false;
            document.getElementById('btn-login').innerText = 'Awaken System';
            document.getElementById('email-group').style.display = 'none';
            document.getElementById('confirm-group').style.display = 'none';
            document.getElementById('toggle-text').innerHTML = 'No account? <span id="toggle-register">Register Identity</span>';
        } catch (err) {
            showError('Connection error: ' + err.message);
        }
        return;
    }

    // LOGIN
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            showError(err.detail || 'Invalid credentials');
            return;
        }

        const data = await response.json();
        localStorage.setItem('darkx_token', data.access_token);
        localStorage.setItem('darkx_user', JSON.stringify(data.user));

        window.location.href = '/static/dashboard.html';
    } catch (err) {
        showError('Connection error: ' + err.message);
    }
});

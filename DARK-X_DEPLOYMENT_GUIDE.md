# 🕶️ DARK-X — DEPLOYMENT & USER GUIDE
> *From Zero to Shadow Monarch — Live on the Internet*

---

## 📋 TABLE OF CONTENTS
1. [Local Setup (5 min)](#-1-local-setup)
2. [Online Deployment (VPS)](#-2-online-deployment-vps)
3. [First-Time Usage](#-3-first-time-usage)
4. [Feature Walkthrough](#-4-feature-walkthrough)
5. [Terminal Command Reference](#-5-terminal-command-reference)
6. [Troubleshooting](#-6-troubleshooting)

---

## 🖥️ 1. LOCAL SETUP

### Requirements
- Python 3.12+
- pip (Python package manager)
- Git (optional)

### Step 1: Get the Code
```bash
# If you have Git:
git clone <your-repo-url>
cd DARK-X

# Or if you have the folder already:
cd E:\ALL AI PROJECT WORK\DARK-X
```

### Step 2: Create Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy the example env file
cp .env.example .env

# Open .env in any text editor and fill in:
# - OPENAI_API_KEY=your_openai_key_here
# - GEMINI_API_KEY=your_gemini_key_here
# - SECRET_KEY=any_random_string_for_jwt_encryption
```

> **⚠️ IMPORTANT**: You NEED at least one AI API key (OpenAI or Gemini) for the agents to work. Without it, agents will respond with "No AI API keys configured."
> - Get OpenAI key: https://platform.openai.com/api-keys
> - Get Gemini key: https://aistudio.google.com/app/apikey

### Step 5: Run the Server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Open in Browser
```
http://localhost:8000/static/index.html
```

---

## 🌐 2. ONLINE DEPLOYMENT (VPS)

### Option A: VPS with Nginx (Recommended)

#### Prerequisites
- A VPS (DigitalOcean, Linode, Hetzner, etc.) — minimum $6/month
- Domain name (optional but recommended)
- SSH access to your VPS

#### Step 1: Connect to VPS
```bash
ssh root@your_server_ip
```

#### Step 2: Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Python, Nginx, Supervisor
apt install python3 python3-pip python3-venv nginx supervisor git -y

# Install Certbot for SSL (optional)
apt install certbot python3-certbot-nginx -y
```

#### Step 3: Clone the Project
```bash
cd /opt
git clone <your-repo-url>
cd DARK-X
```

#### Step 4: Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your API keys and a strong SECRET_KEY
```

#### Step 5: Install Gunicorn for Production
```bash
pip install gunicorn
```

#### Step 6: Configure Supervisor (Auto-restart)
```bash
nano /etc/supervisor/conf.d/darkx.conf
```

Paste the following:
```ini
[program:darkx]
command=/opt/DARK-X/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
directory=/opt/DARK-X
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/darkx.err.log
stdout_logfile=/var/log/darkx.out.log
```

Then run:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start darkx
```

#### Step 7: Configure Nginx Reverse Proxy
```bash
nano /etc/nginx/sites-available/darkx
```

Paste the following (replace `yourdomain.com` with your domain or server IP):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /static/ {
        alias /opt/DARK-X/frontend/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/darkx /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

#### Step 8: Add SSL (HTTPS) — Optional but Recommended
```bash
certbot --nginx -d yourdomain.com
```

#### Step 9: Firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

#### ✅ Done! Access at: `https://yourdomain.com`

---

### Option B: Cloudflare Tunnel (Free & Private)
Best if you want to run it from your home PC without opening ports.

#### Step 1: Install Cloudflare Tunnel
```bash
# On your local Windows machine:
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

#### Step 2: Authenticate & Create Tunnel
```bash
cloudflared tunnel login
cloudflared tunnel create darkx-tunnel
```

#### Step 3: Configure Tunnel
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: darkx-tunnel
credentials-file: C:\Users\Admin\.cloudflared\darkx-tunnel.json

ingress:
  - hostname: darkx.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

#### Step 4: Run Tunnel
```bash
cloudflared tunnel run darkx-tunnel
```

#### ✅ Done! Access at: `https://darkx.yourdomain.com`

---

## 🎮 3. FIRST-TIME USAGE

### Step-by-Step Walkthrough

#### 1. Register an Account
1. Open the app in your browser
2. Click **"Register Identity"** on the login page
3. Enter a **Username** and **Password**
4. Click **"Create Identity"**
5. You'll be redirected to the Login page

#### 2. Log In
1. Enter your username and password
2. Click **"Awaken System"**
3. You are now on the **Dashboard**

#### 3. Configure AI Keys (Required)
1. Click **⚙️ Settings** in the sidebar
2. Paste your **OpenAI API Key** and/or **Gemini API Key**
3. Click **"SAVE CONFIGURATION"**

#### 4. Awaken the Agents
1. Look at the **Terminal** at the bottom-right
2. Click inside the terminal input box
3. Type `/arise` and press **Enter**
4. Watch all 15 agents activate with their introduction messages

#### 5. Chat with an Agent
1. Type any question in the terminal
2. **DARK-GUIDE-X** (the master agent) will respond
3. To talk to a specific agent, type `/<agent-name>` first
   - Example: `/phantom` then ask "Scan 192.168.1.1"
   - Example: `/cipher-mind` then ask "Analyze this hash"

#### 6. Complete Your First Task
1. Click **📋 Tasks** in the sidebar
2. Choose a task from any track (Python, Kali, AI, Industry)
3. Click **"SUBMIT"** on a task
4. Write your solution in the code editor
5. Click **"SUBMIT FOR GRADING"**
6. Receive your AI-generated score and XP

#### 7. Run a Security Tool
1. Click **🛡️ Modules** in the sidebar
2. Click **"INITIALIZE"** on any module card (e.g., Network Scanner)
3. Enter a target IP in the modal
4. Click **"RUN"** to execute
5. View the real-time results and AI analysis

#### 8. Check Your Progress
1. Click **📊 Stats** to see your skill radar chart
2. Click **⚡ Powers** to view unlocked abilities
3. Your **level, XP bar, and rank** are always visible at the top

#### 9. Join the Shadow DAO
1. Click **🌐 Shadow DAO** in the sidebar
2. View your **Decentralized ID (DID)** and reputation
3. Enter a guild name and click **"JOIN GUILD"**

#### 10. Read the News
1. Click **📰 News** in the sidebar
2. Switch between **Hacking News** and **AI News** tabs
3. Each article is AI-summarized for quick reading

---

## ⌨️ 5. TERMINAL COMMAND REFERENCE

| Command | Action | Example Output |
|---------|--------|----------------|
| `/arise` | Activate all 15 agents | *PHANTOM: "I am Phantom Recon..."* |
| `/rest` | Deactivate all agents | *DARK-GUIDE-X: "Going dormant..."* |
| `/status` | System health check | *S-SYSTEM STATUS: All agents operational* |
| `/stats` | View your rank & XP | *Level 3 | Rank: Cyber Scout | Total XP: 250* |
| `/power` | List unlocked powers | *Shadow Sight, Binary Whisper* |
| `/daily` | Check today's quests | *DAILY QUESTS: Available in Tasks tab* |
| `/phantom` | Call specific agent | *PHANTOM: "Awaiting your command."* |
| `/cipher-mind` | Call crypto agent | *CIPHER-MIND: "Ready for decryption."* |
| `/<any-agent>` | Call any of the 15 agents | *Agent activates and responds* |
| `/help` | Show this command list | *Lists all available commands* |
| `/refresh` | Restart agent session | *All agents reloading...* |
| `/logout` | Exit to login page | *Session terminated* |

---

## 🛠️ 6. TROUBLESHOOTING

### Problem: "No AI API keys configured"
**Solution**: Go to **Settings** tab and add your OpenAI or Gemini API key. Restart the agents with `/rest` then `/arise`.

### Problem: WebSocket won't connect
**Solution**: 
- Ensure you're using `http://` not `file://`
- Check browser console for errors (F12)
- The terminal uses `ws://` protocol which may be blocked by some proxies

### Problem: Modules show "simulation mode"
**Solution**:
- The Mesh Bridge runs commands on your system
- For **Network Scanner** to work, you need `nmap` installed
- For full power, install Docker and the Mesh will auto-use Kali containers

### Problem: "Address already in use" when starting
**Solution**:
```bash
# Find what's using port 8000
netstat -ano | findstr :8000
# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Problem: Nginx 502 Bad Gateway
**Solution**:
```bash
# Check if uvicorn is running
supervisorctl status darkx
# If not running, start it:
supervisorctl start darkx
# Check logs:
tail -f /var/log/darkx.err.log
```

### Problem: SSL Certificate Issues
**Solution**:
```bash
# Renew certificate
certbot renew
# Check certificate status
certbot certificates
```

---

## ⚡ QUICK START (For the Impatient)

```bash
# LOCAL
pip install -r requirements.txt
cp .env.example .env  # Then edit with your API keys
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Open http://localhost:8000/static/index.html

# VPS
# SSH into server, then:
apt install python3 python3-pip python3-venv nginx supervisor -y
git clone <repo> /opt/DARK-X && cd /opt/DARK-X
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
# Edit .env, then configure Nginx + Supervisor (see guide above)
```

---

*"The system has chosen you. From Zero to Shadow Monarch — deploy it, use it, master it."* 🕶️⚡

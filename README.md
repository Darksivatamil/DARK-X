# 🕶️ DARK-X — Shadow Monarch Platform

> **"From Zero to Shadow Monarch — This is not a game, it's a life changer."**

DARK-X is a gamified ethical hacking AI agent platform designed to transform learners into security experts through an immersive, "Solo Leveling" inspired experience.

## 🌟 Key Features

- 🤖 **15 AI Agents**: A full roster of specialized AI agents (Recon, Crypto, Fuzzing, etc.) available via a WebSocket terminal.
- 🎮 **Gamification**: XP system, rank progression (Shadow Initiate $\rightarrow$ Shadow Monarch), and unlockable powers.
- 🛡️ **Live Security Modules**: Integrated tools for network scanning, payload generation, and AI fuzzing.
- 📋 **Daily Challenges**: AI-generated tasks with automatic code grading and XP rewards.
- 📰 **Intelligence Feed**: Live hacking and AI news summarized by AI.
- 🖥️ **S-System UI**: A high-end, anime-inspired dashboard with particle effects and electric animations.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy, SQLite, WebSockets.
- **Frontend**: Vanilla JS, CSS3, HTML5, Chart.js, Xterm.js.
- **AI**: OpenAI GPT-4 / Google Gemini.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Darksivatamil/DARK-X.git
cd dark-x

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file based on `.env.example`:
```env
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=sqlite:///./dark_x.db
SECRET_KEY=your_secret_key
```

### 3. Run the System
```bash
uvicorn backend.main:app --reload
```
Access the system at: `http://localhost:8000/static/index.html`

## ⌨️ Terminal Commands
- `/arise` - Awaken all agents.
- `/rest` - Put agents to sleep.
- `/status` - System health check.
- `/stats` - View current rank and level.
- `/power` - List unlocked shadow abilities.
- `/daily` - Check today's challenges.
- `/logout` - Terminate session.

---
*The system has chosen you. Welcome to the shadow.* 🕶️⚡

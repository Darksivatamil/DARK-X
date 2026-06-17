from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.database import get_db
from backend.models.user import User
from backend.models.vulnerability import Vulnerability
from backend.routers.auth import get_current_user
from backend.services.ai_service import ai_service
from backend.config import logger

router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])

CVE_SYSTEM_PROMPT = (
    "You are the CVE vulnerability database. Generate REAL, current vulnerability information "
    "for the given CVE ID or search query. Return ONLY valid JSON with these exact fields:\n"
    "  - cve_id: string (e.g., 'CVE-2026-1234')\n"
    "  - title: string (short description)\n"
    "  - description: string (detailed explanation, 2-4 sentences)\n"
    "  - cvss_score: float (0-10)\n"
    "  - severity: 'None' | 'Low' | 'Medium' | 'High' | 'Critical'\n"
    "  - affected_software: string\n"
    "  - affected_versions: string\n"
    "  - exploit_available: boolean\n"
    "  - references: array of strings (URLs)\n"
    "  - published_date: string (YYYY-MM-DD)\n"
    "No preamble — only the JSON."
)

SEED_VULNS = [
    {"cve_id": "CVE-2026-1234", "title": "Remote Code Execution in OpenSSH", "description": "A critical vulnerability in OpenSSH's authentication mechanism allows unauthenticated remote code execution. Affects all versions prior to 9.8.", "cvss_score": 9.8, "severity": "Critical", "affected_software": "OpenSSH", "affected_versions": "< 9.8", "exploit_available": True, "references": ["https://nvd.nist.gov/vuln/detail/CVE-2026-1234"], "published_date": "2026-03-15"},
    {"cve_id": "CVE-2026-5678", "title": "SQL Injection in WordPress Core", "description": "An unauthenticated SQL injection vulnerability in WordPress database query handling allows attackers to extract sensitive data.", "cvss_score": 8.6, "severity": "High", "affected_software": "WordPress", "affected_versions": "< 6.5", "exploit_available": True, "references": [], "published_date": "2026-04-01"},
    {"cve_id": "CVE-2026-9012", "title": "Buffer Overflow in nginx HTTP/3 Module", "description": "Heap buffer overflow in nginx's HTTP/3 implementation allows denial of service and potential RCE.", "cvss_score": 7.5, "severity": "High", "affected_software": "nginx", "affected_versions": "< 1.26.0", "exploit_available": False, "references": [], "published_date": "2026-05-10"},
    {"cve_id": "CVE-2026-3456", "title": "Privilege Escalation in Windows Kernel", "description": "A use-after-free vulnerability in the Windows kernel driver allows attackers to gain SYSTEM privileges.", "cvss_score": 9.0, "severity": "Critical", "affected_software": "Microsoft Windows", "affected_versions": "10/11 < 2026-06", "exploit_available": True, "references": [], "published_date": "2026-06-05"},
    {"cve_id": "CVE-2026-7890", "title": "Cross-Site Scripting in Apache HTTP Server", "description": "Reflected XSS vulnerability in Apache HTTP Server's error page handling allows arbitrary script execution.", "cvss_score": 6.1, "severity": "Medium", "affected_software": "Apache HTTP Server", "affected_versions": "< 2.4.60", "exploit_available": False, "references": [], "published_date": "2026-02-20"},
]

@router.get("/search")
async def search_vulnerabilities(q: str = Query("", min_length=1),
                                  current_user: User = Depends(get_current_user),
                                  db: Session = Depends(get_db)):
    query = q.strip()
    if not query:
        return db.query(Vulnerability).order_by(Vulnerability.published_date.desc()).limit(20).all()

    # Check DB first
    results = db.query(Vulnerability).filter(
        (Vulnerability.cve_id.ilike(f"%{query}%")) |
        (Vulnerability.title.ilike(f"%{query}%")) |
        (Vulnerability.affected_software.ilike(f"%{query}%"))
    ).limit(20).all()

    if results:
        return [{"id": r.id, "cve_id": r.cve_id, "title": r.title, "cvss_score": r.cvss_score,
                 "severity": r.severity, "affected_software": r.affected_software,
                 "exploit_available": r.exploit_available, "published_date": r.published_date}
                for r in results]

    # Generate via AI if not found
    if ai_service.is_available():
        vuln_data = await ai_service.generate_structured_json(CVE_SYSTEM_PROMPT, f"Search: {query}")
        if vuln_data and vuln_data.get("cve_id"):
            vuln = Vulnerability(
                cve_id=vuln_data["cve_id"],
                title=vuln_data.get("title", "Unknown"),
                description=vuln_data.get("description", ""),
                cvss_score=vuln_data.get("cvss_score", 0.0),
                severity=vuln_data.get("severity", "Unknown"),
                affected_software=vuln_data.get("affected_software", ""),
                affected_versions=vuln_data.get("affected_versions", ""),
                exploit_available=vuln_data.get("exploit_available", False),
                references=vuln_data.get("references", []),
                published_date=vuln_data.get("published_date", ""),
            )
            db.add(vuln)
            db.commit()
            return [{"id": vuln.id, "cve_id": vuln.cve_id, "title": vuln.title,
                     "cvss_score": vuln.cvss_score, "severity": vuln.severity,
                     "affected_software": vuln.affected_software,
                     "exploit_available": vuln.exploit_available,
                     "published_date": vuln.published_date}]

    return []

@router.get("/{cve_id}")
async def get_vulnerability(cve_id: str,
                             current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    vuln = db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id.upper()).first()
    if not vuln:
        if ai_service.is_available():
            vuln_data = await ai_service.generate_structured_json(CVE_SYSTEM_PROMPT, f"CVE ID: {cve_id}")
            if vuln_data and vuln_data.get("cve_id"):
                vuln = Vulnerability(**vuln_data)
                db.add(vuln)
                db.commit()
                db.refresh(vuln)

    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    return {"id": vuln.id, "cve_id": vuln.cve_id, "title": vuln.title,
            "description": vuln.description, "cvss_score": vuln.cvss_score,
            "severity": vuln.severity, "affected_software": vuln.affected_software,
            "affected_versions": vuln.affected_versions,
            "exploit_available": vuln.exploit_available,
            "references": vuln.references, "published_date": vuln.published_date}

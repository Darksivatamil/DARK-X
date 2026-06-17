from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json, os
from datetime import datetime
from backend.database import get_db
from backend.models.user import User
from backend.models.module import ModuleRun
from backend.routers.auth import get_current_user
from backend.services.ai_service import ai_service
from backend.config import logger

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORT_SYSTEM_PROMPT = (
    "You are a professional penetration test report writer. Generate a comprehensive security assessment "
    "report based on the provided module execution results. The report must be professional, detailed, and actionable. "
    "Return ONLY valid JSON with these fields:\n"
    "  - executive_summary: string (2-3 paragraphs overview)\n"
    "  - scope: string (what was tested)\n"
    "  - methodology: string (approach taken)\n"
    "  - findings: array of objects with {title, severity, description, recommendation}\n"
    "  - risk_score: integer (0-100)\n"
    "  - risk_level: string ('Low'/'Medium'/'High'/'Critical')\n"
    "  - recommendations: array of strings (top 5 actions)\n"
    "  - conclusion: string (final assessment)"
)

@router.post("/generate")
async def generate_report(data: Dict[str, Any],
                           current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    run_ids = data.get("run_ids", [])
    target = data.get("target", "Unknown Target")
    include_all = data.get("include_all", False)

    if include_all:
        runs = db.query(ModuleRun).filter(
            ModuleRun.user_id == current_user.id
        ).order_by(ModuleRun.created_at.desc()).limit(10).all()
    elif run_ids:
        runs = db.query(ModuleRun).filter(
            ModuleRun.id.in_(run_ids),
            ModuleRun.user_id == current_user.id
        ).all()
    else:
        raise HTTPException(status_code=400, detail="Specify run_ids or set include_all=true")

    if not runs:
        raise HTTPException(status_code=404, detail="No module runs found")

    # Build report context
    report_data = []
    for r in runs:
        analysis = {}
        try:
            analysis = json.loads(r.ai_analysis) if r.ai_analysis else {}
        except: pass
        report_data.append({
            "module": r.module_id,
            "target": r.target,
            "output_preview": r.output[:500] if r.output else "",
            "score": r.score,
            "findings": analysis.get("findings", []),
            "risk_level": analysis.get("risk_level", "Unknown"),
            "recommendations": analysis.get("recommendations", []),
            "date": r.created_at.isoformat() if r.created_at else "",
        })

    report_json = {}
    if ai_service.is_available():
        context = json.dumps({
            "target": target,
            "date": datetime.now().isoformat(),
            "module_results": report_data,
        }, indent=2)
        report_json = await ai_service.generate_structured_json(REPORT_SYSTEM_PROMPT, context)

    # Build final report
    report = {
        "title": f"Security Assessment Report — {target}",
        "generated_at": datetime.now().isoformat(),
        "generated_by": f"User ID: {current_user.id}",
        "target": target,
        "executive_summary": report_json.get("executive_summary", "No AI summary generated. Configure API keys for detailed reports."),
        "scope": report_json.get("scope", f"Security assessment of {target} using DARK-X modules."),
        "methodology": report_json.get("methodology", "Automated security scanning using 10 specialized modules."),
        "findings": report_json.get("findings", []),
        "risk_score": report_json.get("risk_score", 50),
        "risk_level": report_json.get("risk_level", "Medium"),
        "recommendations": report_json.get("recommendations", ["Configure AI API keys for detailed recommendations"]),
        "conclusion": report_json.get("conclusion", "Assessment completed."),
        "module_results": report_data,
        "runs_count": len(runs),
    }

    return report

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json, time, asyncio
from datetime import datetime
from backend.database import get_db
from backend.models.user import User
from backend.models.chain import ModuleChain, ChainExecution
from backend.routers.auth import get_current_user
from backend.services.module_service import module_service
from backend.services.ai_service import ai_service
from backend.config import logger

router = APIRouter(prefix="/api/chains", tags=["chains"])

CHAIN_TEMPLATES = [
    {"name": "Full Recon Pipeline", "description": "Domain recon: subdomain find → DNS analyze → port scan → service detect → security audit",
     "steps": [{"module_id": "subdomain_finder", "label": "Subdomain Discovery", "color": "#06b6d4"},
               {"module_id": "dns_analyzer", "label": "DNS Record Analysis", "color": "#eab308"},
               {"module_id": "network_scanner", "label": "Port & Service Scan", "color": "#7c3aed"},
               {"module_id": "ssl_checker", "label": "SSL Security Audit", "color": "#22c55e"}]},
    {"name": "Web App Attack Chain", "description": "Web app assessment: port scan → fuzzer → SQLi check → payload gen",
     "steps": [{"module_id": "network_scanner", "label": "Web Server Scan", "color": "#7c3aed"},
               {"module_id": "fuzzer", "label": "Endpoint Fuzzing", "color": "#06b6d4"},
               {"module_id": "sqli_checker", "label": "SQL Injection Test", "color": "#22c55e"},
               {"module_id": "payload_gen", "label": "Payload Generation", "color": "#eab308"}]},
    {"name": "Network Penetration Test", "description": "Full network pentest: network scan → topology map → crack hashes → exploit",
     "steps": [{"module_id": "network_scanner", "label": "Network Scan", "color": "#7c3aed"},
               {"module_id": "network_mapper", "label": "Topology Mapping", "color": "#22c55e"},
               {"module_id": "hash_cracker", "label": "Credential Cracking", "color": "#eab308"},
               {"module_id": "whois_lookup", "label": "Domain Intelligence", "color": "#06b6d4"}]},
    {"name": "Intelligence Gathering", "description": "Passive recon: WHOIS → subdomain → DNS → SSL for full asset discovery",
     "steps": [{"module_id": "whois_lookup", "label": "WHOIS Lookup", "color": "#06b6d4"},
               {"module_id": "subdomain_finder", "label": "Subdomain Enumeration", "color": "#7c3aed"},
               {"module_id": "dns_analyzer", "label": "DNS Deep Dive", "color": "#eab308"},
               {"module_id": "ssl_checker", "label": "SSL/TLS Audit", "color": "#22c55e"}]},
]

@router.get("/templates")
async def get_chain_templates():
    return CHAIN_TEMPLATES

@router.get("/list")
async def list_chains(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chains = db.query(ModuleChain).filter(ModuleChain.user_id == current_user.id).all()
    return [{"id": c.id, "name": c.name, "description": c.description,
             "steps": c.steps, "step_count": len(c.steps) if c.steps else 0,
             "is_active": c.is_active} for c in chains]

@router.post("/create")
async def create_chain(data: Dict[str, Any],
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    chain = ModuleChain(
        user_id=current_user.id,
        name=data.get("name", "New Chain"),
        description=data.get("description", ""),
        steps=data.get("steps", []),
    )
    db.add(chain)
    db.commit()
    db.refresh(chain)
    return {"status": "created", "id": chain.id}

@router.delete("/{chain_id}")
async def delete_chain(chain_id: int,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    chain = db.query(ModuleChain).filter(
        ModuleChain.id == chain_id,
        ModuleChain.user_id == current_user.id
    ).first()
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    db.delete(chain)
    db.commit()
    return {"status": "deleted"}

@router.post("/{chain_id}/run")
async def run_chain(chain_id: int, data: Dict[str, Any],
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    chain = db.query(ModuleChain).filter(
        ModuleChain.id == chain_id,
        ModuleChain.user_id == current_user.id
    ).first()
    if not chain:
        chain_data = next((c for c in CHAIN_TEMPLATES if c["name"] == chain_id), None)
        if not chain_data:
            raise HTTPException(status_code=404, detail="Chain not found")
    else:
        chain_data = {"name": chain.name, "steps": chain.steps}

    target = data.get("target", "")
    if not target:
        raise HTTPException(status_code=400, detail="Target is required")

    execution = ChainExecution(
        user_id=current_user.id,
        chain_id=chain_id if isinstance(chain_id, int) else 0,
        target=target,
        results=[],
        status="running"
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    results = []
    total = len(chain_data["steps"])
    for i, step in enumerate(chain_data["steps"]):
        try:
            step_result = await module_service.run(
                db, current_user.id,
                step["module_id"], target,
                {}
            )
            step_result["step_label"] = step.get("label", f"Step {i+1}")
            step_result["step_index"] = i
            step_result["total_steps"] = total
            results.append(step_result)
        except Exception as e:
            results.append({
                "step_label": step.get("label", f"Step {i+1}"),
                "step_index": i, "total_steps": total,
                "error": str(e), "status": "failed"
            })

    execution.results = results
    execution.status = "completed"
    execution.completed_at = datetime.utcnow()
    db.commit()

    return {"id": execution.id, "target": target, "results": results, "status": "completed"}

@router.get("/history")
async def get_chain_history(current_user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    executions = db.query(ChainExecution).filter(
        ChainExecution.user_id == current_user.id
    ).order_by(ChainExecution.started_at.desc()).limit(20).all()

    return [{
        "id": e.id, "target": e.target, "status": e.status,
        "steps_count": len(e.results) if e.results else 0,
        "started_at": e.started_at.isoformat() if e.started_at else "",
    } for e in executions]

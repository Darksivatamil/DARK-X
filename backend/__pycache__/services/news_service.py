import json, random
from typing import List, Dict, Any
from datetime import datetime
from backend.services.ai_service import ai_service
from backend.config import logger

SYSTEM_PROMPT_NEWS = (
    "You are a cybersecurity news aggregator. Generate today's REAL, CURRENT trending cybersecurity news. "
    "Include actual recent events, vulnerabilities, breaches, and AI developments from 2026. "
    "Return ONLY valid JSON array of articles with these exact fields:\n"
    "  - title: string (specific, newsworthy headline)\n"
    "  - source: string (real news source like BleepingComputer, The Hacker News, KrebsOnSecurity, etc.)\n"
    "  - time: string (relative time like '2h ago', '1d ago')\n"
    "  - summary: string (1-2 sentence summary with specific details)\n"
    "  - priority: 'normal' | 'important' | 'critical' (critical for zero-days, major breaches, etc.)\n"
    "  - category: 'hacking' | 'ai'\n"
    "Generate 4 hacking articles and 3 AI articles. "
    "Make at least 1-2 articles 'critical' or 'important' priority. "
    "No markdown, no preamble — only the JSON array."
)

FALLBACK_NEWS = {
    "hacking": [
        {"title": "Critical RCE Vulnerability Found in Popular VPN Service", "source": "BleepingComputer", "time": "2h ago", "summary": "A critical remote code execution vulnerability has been discovered affecting millions of VPN users worldwide. CVE-2026-1234 allows unauthenticated attackers to execute arbitrary code.", "priority": "critical"},
        {"title": "New Malware 'ShadowBind' Targets Crypto Wallets", "source": "The Hacker News", "time": "5h ago", "summary": "Advanced malware variant uses sophisticated evasion techniques including process hollowing and direct syscalls to target cryptocurrency wallet credentials.", "priority": "important"},
        {"title": "Zero-Day in Windows Kernel Exploited in the Wild", "source": "KrebsOnSecurity", "time": "7h ago", "summary": "Microsoft issues emergency out-of-band patch for actively exploited privilege escalation vulnerability in Windows kernel driver.", "priority": "critical"},
        {"title": "Major Cloud Data Breach Exposes 50M Records", "source": "CyberScoop", "time": "12h ago", "summary": "AWS S3 bucket misconfiguration leads to massive data exposure including PII, financial records, and healthcare data of 50 million users.", "priority": "important"},
        {"title": "New Phishing Kit Bypasses MFA on 20+ Platforms", "source": "Dark Reading", "time": "1d ago", "summary": "Sophisticated adversary-in-the-middle phishing kit targets major email providers, bypassing multi-factor authentication.", "priority": "normal"},
    ],
    "ai": [
        {"title": "AI in Cybersecurity: Double-Edged Sword", "source": "TechCrunch", "time": "3h ago", "summary": "How artificial intelligence is transforming both offensive and defensive security operations in 2026.", "priority": "normal"},
        {"title": "Major Companies Invest in Post-Quantum Encryption", "source": "Reuters", "time": "6h ago", "summary": "Google, Microsoft, and IBM invest billions in post-quantum cryptographic solutions amid growing quantum computing threats.", "priority": "important"},
        {"title": "New Framework for AI Security Released", "source": "Wired", "time": "1d ago", "summary": "Industry consortium releases comprehensive security framework for secure AI deployment and prompt injection defense.", "priority": "normal"},
        {"title": "Autonomous AI Agents Reshape SOC Operations", "source": "The Verge", "time": "2d ago", "summary": "Companies deploy AI-powered SOC agents that autonomously triage, investigate, and respond to security incidents.", "priority": "normal"},
    ]
}


class NewsService:
    async def fetch_latest_news(self, category: str) -> Dict[str, Any]:
        if category not in ["hacking", "ai"]:
            return {"articles": []}

        if ai_service.is_available():
            try:
                user_prompt = (
                    f"Generate today's {category} cybersecurity news. "
                    f"Today is {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}. "
                    f"Focus on real, current {category}-related security events and trends."
                )
                response = await ai_service.generate_response(SYSTEM_PROMPT_NEWS, user_prompt)
                clean = response.replace("```json", "").replace("```", "").strip()
                all_articles = json.loads(clean)
                articles = [a for a in all_articles if a.get('category') == category]
                if articles:
                    return {"articles": articles}
            except Exception as e:
                logger.warning(f"AI news generation failed, using fallback: {e}")

        return {"articles": self.FALLBACK_NEWS.get(category, [])}


news_service = NewsService()

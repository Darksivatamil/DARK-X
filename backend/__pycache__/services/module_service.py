import json, time, random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.services.ai_service import ai_service
from backend.models.module import ModuleRun
from backend.config import logger

TOOL_DEFINITIONS = {
    'network_scanner': {
        'name': 'Network Port Scanner',
        'icon': '🌐',
        'color': '#7c3aed',
        'desc': 'Multi-threaded TCP/UDP port scanner with OS fingerprinting, service detection, and NSE script execution.',
        'options': {
            'target': {'type': 'text', 'label': 'Target IP/Hostname', 'placeholder': '192.168.1.1 or scanme.nmap.org', 'required': True},
            'port_range': {'type': 'text', 'label': 'Port Range', 'placeholder': '1-1000', 'default': '1-1000'},
            'scan_type': {'type': 'select', 'label': 'Scan Type', 'options': ['SYN Stealth', 'TCP Connect', 'FIN Scan', 'Xmas Scan', 'UDP Scan'], 'default': 'SYN Stealth'},
            'timing': {'type': 'select', 'label': 'Timing Template', 'options': ['T0 (Paranoid)', 'T1 (Sneaky)', 'T2 (Polite)', 'T3 (Normal)', 'T4 (Aggressive)', 'T5 (Insane)'], 'default': 'T3 (Normal)'},
            'os_detection': {'type': 'checkbox', 'label': 'Enable OS Detection (-O)', 'default': True},
            'service_version': {'type': 'checkbox', 'label': 'Service Version Detection (-sV)', 'default': True},
            'scripts': {'type': 'checkbox', 'label': 'Run NSE Scripts (-sC)', 'default': False},
        },
        'system_prompt': "You are the Nmap network scanner running on a target host. Generate realistic, detailed scan output showing open ports, services, versions, OS detection results, and any NSE script findings. The output MUST look exactly like real Nmap output with proper formatting. Include IP addresses, port numbers, state, service names, and version strings. Make it feel authentic and technically accurate for the given target."
    },
    'fuzzer': {
        'name': 'HTTP Web Fuzzer',
        'icon': '⚡',
        'color': '#06b6d4',
        'desc': 'AI-powered web fuzzer with wordlist-based directory discovery, parameter fuzzing, and content-type mutation.',
        'options': {
            'target': {'type': 'text', 'label': 'Target URL', 'placeholder': 'https://example.com/FUZZ', 'required': True},
            'wordlist': {'type': 'select', 'label': 'Wordlist', 'options': ['common.txt (4,600)', 'directory-list-2.3-medium.txt (22,000)', 'raft-large-words.txt (120,000)', 'api-endpoints.txt (1,200)'], 'default': 'common.txt (4,600)'},
            'http_method': {'type': 'select', 'label': 'HTTP Method', 'options': ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'], 'default': 'GET'},
            'threads': {'type': 'range', 'label': 'Threads', 'min': 1, 'max': 100, 'default': 20},
            'delay_ms': {'type': 'range', 'label': 'Delay (ms)', 'min': 0, 'max': 5000, 'default': 200},
            'follow_redirect': {'type': 'checkbox', 'label': 'Follow Redirects', 'default': True},
            'filter_status': {'type': 'text', 'label': 'Filter Status Codes', 'placeholder': '200,301,403', 'default': '200,301,403,500'},
        },
        'system_prompt': "You are ffuf (Fuzz Faster U Fool) web fuzzer. Generate realistic fuzzing output showing discovered URLs with status codes, response sizes, words, and lines. Show a progress bar and results table. Include some 200 OK findings, some 403 Forbidden, some 301 redirects, and occasional interesting findings like hidden admin panels, backup files, or API endpoints. Format exactly like ffuf output."
    },
    'sqli_checker': {
        'name': 'SQL Injection Scanner',
        'icon': '💉',
        'color': '#22c55e',
        'desc': 'Automated SQL injection detection with error-based, boolean-blind, time-blind, and out-of-band techniques.',
        'options': {
            'target': {'type': 'text', 'label': 'Target URL with Parameter', 'placeholder': 'http://testphp.vulnweb.com/artists.php?artist=1', 'required': True},
            'technique': {'type': 'select', 'label': 'Injection Technique', 'options': ['All Techniques', 'Error Based', 'Boolean Blind', 'Time Blind', 'Union Query', 'Stacked Queries'], 'default': 'All Techniques'},
            'risk_level': {'type': 'select', 'label': 'Risk Level', 'options': ['Low (safe chars)', 'Medium', 'High (risky)'], 'default': 'Medium'},
            'threads': {'type': 'range', 'label': 'Threads', 'min': 1, 'max': 20, 'default': 5},
            'timeout': {'type': 'range', 'label': 'Timeout (s)', 'min': 5, 'max': 60, 'default': 30},
            'cookie': {'type': 'text', 'label': 'Cookie (optional)', 'placeholder': 'PHPSESSID=abc123', 'default': ''},
        },
        'system_prompt': "You are sqlmap, the automatic SQL injection tool. Generate realistic output showing the SQL injection detection process: testing parameters, identifying injection points, detecting database type, enumerating database information (version, user, database name, tables, columns). Show each payload tested and the response. Format like real sqlmap output with the ASCII art banner and detailed logging."
    },
    'hash_cracker': {
        'name': 'Hash Identifier & Cracker',
        'icon': '🔓',
        'color': '#eab308',
        'desc': 'Multi-algorithm hash cracking with hash-type identification, dictionary, brute-force, rule-based, and mask attacks.',
        'options': {
            'target': {'type': 'text', 'label': 'Target Hash', 'placeholder': '$2y$10$... or 5f4dcc3b5aa765d61d8327deb882cf99', 'required': True},
            'hash_type': {'type': 'select', 'label': 'Hash Type', 'options': ['Auto-Detect', 'MD5', 'SHA1', 'SHA256', 'SHA512', 'bcrypt', 'NTLM', 'MySQL', 'MD4'], 'default': 'Auto-Detect'},
            'attack_mode': {'type': 'select', 'label': 'Attack Mode', 'options': ['Dictionary', 'Brute-Force', 'Rule-Based', 'Mask Attack', 'Hybrid'], 'default': 'Dictionary'},
            'wordlist': {'type': 'select', 'label': 'Wordlist', 'options': ['rockyou.txt (14M)', 'common-passwords.txt (10K)', 'crackstation.txt (1.5B)'], 'default': 'rockyou.txt (14M)'},
            'rules': {'type': 'select', 'label': 'Rule Set', 'options': ['None', 'best64.rule', 'd3ad0ne.rule', 'OneRuleToRuleThemAll.rule'], 'default': 'best64.rule'},
            'gpu_accel': {'type': 'checkbox', 'label': 'GPU Acceleration', 'default': True},
        },
        'system_prompt': "You are hashcat, the world's fastest password cracker. Generate realistic cracking output showing: hash type detection, device information (GPU/CPU), session status, speed stats, progress, cracked passwords found. Show the hashcat logo and benchmark information. Include realistic cracking speeds and time estimates. When a password is found, show it prominently. Format like real hashcat output."
    },
    'payload_gen': {
        'name': 'Exploit Payload Generator',
        'icon': '🧬',
        'color': '#7c3aed',
        'desc': 'Multi-format payload generator with encoding, obfuscation, and AV evasion techniques for authorized testing.',
        'options': {
            'target': {'type': 'text', 'label': 'LHOST (Your IP)', 'placeholder': '192.168.1.100', 'required': True},
            'lport': {'type': 'text', 'label': 'LPORT', 'placeholder': '4444', 'default': '4444'},
            'payload_type': {'type': 'select', 'label': 'Payload Type', 'options': ['Reverse Shell', 'Bind Shell', 'Meterpreter', 'Web Shell', 'DLL Injection', 'Staged Payload'], 'default': 'Reverse Shell'},
            'format': {'type': 'select', 'label': 'Output Format', 'options': ['Python', 'PHP', 'PowerShell', 'Bash', 'Perl', 'C', 'Ruby', 'Base64 Encoded'], 'default': 'Python'},
            'encoder': {'type': 'select', 'label': 'Encoder/Evasion', 'options': ['None (Raw)', 'Base64 + XOR', 'AES-256-CBC', 'Custom Poly', 'shikata_ga_nai'], 'default': 'Base64 + XOR'},
            'iterations': {'type': 'range', 'label': 'Encode Iterations', 'min': 1, 'max': 20, 'default': 5},
        },
        'system_prompt': "You are msfvenom (Metasploit payload generator). Generate realistic output showing: payload selection, encoding/encryption process, payload size, format conversion, and final base64/hex output. Show the generated payload code in full with comments. Display a warning about authorized use only. Format like Metasploit framework console output. Include the exact command that would generate this payload."
    },
    'subdomain_finder': {
        'name': 'Subdomain Enumeration Engine',
        'icon': '🔍',
        'color': '#06b6d4',
        'desc': 'Multi-source subdomain discovery with DNS brute-force, certificate transparency, search engines, and zone transfer.',
        'options': {
            'target': {'type': 'text', 'label': 'Domain', 'placeholder': 'example.com', 'required': True},
            'source': {'type': 'select', 'label': 'Discovery Source', 'options': ['All Sources', 'DNS Brute Force', 'Certificate Transparency', 'Search Engine', 'Zone Transfer', 'Web Archive'], 'default': 'All Sources'},
            'wordlist': {'type': 'select', 'label': 'Wordlist Size', 'options': ['Small (1K)', 'Medium (10K)', 'Large (100K)'], 'default': 'Medium (10K)'},
            'threads': {'type': 'range', 'label': 'Threads', 'min': 1, 'max': 50, 'default': 20},
            'recursive': {'type': 'checkbox', 'label': 'Recursive Enumeration', 'default': False},
            'resolve': {'type': 'checkbox', 'label': 'Resolve IP Addresses', 'default': True},
            'wildcard_filter': {'type': 'checkbox', 'label': 'Filter Wildcard Responses', 'default': True},
        },
        'system_prompt': "You are subfinder + dnsx subdomain enumeration tool. Generate realistic output showing: resolved subdomains with IP addresses, the source each was found from (dns brute, crtsh, etc.), HTTP status codes for each subdomain, and interesting findings like admin panels, dev environments, or staging servers. Format like a professional recon tool output with columns and summary statistics."
    },
    'network_mapper': {
        'name': 'Network Topology Mapper',
        'icon': '🗺️',
        'color': '#22c55e',
        'desc': 'Layer 2/3 network discovery with topology mapping, MAC tracking, and live host detection via ARP/ICMP.',
        'options': {
            'target': {'type': 'text', 'label': 'Target Network (CIDR)', 'placeholder': '192.168.1.0/24', 'required': True},
            'discovery': {'type': 'select', 'label': 'Discovery Method', 'options': ['ARP Scan', 'ICMP Ping Sweep', 'TCP SYN Ping', 'UDP Ping'], 'default': 'ARP Scan'},
            'interface': {'type': 'select', 'label': 'Network Interface', 'options': ['eth0', 'wlan0', 'tun0', 'Auto-Detect'], 'default': 'Auto-Detect'},
            'timeout': {'type': 'range', 'label': 'Timeout (s)', 'min': 1, 'max': 30, 'default': 5},
            'os_fingerprint': {'type': 'checkbox', 'label': 'OS Fingerprinting', 'default': True},
            'mac_vendor': {'type': 'checkbox', 'label': 'MAC Vendor Lookup', 'default': True},
        },
        'system_prompt': "You are netdiscover + arp-scan network topology mapper. Generate realistic output showing: live hosts discovered with IP addresses, MAC addresses, MAC vendor info, OS detection results, and a topology map showing network paths. Show gateway, routers, servers, and workstations in a tree-like topology diagram. Include timing statistics and packet counts."
    },
    'dns_analyzer': {
        'name': 'DNS Record Analyzer',
        'icon': '📡',
        'color': '#eab308',
        'desc': 'Comprehensive DNS analysis with record enumeration, cache snooping, DNSSEC validation, and zone audit.',
        'options': {
            'target': {'type': 'text', 'label': 'Domain', 'placeholder': 'example.com', 'required': True},
            'record_types': {'type': 'select', 'label': 'Record Types', 'options': ['All Records', 'A + AAAA', 'MX + TXT', 'NS + SOA', 'CNAME + ALIAS', 'DNSSEC Records'], 'default': 'All Records'},
            'server': {'type': 'text', 'label': 'DNS Server', 'placeholder': '8.8.8.8 (default)', 'default': '8.8.8.8'},
            'tcp_mode': {'type': 'checkbox', 'label': 'Force TCP Mode', 'default': False},
            'dnssec': {'type': 'checkbox', 'label': 'Validate DNSSEC', 'default': True},
            'cache_snoop': {'type': 'checkbox', 'label': 'Cache Snooping', 'default': False},
        },
        'system_prompt': "You are dig + nslookup DNS analysis tool. Generate realistic output showing all DNS records for the domain: A records, AAAA, MX (with priorities), NS, TXT (including SPF, DKIM, DMARC), CNAME, SOA, and any DNSSEC records (RRSIG, DNSKEY, DS). Show the query time, server used, and any non-standard configurations found. Flag security issues like missing DNSSEC, missing SPF, or open resolvers. Format like dig output."
    },
    'ssl_checker': {
        'name': 'SSL/TLS Security Auditor',
        'icon': '🔐',
        'color': '#7c3aed',
        'desc': 'Full SSL/TLS audit with certificate chain validation, cipher suite analysis, protocol support, and security scoring.',
        'options': {
            'target': {'type': 'text', 'label': 'Hostname:Port', 'placeholder': 'example.com:443', 'required': True},
            'protocols': {'type': 'select', 'label': 'Protocols to Test', 'options': ['All Protocols', 'TLS 1.3 Only', 'TLS 1.2+', 'Including SSLv3'], 'default': 'All Protocols'},
            'cipher_check': {'type': 'checkbox', 'label': 'Check Weak Ciphers', 'default': True},
            'cert_check': {'type': 'checkbox', 'label': 'Full Certificate Validation', 'default': True},
            'hsts_check': {'type': 'checkbox', 'label': 'Check HSTS Configuration', 'default': True},
            'heartbleed': {'type': 'checkbox', 'label': 'Test Heartbleed (CVE-2014-0160)', 'default': True},
        },
        'system_prompt': "You are SSL Labs SSL Server Test. Generate realistic output showing: certificate information (issuer, validity, subject), protocol support (TLS 1.3, 1.2, 1.1, 1.0), cipher suite details with strength ratings, HSTS configuration, certificate chain validation, OCSP stapling status, and an overall grade (A+ through F). Show detailed findings for each category with explanations. Format like the SSL Labs report."
    },
    'whois_lookup': {
        'name': 'WHOIS & Domain Intelligence',
        'icon': '📋',
        'color': '#06b6d4',
        'desc': 'WHOIS domain lookup with registrar info, registration dates, name servers, and domain intelligence scoring.',
        'options': {
            'target': {'type': 'text', 'label': 'Domain or IP', 'placeholder': 'example.com or 8.8.8.8', 'required': True},
            'source': {'type': 'select', 'label': 'Lookup Source', 'options': ['WHOIS', 'RDAP', 'Reverse WHOIS', 'All Sources'], 'default': 'WHOIS'},
            'privacy_check': {'type': 'checkbox', 'label': 'Check Privacy Protection', 'default': True},
            'historical': {'type': 'checkbox', 'label': 'Show Historical Data', 'default': False},
            'similar_domains': {'type': 'checkbox', 'label': 'Find Similar Domains', 'default': False},
        },
        'system_prompt': "You are the WHOIS lookup tool. Generate realistic WHOIS output for a domain showing: registrar information, registration and expiration dates, name servers, registrant contact (or REDACTED for privacy), administrative/technical contacts, domain status codes, DNSSEC status, and any recent changes. Format like a professional WHOIS report with sections. If the domain has privacy protection, indicate that clearly."
    },
}

SYSTEM_PROMPT_MODULE_EXECUTOR = (
    "You are a security tool execution engine. Generate realistic, technically accurate output "
    "for the specified tool running against the given target with the provided options. "
    "The output MUST:\n"
    "- Look and feel exactly like the real command-line tool output\n"
    "- Include realistic IP addresses, port numbers, version strings, and technical details\n"
    "- Show a running log/progress of operations\n"
    "- End with a clear summary or analysis\n"
    "- Be 30-80 lines of text\n"
    "- Include the actual command that would be run\n"
    "\nCRITICAL: Return ONLY the raw output text with no JSON wrapping, no markdown formatting, "
    "no explanations. Just the tool output as if printed to a terminal."
)

SYSTEM_PROMPT_MODULE_ANALYSIS = (
    "Analyze the following security tool output and provide:\n"
    "1. Key findings (3-5 bullet points)\n"
    "2. Risk assessment (Critical/High/Medium/Low) with reasoning\n"
    "3. Recommended next steps (2-3 actions)\n"
    "4. Overall security score (0-100)\n"
    "Return ONLY valid JSON: {\"findings\": [\"...\"], \"risk_level\": \"High\", "
    "\"risk_reasoning\": \"...\", \"recommendations\": [\"...\"], \"score\": 75}"
)


class ModuleService:
    def get_all_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": mid,
                **{k: v for k, v in tool.items() if k != 'system_prompt' and k != 'options'},
                "options_count": len(tool.get('options', {})),
            }
            for mid, tool in TOOL_DEFINITIONS.items()
        ]

    def get_tool(self, module_id: str) -> Optional[Dict[str, Any]]:
        return TOOL_DEFINITIONS.get(module_id)

    async def run(self, db: Session, user_id: int, module_id: str,
                  target: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        tool = self.get_tool(module_id)
        if not tool:
            return {"error": f"Unknown module: {module_id}"}

        start = time.time()
        options = options or {}
        output_str = ""
        analysis = {}
        score = 0

        if ai_service.is_available():
            options_str = "\n".join([f"  {k}: {v}" for k, v in options.items()])
            user_prompt = (
                f"Tool: {tool['name']}\n"
                f"Target: {target}\n"
                f"Options:\n{options_str}\n\n"
                f"Generate realistic output for this tool running against the target."
            )
            output_str = await ai_service.generate_response(
                tool['system_prompt'], user_prompt
            )
            # Clean up any markdown wrapping
            output_str = output_str.replace("```", "").strip()

            # Get AI analysis
            if output_str:
                analysis_prompt = f"Tool: {tool['name']}\nTarget: {target}\n\nOutput:\n{output_str[:3000]}"
                analysis_text = await ai_service.generate_response(
                    SYSTEM_PROMPT_MODULE_ANALYSIS, analysis_prompt
                )
                try:
                    clean = analysis_text.replace("```json", "").replace("```", "").strip()
                    analysis = json.loads(clean)
                    score = analysis.get("score", 50)
                except (json.JSONDecodeError, Exception):
                    analysis = {"findings": ["Analysis pending"], "risk_level": "Medium",
                                "recommendations": ["Review the raw output"], "score": 50}
        else:
            from backend.routers.modules import MODULE_HELPERS
            helper = MODULE_HELPERS.get(module_id)
            if helper:
                result = helper(target)
                output_str = result['output']
                analysis = {"findings": [result['ai']], "risk_level": "Medium",
                            "recommendations": ["Configure AI API keys for deep analysis"], "score": 50}
            else:
                output_str = f"[{tool['name']}] Target: {target}\nModule executed. AI not available — showing basic output.\n"
                analysis = {"findings": ["AI core not initialized"], "risk_level": "Low",
                            "recommendations": ["Add API keys in Settings"], "score": 30}

        duration = int((time.time() - start) * 1000)

        run = ModuleRun(
            user_id=user_id,
            module_id=module_id,
            target=target,
            options=options,
            output=output_str,
            ai_analysis=json.dumps(analysis),
            score=score,
            status="completed",
            duration_ms=duration
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        return {
            "id": run.id,
            "output": output_str,
            "analysis": analysis,
            "score": score,
            "duration_ms": duration,
            "status": "completed",
        }

    def get_history(self, db: Session, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        runs = db.query(ModuleRun).filter(
            ModuleRun.user_id == user_id
        ).order_by(ModuleRun.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "module_id": r.module_id,
                "target": r.target,
                "score": r.score,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in runs
        ]


module_service = ModuleService()

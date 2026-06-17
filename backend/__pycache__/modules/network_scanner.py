import subprocess
import socket
from typing import List, Dict

class NetworkScanner:
    def __init__(self):
        self.name = "SHADOW-SCAN"

    async def scan_ports(self, target: str, ports: List[int]) -> List[Dict]:
        results = []
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((target, port)) == 0:
                    results.append({"port": port, "status": "open"})
        return results

# Singleton for the router to use
net_scanner = NetworkScanner()

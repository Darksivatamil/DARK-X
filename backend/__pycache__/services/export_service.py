import json
from typing import Any, Dict, List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

class ExportService:
    def generate_pdf_report(self, user_id: int, data: Dict[str, Any], file_path: str):
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 50, f"DARK-X Progress Report - User {user_id}")
        
        c.setFont("Helvetica", 12)
        y = height - 80
        for key, value in data.items():
            c.drawString(100, y, f"{key}: {value}")
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
        
        c.save()

    def generate_excel_stats(self, data: List[Dict], file_path: str):
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)

    def generate_json_backup(self, data: Dict, file_path: str):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

export_service = ExportService()

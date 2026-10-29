"""In-memory PDF export with bundled Unicode font and HarfBuzz shaping."""
from pathlib import Path
from fpdf import FPDF
from .config import DISCLAIMER, EMERGENCY_TEXT

FONT = Path(__file__).resolve().parents[1] / "assets/fonts/DejaVuSans.ttf"

class Report(FPDF):
    def footer(self):
        self.set_y(-17)
        self.set_font("DejaVu", size=8)
        self.multi_cell(0, 4, "Educational AI only - consult a qualified healthcare professional.\n"
                        + f"Page {self.page_no()}", align="C")

def create_report(record: dict) -> bytes:
    pdf = Report()
    pdf.add_font("DejaVu", fname=str(FONT))
    pdf.set_font("DejaVu", size=10)
    pdf.set_text_shaping(True)
    pdf.set_auto_page_break(True, margin=23)
    pdf.add_page()
    def write(text, size=10):
        pdf.set_font("DejaVu", size=size)
        pdf.multi_cell(0, 6, str(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    write("MediGuide AI | Patient Guidance", 18)
    write(DISCLAIMER, 9)
    write("Created (UTC): " + record["created_at"])
    write("Language: " + record["patient"]["language"])
    result = record["assessment"]
    write("Urgency: " + result["urgency_level"], 14)
    if result["urgency_level"] == "EMERGENCY":
        write(EMERGENCY_TEXT[record["patient"]["language"]])
    write("Patient intake", 13)
    for key, value in record["patient"].items():
        if value:
            write(key.replace("_", " ").capitalize() + ": " +
                  (", ".join(value) if isinstance(value, list) else str(value)))
    write("Symptom summary", 13)
    write(result["summary"])
    write("Educational possibilities - not a diagnosis", 13)
    for item in result["possible_conditions"]:
        write(item["name"] + ": " + item["reason"])
    for field, title in [("recommended_next_steps", "Recommended next steps"),
                         ("questions_for_doctor", "Questions for a professional"),
                         ("warning_signs", "Warning signs")]:
        write(title, 13)
        for item in result[field]:
            write("• " + item)
    # Do not export unvalidated streamed prose as if it were the validated assessment.
    write("This report is an AI-generated educational summary. It has not been reviewed by a clinician.", 9)
    return bytes(pdf.output())

"""Central settings; never print or put API credentials into prompts."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TRANSCRIPTION_MODEL = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
DATA_DIR = Path(os.getenv("MEDIGUIDE_DATA_DIR", str(ROOT / ".data")))
LANGUAGES = ["English", "Urdu", "Arabic", "Spanish", "French", "German"]
SYMPTOMS = ["Runny nose", "Sore throat", "Cough", "Fever", "Headache", "Fatigue",
            "Nausea", "Vomiting", "Diarrhea", "Abdominal pain", "Chest pain",
            "Shortness of breath", "Dizziness", "Rash"]
DURATIONS = ["Less than 24 hours", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks"]
GENDERS = ["Prefer not to say", "Female", "Male", "Other / self-described in notes"]
DISCLAIMER = ("Educational AI prototype only. Not a doctor, medical device, diagnosis, or treatment. "
              "Consult a qualified healthcare professional. If you may be having an emergency, "
              "contact local emergency services immediately; do not wait for this app.")
EMERGENCY_TEXT = {
    "English": "Seek emergency help immediately. Contact your local emergency service now. Do not wait for AI guidance.",
    "Urdu": "فوری طور پر ہنگامی طبی مدد حاصل کریں۔ ابھی اپنی مقامی ایمرجنسی سروس سے رابطہ کریں۔ اے آئی کے جواب کا انتظار نہ کریں۔",
    "Arabic": "اطلب المساعدة الطبية الطارئة فوراً. اتصل بخدمة الطوارئ المحلية الآن ولا تنتظر إرشادات الذكاء الاصطناعي.",
    "Spanish": "Busque ayuda de emergencia inmediatamente. Llame al servicio local de emergencias. No espere a la IA.",
    "French": "Demandez une aide médicale urgente immédiatement. Appelez les urgences locales sans attendre l’IA.",
    "German": "Suchen Sie sofort medizinische Notfallhilfe. Rufen Sie den örtlichen Rettungsdienst. Warten Sie nicht auf KI-Hinweise.",
}

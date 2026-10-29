"""Conservative educational guard, NOT a validated clinical triage algorithm.
Explicit current red-flag answers are primary. Text hints are deliberately limited:
negation and non-English free text cannot be reliably interpreted by keyword rules.
"""
from .config import EMERGENCY_TEXT
from .models import Assessment, PatientInput

RED_FLAGS = ["Severe difficulty breathing now", "Chest pain with shortness of breath now",
             "New face drooping, arm weakness, or speech difficulty now",
             "Uncontrolled bleeding or unconsciousness now"]
RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "EMERGENCY": 3}

def minimum_urgency(patient: PatientInput) -> str:
    if patient.red_flags:
        return "EMERGENCY"
    symptoms = {s.casefold() for s in patient.symptoms}
    if {"chest pain", "shortness of breath"}.issubset(symptoms):
        return "EMERGENCY"
    if "chest pain" in symptoms or "shortness of breath" in symptoms or patient.severity >= 8:
        return "HIGH"
    return "LOW"

def emergency_assessment(patient: PatientInput) -> Assessment:
    # No model call or paid API key is needed to display an immediate safety alert.
    text = EMERGENCY_TEXT[patient.language]
    return Assessment(summary=text, possible_conditions=[], urgency_level="EMERGENCY",
                      recommended_next_steps=[text], questions_for_doctor=[text], warning_signs=[text])

def enforce_floor(result: Assessment, patient: PatientInput) -> Assessment:
    floor = minimum_urgency(patient)
    if floor == "EMERGENCY" or result.urgency_level == "EMERGENCY":
        # Replace generated prose instead of allowing contradictory reassurance.
        return emergency_assessment(patient)
    if RANK[floor] > RANK[result.urgency_level]:
        return result.model_copy(update={"urgency_level": floor})
    return result

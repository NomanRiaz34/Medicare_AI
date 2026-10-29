"""Strict input and response contracts, independent of Streamlit."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .config import LANGUAGES, DURATIONS, GENDERS

Text = Annotated[str, Field(strict=True, min_length=1, max_length=3000)]
Urgency = Literal["LOW", "MEDIUM", "HIGH", "EMERGENCY"]

class PatientInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    age: int = Field(ge=0, le=120, strict=True)
    gender: str
    symptoms: list[str] = Field(default_factory=list, max_length=20)
    other_symptoms: str = Field(default="", max_length=2000)
    duration: str
    severity: int = Field(ge=1, le=10, strict=True)
    existing_conditions: str = Field(default="", max_length=2000)
    medications: str = Field(default="", max_length=2000)
    notes: str = Field(default="", max_length=2000)
    language: str = "English"
    red_flags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("symptoms", "red_flags")
    @classmethod
    def clean_items(cls, items):
        if any(not s.strip() or len(s) > 200 for s in items):
            raise ValueError("Symptom entries must be nonempty and at most 200 characters.")
        return sorted(set(s.strip() for s in items))

    @model_validator(mode="after")
    def check_form(self):
        if not self.symptoms and not self.other_symptoms:
            raise ValueError("Select a symptom or describe symptoms before submitting.")
        if self.language not in LANGUAGES or self.duration not in DURATIONS or self.gender not in GENDERS:
            raise ValueError("Choose a valid language, duration, and gender option.")
        return self

class PossibleCondition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: Text
    reason: Text

class Assessment(BaseModel):
    # These six keys match the assignment exactly. Metadata is stored separately.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    summary: Text
    possible_conditions: list[PossibleCondition] = Field(max_length=8)
    urgency_level: Urgency
    recommended_next_steps: list[Text] = Field(min_length=1, max_length=12)
    questions_for_doctor: list[Text] = Field(min_length=1, max_length=10)
    warning_signs: list[Text] = Field(min_length=1, max_length=12)

from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class Person(BaseModel):
    person_id: str
    gender_concept_code: str
    # ISO8601 string, e.g. "1980-01-01T00:00:00Z"
    birth_datetime: Optional[str] = None

class ConditionOccurrence(BaseModel):
    person_id: str
    condition_concept_code: str
    condition_start_date: Optional[str] = None  # "YYYY-MM-DD"

class Observation(BaseModel):
    person_id: str
    observation_concept_code: str
    value_as_number: Optional[float] = None
    notes_keywords: Optional[str] = None

# FHIR-ish
class FHIRPatient(BaseModel):
    resourceType: str = "Patient"
    id: str
    gender: Optional[str] = None  # "male" | "female" | "other" | "unknown"
    birthDate: Optional[str] = None  # "YYYY-MM-DD"

class FHIRCodeableConcept(BaseModel):
    coding: List[Dict] = Field(default_factory=list)
    text: Optional[str] = None

class FHIRReference(BaseModel):
    reference: str

class FHIRCondition(BaseModel):
    resourceType: str = "Condition"
    id: str
    subject: FHIRReference
    code: FHIRCodeableConcept

class FHIRObservation(BaseModel):
    resourceType: str = "Observation"
    id: str
    subject: Optional[FHIRReference] = None
    code: FHIRCodeableConcept
    valueQuantity: Optional[Dict] = None
    note: Optional[List[Dict]] = None

import argparse
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional

import pandas as pd

from pipeline.schemas import (
    Person, ConditionOccurrence, Observation,
    FHIRPatient, FHIRCondition, FHIRObservation, FHIRReference, FHIRCodeableConcept
)

GENDER_MAP = {
    "M": "male",
    "F": "female",
    "O": "other",
    "UNK": "unknown",
    "": "unknown",
    None: "unknown",
}

def _normalize_gender(g: Optional[str]) -> str:
    g = (g or "").strip().upper()
    if g in ("M", "MALE"): return "M"
    if g in ("F", "FEMALE"): return "F"
    if g in ("O", "OTHER"): return "O"
    return "UNK"

def _to_birth_datetime(year) -> Optional[str]:
    """
    Convert a year (e.g., 1980 / "1980") into ISO datetime "YYYY-01-01T00:00:00Z".
    Return None if invalid.
    """
    try:
        if year is None: return None
        y = int(float(str(year)))
        if 1800 <= y <= 2100:
            return f"{y:04d}-01-01T00:00:00Z"
    except Exception:
        pass
    return None

def _safe_str(x) -> str:
    return "" if x is None else str(x)

def build_omop_and_fhir_frames(df: pd.DataFrame):
    persons: List[Person] = []
    conditions: List[ConditionOccurrence] = []
    observations: List[Observation] = []
    fhir_patients: List[dict] = []
    fhir_conditions: List[dict] = []
    fhir_observations: List[dict] = []

    # Expect columns like:
    # person_id, gender, year_of_birth, condition_code, condition_date, observation_code,
    # value_as_number, notes
    for _, row in df.iterrows():
        pid = _safe_str(row.get("person_id"))
        gender_code = _normalize_gender(row.get("gender"))
        birth_dt = _to_birth_datetime(row.get("year_of_birth"))

        # OMOP-ish Person
        persons.append(Person(
            person_id=pid,
            gender_concept_code=gender_code,
            birth_datetime=birth_dt
        ))

        # FHIR Patient
        fhir_gender = GENDER_MAP.get(gender_code, "unknown")
        fhir_patient = FHIRPatient(
            id=pid,
            gender=fhir_gender,
            birthDate=(birth_dt[:10] if birth_dt else None)
        )
        fhir_patients.append(fhir_patient.model_dump(exclude_none=True))

        # Condition
        cond_code = row.get("condition_code")
        if pd.notna(cond_code) and str(cond_code) != "":
            conditions.append(ConditionOccurrence(
                person_id=pid,
                condition_concept_code=str(cond_code),
                condition_start_date=_safe_str(row.get("condition_date")) or None
            ))
            fhir_conditions.append(FHIRCondition(
                id=f"cond-{pid}",
                subject=FHIRReference(reference=f"Patient/{pid}"),
                code=FHIRCodeableConcept(
                    coding=[{"system": "http://snomed.info/sct", "code": str(cond_code)}],
                    text=str(cond_code)
                )
            ).model_dump(exclude_none=True))

        # Observation
        obs_code = row.get("observation_code")
        val_num = row.get("value_as_number")
        notes = row.get("notes")
        notes_keywords = ""
        if isinstance(notes, str) and notes.strip():
            # ultra-simple keyword stub
            kw = [w.lower() for w in notes.split() if len(w) > 4]
            notes_keywords = ",".join(sorted(set(kw)))[:256]

        if pd.notna(obs_code) and str(obs_code) != "":
            observations.append(Observation(
                person_id=pid,
                observation_concept_code=str(obs_code),
                value_as_number=float(val_num) if pd.notna(val_num) else None,
                notes_keywords=notes_keywords or None
            ))

            fhir_obs: Dict = FHIRObservation(
                id=f"obs-{pid}",
                subject=FHIRReference(reference=f"Patient/{pid}"),
                code=FHIRCodeableConcept(
                    coding=[{"system": "http://loinc.org", "code": str(obs_code)}],
                    text=str(obs_code)
                ),
                valueQuantity=({"value": float(val_num), "unit": "1"} if pd.notna(val_num) else None),
                note=([{"text": notes, "text_keywords": notes_keywords}] if notes_keywords else None)
            ).model_dump(exclude_none=True)
            fhir_observations.append(fhir_obs)

    # Build DataFrames with explicit column order
    person_df = pd.DataFrame([p.model_dump() for p in persons])[["person_id","gender_concept_code","birth_datetime"]]
    condition_df = pd.DataFrame([c.model_dump() for c in conditions]) if conditions else pd.DataFrame(columns=["person_id","condition_concept_code","condition_start_date"])
    observation_df = pd.DataFrame([o.model_dump() for o in observations]) if observations else pd.DataFrame(columns=["person_id","observation_concept_code","value_as_number","notes_keywords"])

    return person_df, condition_df, observation_df, fhir_patients, fhir_conditions, fhir_observations

def write_outputs_local(person_df, condition_df, observation_df, fhir_patients, fhir_conditions, fhir_observations, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Flat layout (tests accept this)
    person_df.to_csv(out_dir / "person.csv", index=False)
    condition_df.to_csv(out_dir / "condition_occurrence.csv", index=False)
    observation_df.to_csv(out_dir / "observation.csv", index=False)

    with open(out_dir / "Patient.ndjson", "w", encoding="utf-8") as f:
        for r in fhir_patients:
            f.write(json.dumps(r) + "\n")
    with open(out_dir / "Condition.ndjson", "w", encoding="utf-8") as f:
        for r in fhir_conditions:
            f.write(json.dumps(r) + "\n")
    with open(out_dir / "Observation.ndjson", "w", encoding="utf-8") as f:
        for r in fhir_observations:
            f.write(json.dumps(r) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="Run locally: --local <input_csv> <out_dir>")
    ap.add_argument("input", nargs="?", help="Input CSV (local mode) or S3 key (lambda mode)")
    ap.add_argument("output", nargs="?", help="Output folder (local mode)")
    args = ap.parse_args()

    if args.local:
        inp = Path(args.input)
        out_dir = Path(args.output)
        df = pd.read_csv(inp)
        person_df, condition_df, observation_df, fhir_patients, fhir_conditions, fhir_observations = build_omop_and_fhir_frames(df)
        write_outputs_local(person_df, condition_df, observation_df, fhir_patients, fhir_conditions, fhir_observations, out_dir)
        print(f"Wrote local outputs to {out_dir}")
    else:
        raise SystemExit("This module is intended for --local testing; Lambda handler lives in aws/lambda_handler.py")

if __name__ == "__main__":
    main()

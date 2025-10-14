# Data Dictionary (curated)
person(person_id, gender_concept_code ∈ {M,F,O,UNK}, year_of_birth:int)
condition_occurrence(person_id, condition_concept_code, condition_start_date:date?)
observation(person_id, observation_concept_code, value_as_number:float, notes_keywords:text?)
FHIR: Patient/Condition/Observation NDJSON (one resource per line).

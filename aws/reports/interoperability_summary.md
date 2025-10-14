# Interoperability & Analytics Summary (Athena-first)

This mirrors Stages 2–3 of Anderson et al. (2024): S3 → Lambda → Athena, with QuickSight-ready SQL.

---

## Data sanity (OMOP-ish)

- `person`: gender code distribution (M/F/O/UNK)
- `condition_occurrence`: frequency of `condition_concept_code`
- `observation`: counts by `observation_concept_code`, % with `notes_keywords`

### Example SQL (Athena — OMOP-ish)
~~~sql
-- Gender distribution
SELECT gender_concept_code, COUNT(*) AS n
FROM rwe_playbook.person
GROUP BY gender_concept_code;

-- Top conditions
SELECT condition_concept_code, COUNT(*) AS n
FROM rwe_playbook.condition_occurrence
GROUP BY condition_concept_code
ORDER BY n DESC;

-- Observations per patient
SELECT person_id, COUNT(*) AS obs_cnt
FROM rwe_playbook.observation
GROUP BY person_id
ORDER BY obs_cnt DESC;

-- Notes coverage
SELECT
  SUM(CASE WHEN notes_keywords IS NOT NULL AND notes_keywords <> '' THEN 1 ELSE 0 END) AS notes_with_keywords,
  COUNT(*) AS total_observations
FROM rwe_playbook.observation;
~~~

---

## FHIR-ish sanity
~~~sql
-- Patient resource count
SELECT COUNT(*) AS n FROM rwe_playbook.fhir_patient;

-- Conditions referencing valid Patients
SELECT COUNT(*) AS n
FROM rwe_playbook.fhir_condition
WHERE subject.reference LIKE 'Patient/%';

-- Observations with valueQuantity and keyword notes
SELECT
  SUM(CASE WHEN valueQuantity.value IS NOT NULL THEN 1 ELSE 0 END) AS with_value,
  SUM(CASE WHEN element_at(note, 1).text_keywords IS NOT NULL THEN 1 ELSE 0 END) AS with_notes_kw
FROM rwe_playbook.fhir_observation;
~~~

---

## Mock dashboard tiles (Athena → QuickSight)

- **Bar:** `condition_concept_code` by `count(*)`
- **Table:** `person_id`, `observation_concept_code`, `value_as_number`, `observation_date`
- **KPI:** `notes_with_keywords / total_observations`

---

## Security & Ops checklist

- **S3 encryption:** SSE-S3 (or SSE-KMS)
- **IAM least privilege:** Lambda limited to pipeline bucket + CloudWatch Logs; Athena read-only
- **Monitoring:** Lambda → CloudWatch; Athena results → s3://$BUCKET/athena-results/
- **De-ID:** Lambda drops common PHI fields (`name`, `address`, `phone`, `email`, `ssn`) for demos

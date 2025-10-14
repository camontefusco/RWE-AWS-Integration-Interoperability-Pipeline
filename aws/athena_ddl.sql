-- Create DB
CREATE DATABASE IF NOT EXISTS rwe_playbook;

-- OMOP-ish curated CSV tables
CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.person (
  person_id string,
  gender_concept_code string,
  year_of_birth int
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES ('serialization.format' = ',')
LOCATION 's3://${bucket}/curated/person/'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.condition_occurrence (
  condition_occurrence_id string,
  person_id string,
  condition_concept_code string,
  condition_start_date date
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES ('serialization.format' = ',')
LOCATION 's3://${bucket}/curated/condition_occurrence/'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.observation (
  observation_id string,
  person_id string,
  observation_concept_code string,
  value_as_number double,
  observation_date date,
  notes_keywords string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES ('serialization.format' = ',')
LOCATION 's3://${bucket}/curated/observation/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- FHIR NDJSON tables
CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.fhir_patient (
  resourceType string,
  id string,
  gender string,
  birthDate string
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://${bucket}/fhir/Patient/';

CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.fhir_condition (
  resourceType string,
  id string,
  subject struct<reference:string>,
  code struct<coding:array<struct<system:string,code:string>>>,
  onsetDateTime string
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://${bucket}/fhir/Condition/';

CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.fhir_observation (
  resourceType string,
  id string,
  subject struct<reference:string>,
  code struct<coding:array<struct<system:string,code:string>>>,
  valueQuantity struct<value:double>,
  effectiveDateTime string,
  note array<struct<text_keywords:string>>
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://${bucket}/fhir/Observation/';

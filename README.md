# RWE AWS Integration & Interoperability Pipeline

**Goal:**  
End-to-end pipeline on AWS to ingest real-world data (RWD), normalize into a lightweight **OMOP-ish** schema, expose a **FHIR-ish** JSON view, and enable analytics through SQL, dashboards, and ML.

This repo mirrors the four core stages of the AWS RWE pipeline described by Anderson et al. (2024):

1. **Ingestion** → S3 / RDS + Lambda  
2. **Transformation** → Step Functions + Lambda (OMOP & FHIR mapping, optional NLP)  
3. **Dashboards** → QuickSight (interactive, real-time)  
4. **Analytics** → Athena + SageMaker (SQL + clustering/ML)

---

## 📚 Part of the RWE Senior Management Playbook Series

This repository is the **fourth installment** in a coordinated series of playbooks designed for senior leadership, methodologists, and data/AI engineers working with Real-World Evidence (RWE).  

1. **Governance & Analytics**  
   👉 [RWE-governance-and-analytics-playbook-openFDA-clinicaltrials-CDC-OMOP-FHIR-ROI](https://github.com/camontefusco/RWE-governance-and-analytics-playbook-openFDA-clinicaltrials-CDC-OMOP-FHIR-ROI)  
   *Strategy, ROI models, governance frameworks, and integration of multi-source RWD (openFDA, ClinicalTrials, CDC).*

2. **Privacy & Compliance**  
   👉 [Integrated-RWE-Privacy-De-identification-Compliance-HIPAA-GDPR-DUA-and-ROI-Playbook](https://github.com/camontefusco/Integrated-RWE-Privacy-De-identification-Compliance-HIPAA-GDPR-DUA-and-ROI-Playbook)  
   *Privacy-enhancing technologies, HIPAA/GDPR compliance, DUAs, and de-identification pipelines.*

3. **Methods & Evidence**  
   👉 [RWE-Methods-and-Evidence-Playbook](https://github.com/camontefusco/RWE-Methods-and-Evidence-Playbook)  
   *Best practices for study design, causal inference, and evidence frameworks in RWE.*

4. **AI & NLP**  
   👉 [RWE-AI-NLP-Integration-Playbook](https://github.com/camontefusco/RWE-AI-NLP-Integration-Playbook)  
   *Integrating unstructured data and modern NLP/LLM approaches into RWE analytics.*

5. **Integration & Interoperability (AWS-first)** *(this repo)*  
   👉 [RWE-AWS-Integration-Interoperability-Pipeline](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline)  
   *Hands-on, cloud-native AWS pipeline aligned to Anderson et al. (2024) tutorial — ingestion → transformation (OMOP/FHIR) → dashboards → analytics/ML.*

---

> 💡 Together, these repos create a **comprehensive, senior-level RWE playbook**:  
> from **governance and compliance**, through **methodological rigor**, to **AI/NLP innovation**, and now a **demoable cloud-native pipeline**.

---

## 📁 Repository Structure
```plaintext
RWE-Integration-and-Interoperability-Playbook/
├── aws/
│ ├── lambda_handler.py # core Lambda for ingestion + transform
│ ├── serverless.yaml # IaC (SAM / Serverless Framework)
│ ├── athena_ddl.sql # Athena external tables for curated data
│ └── step_functions.asl.json # (optional) orchestration stub
│
├── pipeline/
│ ├── transform.py # OMOP & FHIR normalization logic
│ └── schemas.py # schema validators/mappers
│
├── reports/
│ └── interoperability_summary.md # sample queries + mini-dashboard
│
├── tests/
│ └── test_transform.py
│
├── requirements.txt
└── README.md
```

---

## 1️⃣ Data Ingestion

- **Source**: Raw JSON/CSV (synthetic or OpenFDA).  
- **Landing**: S3 bucket (`/raw/`).  
- **Lambda**: Polls source or triggered on upload, validates schema, writes to S3 (`/raw/`) or RDS (Postgres).  
- **Security**: S3 encryption, IAM roles, CloudWatch logging, optional de-identification.

```bash
aws s3 cp sample_raw.json s3://<your-bucket>/raw/
```
2️⃣ Data Transformation

Orchestration: AWS Step Functions (stub provided).

Logic: pipeline/transform.py normalizes to OMOP-ish tables and FHIR-ish NDJSON.

Outputs:

S3 /curated/ → OMOP-ish CSV (person, condition_occurrence, observation)

S3 /fhir/ → FHIR-ish NDJSON (Patient, Condition, Observation)

Example Athena table (see aws/athena_ddl.sql):
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS rwe_playbook.condition_occurrence(
  person_id string,
  condition_concept_code string,
  condition_start_date string,
  source_vocabulary string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySerDe'
WITH SERDEPROPERTIES ('serialization.format' = ',')
LOCATION 's3://<bucket>/curated/condition_occurrence/'
TBLPROPERTIES ('skip.header.line.count'='1');
```
Optional advanced transform:

NLP stub (topic modeling / entity extraction on unstructured notes field).

Placeholder for LLM/NER integration.

3️⃣ Dashboards & Reports

Default: Amazon QuickSight dashboards (connect to Athena or RDS).

Stub: reports/interoperability_summary.md includes sample SQL queries + markdown tables as a lightweight stand-in.

Alternatives: Grafana, OpenSearch, Superset.

Example QuickSight panel:

Age distribution of patients

Conditions by vocabulary (ICD-10)

Observations (LOINC labs) over time
4️⃣ Analytics & ML

Baseline: Query curated data in Athena or DuckDB (local test).

Advanced:

SageMaker clustering stub (Kmodes on categorical features).

Optional notebook showing how to load curated data from S3 into SageMaker for analysis.

Example query (Athena):
```sql
SELECT condition_concept_code, COUNT(*) as n
FROM rwe_playbook.condition_occurrence
GROUP BY condition_concept_code
ORDER BY n DESC
LIMIT 10;
```
✅ Interoperability Checks

OMOP-ish presence: person.csv, condition_occurrence.csv, observation.csv.

FHIR-ish presence: Patient.ndjson, Condition.ndjson, Observation.ndjson.

Vocabulary tags preserved: ICD-10, LOINC.

Queryable: Athena external tables + dashboards.

🔐 Security

Encryption: S3 default encryption (SSE-S3 / SSE-KMS).

Access Control: IAM least privilege for Lambda/Athena.

Logging: CloudWatch for pipeline steps.

PHI handling: Stub de-identification functions; real deployment must align with HIPAA/GxP.

🛠 Requirements
```graphql
pandas
boto3
duckdb   # for local SQL sanity checks
```
📌 Roadmap

✅ S3 + Lambda → OMOP & FHIR outputs

✅ Athena queries (DDL provided)

🔲 Step Functions orchestration (stub included)

🔲 QuickSight dashboards (link Athena to QuickSight)

🔲 SageMaker clustering demo (Kmodes on curated data)

🔲 Glue Crawler + Parquet for performance

## 📊 Mock Dashboard (Athena-first)

Until QuickSight or Grafana is enabled, results are visualized from Athena query outputs.

| Metric | Example Output | Visualization Type |
|--------|----------------|--------------------|
| Gender distribution | M: 45, F: 55 | Pie chart |
| Top conditions | Hypertension (36), Diabetes (42) | Horizontal bar |
| Notes with keywords | 62% | KPI card |
| Observations per patient | 5.4 avg. per patient | Histogram |


📚 References

Anderson W. et al. (2024), Real-world evidence in the cloud: Tutorial on developing an end-to-end data and analytics pipeline using AWS, Clin Transl Sci, 17:e70078.

OMOP CDM — https://ohdsi.github.io/CommonDataModel/

# RWE AWS Integration & Interoperability Pipeline

**Goal:**  
End-to-end pipeline on AWS to ingest real-world data (RWD), normalize into a lightweight **OMOP-ish** schema, expose a **FHIR-ish** JSON view, and enable analytics through SQL, dashboards, and ML.

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=awslambda&logoColor=white)](https://docs.aws.amazon.com/lambda/)
[![Step Functions](https://img.shields.io/badge/AWS-Step%20Functions-orange?logo=awsstepfunctions&logoColor=white)](https://docs.aws.amazon.com/step-functions/)
[![S3](https://img.shields.io/badge/AWS-S3-orange?logo=amazons3&logoColor=white)](https://docs.aws.amazon.com/s3/)
[![Athena](https://img.shields.io/badge/AWS-Athena-orange?logo=amazon-aws&logoColor=white)](https://docs.aws.amazon.com/athena/)
[![FHIR](https://img.shields.io/badge/FHIR-v5.0+-red?logo=fhir&logoColor=white)](https://www.hl7.org/fhir/)
[![OMOP](https://img.shields.io/badge/OMOP-CDM-blue)](https://ohdsi.github.io/CommonDataModel/)
[![SQL](https://img.shields.io/badge/SQL-ANSI-blue)](https://en.wikipedia.org/wiki/SQL)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)

![Banner](banner.png)

---

## 🧩 Overview

This repository demonstrates an **end-to-end AWS pipeline** for ingesting Real-World Evidence (RWE) data, transforming it into:
- an **OMOP-ish** tabular model (`/curated`)
- a **FHIR-ish** JSON structure (`/fhir`)

and enabling analytics via **Athena**, **SQL**, **QuickSight**, and **Python-based ML**.

---

## 🗂️ Branches Overview

| Branch | Description |
|--------|--------------|
| **main** | Core codebase, docs, and architecture files |
| **curated** | Example output layout for `/curated` CSV and `/fhir` NDJSON |
| **reports** | Example CSV reports and summaries |
| **athena-results** | Athena query result structure (CSV) |
| **analytics** | notebooks |

```bash
git fetch --all
git checkout <branch>
```
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

## 📁 Repository Structure (main branch)
```plaintext
aws/            # Lambda, IaC, and Athena DDL (aws/athena_ddl.sql)
pipeline/       # Transformation logic and schema mapping
diagrams/       # Architecture diagrams
docs/           # Supporting documentation
samples/        # Sample raw data inputs
tests/          # Unit tests (pytest)
ARCHITECTURE.md
DATA_DICTIONARY.md
```

---

## 1️⃣ Data Ingestion

- **Source**: Raw JSON/CSV (synthetic or OpenFDA).  This project uses sample real-world evidence (RWE) data from [openfda_ae.csv](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/blob/raw/openfda_ae.csv) stored in the `raw` branch.
- **Landing**: S3 bucket (`/raw/`).  
- **Lambda**: Polls source or triggered on upload, validates schema, writes to S3 (`/raw/`) or RDS (Postgres).  
- **Security**: S3 encryption, IAM roles, CloudWatch logging, optional de-identification.

```bash
aws s3 cp sample_raw.json s3://<your-bucket>/raw/
```
## 2️⃣ Data Transformation

- Orchestration: AWS Step Functions (stub provided).
- Logic: pipeline/transform.py normalizes to OMOP-ish tables and FHIR-ish NDJSON.
- Outputs:
   - S3 /curated/ → OMOP-ish CSV (person, condition_occurrence, observation)
   - S3 /fhir/ → FHIR-ish NDJSON (Patient, Condition, Observation)

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

## 3️⃣ Dashboards & Reports
- Default: Amazon QuickSight dashboards (connect to Athena or RDS).
- Stub: reports/interoperability_summary.md includes sample SQL queries + markdown tables as a lightweight stand-in.

## 4️⃣ Analytics & ML
- Baseline: Query curated data in Athena or DuckDB (local test).
- Advanced: SageMaker clustering stub (Kmodes on categorical features).

## ✅ Interoperability Checks
- OMOP-ish presence: person.csv, condition_occurrence.csv, observation.csv.
- FHIR-ish presence: Patient.ndjson, Condition.ndjson, Observation.ndjson.
- Vocabulary tags preserved: ICD-10, LOINC.
- Queryable: Athena external tables + dashboards.

## 🔐 Security
- Encryption: S3 default encryption (SSE-S3 / SSE-KMS).
- Access Control: IAM least privilege for Lambda/Athena.
- Logging: CloudWatch for pipeline steps.
- PHI handling: Stub de-identification functions; real deployment must align with HIPAA/GxP.

## 🛠 Requirements
```graphql
pandas
boto3
duckdb   # for local SQL sanity checks
```
---

## ⚙️ Workflow

- **Ingest** → Upload raw JSON/CSV to **S3** (`/raw`) via **AWS Lambda**  
- **Transform** → **Step Functions** + Lambda produce `/curated` (CSV) and `/fhir` (NDJSON) outputs  
- **Query** → Define **Athena** external tables from [`aws/athena_ddl.sql`](aws/athena_ddl.sql)  
- **Analyze & Report** → Build **QuickSight dashboards**, explore CSVs in [`reports/`](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/tree/reports), or run notebooks in [`analytics/`](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/tree/analytics)

- **Data Source** – [openfda_ae.csv](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/blob/raw/openfda_ae.csv)  
  Synthetic RWE sample derived from **OpenFDA adverse event** datasets.  

- **Athena DDL** – [`aws/athena_ddl.sql`](aws/athena_ddl.sql)  
  Defines external tables for querying curated data in S3.  

- **Transformation Logic** – [`pipeline/transform.py`](pipeline/transform.py)  
  Normalizes input to OMOP and FHIR structures.  

- **Reports & Summaries** – [`reports/`](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/tree/reports)  
  Contains summary CSVs and interoperability overview markdown.  

- **Analytics & ML** – [`analytics/`](https://github.com/camontefusco/RWE-AWS-Integration-Interoperability-Pipeline/tree/analytics)  
  Holds SQL, notebooks, and exploration scripts.

---

## 🧭 Notes

- “**OMOP-ish**” and “**FHIR-ish**” denote simplified demo subsets — for concept demonstration, not production.  
- Branches represent different pipeline stages: **data**, **reports**, **analytics**.  
- Fully compatible with **AWS Serverless Framework** and **AWS SAM** deployments.  
- Designed for interoperability between **OpenFDA RWE datasets** and AWS-native analytics tools.

---

📚 References
- Anderson W. et al. (2024), Real-world evidence in the cloud: Tutorial on developing an end-to-end data and analytics pipeline using AWS, Clin Transl Sci, 17:e70078.
OMOP CDM — https://ohdsi.github.io/CommonDataModel/

---
## 📫 Contact
Carlos Victor Montefusco Pereira, PhD  
[LinkedIn](https://www.linkedin.com/in/camontefusco) | [GitHub](https://github.com/camontefusco)

import json
import os
import subprocess
import sys
import csv
from pathlib import Path

ALLOWED_GENDERS = {"M","F","O","UNK"}

def run_local_transform(tmp_out: Path):
    tmp_out.mkdir(parents=True, exist_ok=True)
    sample = Path("samples") / "sample_rwd.csv"
    assert sample.exists(), "samples/sample_rwd.csv is missing"
    cp = subprocess.run(
        [sys.executable, "-m", "pipeline.transform", "--local", str(sample), str(tmp_out)],
        capture_output=True, text=True
    )
    if cp.returncode != 0:
        raise AssertionError(f"transform failed:\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}")
    return tmp_out

def first_existing(*candidates: Path) -> Path:
    for p in candidates:
        if p.exists():
            return p
    raise AssertionError(f"None of the expected paths exist:\n" + "\n".join(str(p) for p in candidates))

def read_csv_head(path: Path, n=5):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            rows.append(row)
            if i+1 >= n:
                break
    return rows

def test_outputs_exist_and_columns(tmp_path):
    outdir = run_local_transform(tmp_path / "local_out")

    # OMOP-ish CSVs (support both nested and flat layouts)
    person_csv = first_existing(
        outdir / "curated" / "person" / "person.csv",
        outdir / "person.csv"
    )
    cond_csv = first_existing(
        outdir / "curated" / "condition_occurrence" / "condition_occurrence.csv",
        outdir / "condition_occurrence.csv"
    )
    obs_csv = first_existing(
        outdir / "curated" / "observation" / "observation.csv",
        outdir / "observation.csv"
    )

    # Basic columns present (check minimal required set)
    person_head = read_csv_head(person_csv, 1)[0]
    for col in ["person_id", "gender_concept_code"]:
        assert col in person_head
    assert ("birth_datetime" in person_head) or ("year_of_birth" in person_head), "Expected birth_datetime or year_of_birth"

    cond_head = read_csv_head(cond_csv, 1)[0]
    for col in ["person_id", "condition_concept_code", "condition_start_date"]:
        assert col in cond_head

    obs_head = read_csv_head(obs_csv, 1)[0]
    for col in ["person_id", "observation_concept_code"]:
        assert col in obs_head

def test_gender_values_normalized(tmp_path):
    outdir = run_local_transform(tmp_path / "local_out2")
    person_csv = first_existing(
        outdir / "curated" / "person" / "person.csv",
        outdir / "person.csv"
    )
    rows = read_csv_head(person_csv, n=1000)
    genders = { (row.get("gender_concept_code") or "").strip() for row in rows }
    assert genders <= ALLOWED_GENDERS, f"Unexpected gender codes: {genders - ALLOWED_GENDERS}"

def test_fhir_shapes(tmp_path):
    outdir = run_local_transform(tmp_path / "local_out3")

    # FHIR NDJSONs (support both nested and flat layouts)
    for res in ["Patient","Condition","Observation"]:
        nd = first_existing(
            outdir / "fhir" / res / f"{res}.ndjson",
            outdir / f"{res}.ndjson"
        )
        with open(nd, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            assert line, f"{res}.ndjson is empty"
            obj = json.loads(line)
            assert obj.get("resourceType") == res
            if res == "Patient":
                assert "id" in obj
            if res == "Condition":
                assert "code" in obj and "subject" in obj
            if res == "Observation":
                assert "code" in obj

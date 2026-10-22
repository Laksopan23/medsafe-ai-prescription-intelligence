# MedSafe-AI thesis implementation and verification — 22 October 2026

This is an evidence ledger for the current software branch, not a claim of clinical safety or completed thesis acceptance. The original proposal and the connected Drive research folder were reviewed. No patient prescription or unreviewed clinical threshold was copied into Git. Re-run the commands below before relying on a newer commit.

## Achievement matrix

| Thesis requirement | Status | Implemented evidence | Remaining gate |
| --- | --- | --- | --- |
| Four-engine same-image OCR comparison | PARTIALLY_IMPLEMENTED | `backend/app/api/routes/ocr_compare.py`, React comparison tests; all four adapters exposed without silent substitution | End-to-end held-out comparison requires independent images, all model weights and measured runs |
| Notebook 44 fine-tuned recognition | PARTIALLY_IMPLEMENTED | `medsafe/trocr.py`, `medsafe/ocr_product.py`; app now uses Notebook 61 LAYOUT_V2 CRAFT thresholds, merging, crop padding and `max_new_tokens=64, num_beams=2`; standalone word inference uses Notebook 44's 48-token setting; full local checkpoint and live synthetic-image inference verified | Compare predictions on the notebook's development images where access is authorized; no independent test metric yet |
| Prescription extraction and correction | IMPLEMENTED_AND_TESTED | `medsafe/extraction.py`, `medsafe/pipeline.py`, `frontend/src/features/PrescriptionWorkspace.jsx`; reviewer confirmation, per-medication blocks, uncertain-candidate abstention | OCR accuracy on independent handwriting unknown |
| DailyMed/openFDA/RxNorm evidence | IMPLEMENTED_AND_TESTED | `medsafe/references.py`, `/api/reference`, `/api/reference/label/{setid}`; source IDs, version/date, bounded network retries and cache; real public label read and mocked tests | Search results are candidate evidence, not confirmed Sri Lankan product matches or approved limits |
| Reviewed-rule lifecycle and dose checks | PARTIALLY_IMPLEMENTED | `medsafe/rule_workflow.py`, `medsafe/rule_registry.py`, `backend/app/services/review_service.py`; draft-only local workflow, offline import validation, exact context, expiry and age applicability, mass/mL concentration and mg/kg screens | Zero real-drug rules approved; reviewer identity and source interpretation need independent governance |
| Pediatric/adult/elderly age screen | PARTIALLY_IMPLEMENTED | Reviewed age-range flags require a matching rule and verified age; out-of-range age prevents use of that rule's dose threshold | No approved age-specific rules or patient-level clinical validation |
| Synthetic 300–500 prescription dataset | IMPLEMENTED_AND_TESTED | `backend/app/research/synthetic.py`; 400 deterministic fictional images generated locally with seed `20261022`, 280/60/60 split, mixed image conditions, 50 each multi/missing/ambiguous/conflicting cases | Fictional images and labels are **not** independently verified medical evidence |
| Independent OCR and safety evaluation | READY_FOR_INDEPENDENT_EVALUATION | `backend/app/research/benchmark.py`, `medsafe/evaluation.py`; CER/WER, field and ordered medication-level scores, coverage, specificity, Wilson intervals, stage latency, condition breakdown | Drive candidate label CSV has blank ground truth, `human_verified=false`; no eligible held-out metrics or clinical labels |
| Batch processing and performance | PARTIALLY_IMPLEMENTED | `/api/prescriptions/batch` bounds requests to 1–32 files and isolates per-file HTTP errors; 12-image synthetic Tesseract smoke result below | Cloud-GPU latency, four-engine throughput, memory and concurrency not measured |
| Local application quality | IMPLEMENTED_AND_TESTED | FastAPI/SQLite workflow, React review and source display, pytest/Vitest/production build, local audit; frontend lockfile makes installs reproducible | No production authentication, patient-data governance, clinical approval or public deployment clearance |

## Target versus actual verified result

| Measure | Thesis target | Actual independent result |
| --- | --- | --- |
| Best-engine CER | ≤10% | Not measured on eligible held-out data |
| WER by engine and image condition | Report | Not measured on eligible held-out data |
| Medicine-name accuracy | ≥90% | Not measured on eligible held-out data |
| Administered-dose accuracy | ≥90% | Not measured on eligible held-out data |
| Overdose precision / recall | ≥85% each | Not measured; zero approved real-drug rules and zero adjudicated cases |
| Age accuracy and flag precision / recall | ≥85% accuracy; report precision/recall | Not measured; no approved age rules or adjudicated cases |
| Processing time on standard cloud GPU | ≤10 s per prescription | Not measured on specified GPU |
| Synthetic-image count | 300–500 | 400 fictional images generated locally; **not a clinical or held-out achievement** |

Local smoke-only measurement: Tesseract processed 12 synthetic pages with `n=12`, OCR completion `12/12`, mean 0.8274 s, median 0.7989 s, p95 1.0774 s, maximum 1.0774 s. Both `ocr_eligible` and `thesis_eligible` are false. Dose and age alert evaluated counts are zero because ambiguous/unsupported results abstain. See ignored local artifact `runtime_data/synthetic_smoke_12/tesseract_benchmark.json`; these are not reproducible hardware-neutral claims.

Notebook 44 synthetic-image smoke check: `setup_and_verify_models.py` loaded CRAFT and the local fine-tuned checkpoint, produced 5/5 nonempty region predictions, and completed in 134.59 s on a CPU-only Windows machine. The copied `model.safetensors` is 1,335,747,032 bytes, SHA-256 `a646621570f74db93c0a9354795860ccdd44bae3267624a140a4087ac6113a80`. The ignored report is `runtime_data/notebook44_synthetic_smoke.json`; it records only input/output hashes and counts, not the transcription. This is a live integration check, **not** a held-out accuracy comparison or a cloud-GPU latency result.

## Executed software verification

- Python: `python -m pytest -q` — **142 passed**, one local `requests` dependency-compatibility warning, zero failures.
- Frontend: `npm ci --no-audit --no-fund`, `npm run test:unit` — **10 passed** across 4 files; `npm run build` passed.
- Real public reference call: the openFDA label endpoint returned `UNVERIFIED_LABEL_EVIDENCE` with a source label ID and eight section categories for a public DailyMed example Set ID. This did not activate a drug rule.
- Synthetic generator: 400 images created; `read_manifest(..., require_human=False)` accepted all 400 unique images and recorded normal, blurred, low-light and rotated tags. It is rejected by the human-verification gate in tests.
- API and safety checks: upload/review/report/audit, candidate lookup, rule import, expiry, concentration, age applicability, PRN abstention and multi-medicine boundaries are covered by automated tests. These tests are primarily synthetic and mocked, not clinical outcome validation.
- Running local server on isolated port 8001/database: synthetic-image upload, transcription review, report and audit returned HTTP 200; report had one medication, zero reviewed rules and `clinical_clearance=false`. Two-file batch returned one `REVIEW_REQUIRED` and one `FAILED` without aborting the batch.
- Browser-control inspection was attempted but both available UI helpers failed to initialize (`failed to write kernel assets: system cannot find the path specified`). No manual browser click-through is claimed. React component tests, production build and HTTP integration checks passed instead.

## Clinical readiness and provenance

- Active approved medication rules in the shipped registry: **0**. Draft rules shipped: **0**. Supported approved real medicine/product contexts: **0**.
- Positive and negative independently adjudicated clinical cases evaluated: **0 / 0**. Clinical alert coverage, abstention and precision/recall on real data: **not measurable**.
- `backend/app/research/clinical_readiness.py` returns `clinical_use_authorized=false`; blockers include no approved real-drug rules, no independently human-labeled evaluation, no clinical targets established, and no sign-off.
- The connected Drive `04_results/independent_evaluation_labels.csv` is an unfilled candidate sheet; its 20 listed entries have blank ground truth and `human_verified=false`. It cannot be relabeled as a completed independent test.
- DailyMed/openFDA are official U.S. label evidence sources. Their presence does not establish exact local product, formulation, indication, dose ceiling, age suitability or Sri Lankan applicability. A qualified reviewer must verify the applicable label and local guidance before a rule is activated.
- Rule schema v2 checks evidence identifiers, revisions, review dates, independent reviewer declarations, expiry and relevant concentration. Software cannot authenticate identities, signatures, qualifications or medical correctness. The external governance process remains mandatory.

## Reproduce available software checks

```powershell
python -m pytest -q
cd frontend
npm ci --no-audit --no-fund
npm run test:unit
npm run build
```

Synthetic generator (fictional data only):

```powershell
python -m backend.app.research.synthetic --output runtime_data/synthetic_thesis_400 --count 400 --seed 20261022
python -m backend.app.research.benchmark runtime_data/synthetic_smoke_12/manifest.jsonl --synthetic-development-only --engines tesseract --output runtime_data/synthetic_smoke_12/tesseract_benchmark.json
```

The 12-image smoke manifest is created via `backend.app.research.synthetic.generate(..., count=12, allow_small=True)` for local debugging; it is deliberately too small and too synthetic for thesis acceptance. For independent evaluation, follow [the held-out protocol](INDEPENDENT_EVALUATION_PROTOCOL.md) and do **not** use `--synthetic-development-only`.

## External evidence still required

1. Explicit authorization and de-identification for any genuine prescription images; independent transcription and medication-level labels, with adjudication and leakage audit.
2. Four-engine same-image benchmark, including Notebook 44 checkpoint inference, on the isolated held-out set. Record model hashes, OCR settings, errors, latency, image conditions and sample denominators.
3. Qualified first and independent second reviews of each real-drug rule, source sections/versions, local applicability, age/weight restrictions and approval record. Keep the default registry empty until then.
4. Independently labeled positive, negative and indeterminate overdose/age cases, with uncertainty/abstention coverage, confidence intervals, and class support.
5. Cloud-GPU runtime performance and batch/concurrency/resource measurements; security and clinical governance sign-off before any clinical or public deployment.

Official API references: [DailyMed v2 web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm), [openFDA labeling fields](https://open.fda.gov/apis/drug/label/searchable-fields/), [openFDA authentication](https://open.fda.gov/apis/authentication/), [RxNorm name search](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiByString.html).

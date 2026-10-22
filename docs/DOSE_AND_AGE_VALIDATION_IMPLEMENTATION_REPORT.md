# Dose and age validation implementation report

22 October 2026. Research prototype only. No clinical clearance, prescribing, or dispensing authorization.

## Requirement traceability

| Requirement | Implementation | Test evidence | Status | Remaining dependency |
| --- | --- | --- | --- | --- |
| Preserve image, review text before screening | `medsafe/api_product.py`, `medsafe/storage.py` | Product workflow and review tests | IMPLEMENTED_AND_TESTED | None for local prototype |
| Keep medicines and administered doses separate | `medsafe/extraction.py`, `medsafe/pipeline.py` | Extraction and multi-medication tests | IMPLEMENTED_AND_TESTED | Independent handwritten-image labels for accuracy |
| Retrieve and inspect official candidate references | `medsafe/references.py`, label endpoint and React review | Mocked label tests and earlier live public-label check in thesis evidence ledger | IMPLEMENTED_AND_TESTED | Qualified product and local applicability verification |
| Draft evidence without automatic approval | `medsafe/rule_workflow.py` | Draft lifecycle tests | IMPLEMENTED_AND_TESTED | External qualified review |
| Import externally governed reviewed rules | `medsafe/rule_registry.py`, schema v2 and stricter v3 | Registry tests; offline inspection command | PARTIALLY_IMPLEMENTED | Structural validation cannot authenticate qualifications, signatures, or clinical correctness |
| Exact formulation, strength, product and clinical-context matching | Schema v3 matching in `medsafe/rule_registry.py`; `medsafe/extraction.py` | `tests/test_dose_age_detail.py` | IMPLEMENTED_AND_TESTED | Human confirmation of product, formulation, indication and population |
| Single, daily and weight-based screening | `assess_reviewed_rule`; decimal arithmetic and separate comparison outcomes | Existing rule tests and `tests/test_dose_age_detail.py` | IMPLEMENTED_AND_TESTED | Real-drug thresholds require external approval |
| Age applicability and age-related abstention | `backend/app/services/review_service.py`; age outside range prevents use of dose threshold | Existing review tests and new age outcome field | PARTIALLY_IMPLEMENTED | No reviewed real-drug age or geriatric rules; no universal age table is used |
| Medication-specific warnings and provenance in report | Review service and React prescription workspace | Backend and frontend suites | IMPLEMENTED_AND_TESTED | Qualified clinician interpretation |
| Overdose precision/recall >=85% and age accuracy >=85% | Independent evaluation tooling and protocol | No eligible clinical evaluation result | BLOCKED_BY_INDEPENDENT_EVALUATION | Independently adjudicated positive, negative and indeterminate cases, plus approved rules |
| Clinical deployment approval | No approval pathway in this application | `backend/app/research/clinical_readiness.py` | BLOCKED_BY_EXTERNAL_CLINICAL_REVIEW | Governance, ethics, security, local applicability and professional sign-off |

## Data flow and safety boundary

```text
Original local image -> OCR candidate text -> human correction/confirmation
 -> medication-specific fields -> exact product/context rule match
 -> reviewed age applicability -> dose/weight/concentration comparisons
 -> evidence-linked warning or explicit abstention -> stored local report
```

The default `reviewed_rules_EMPTY.json` contains no real-drug rule. Public DailyMed/openFDA label sections and RxNorm names are candidate evidence, not dose ceilings or proof of equivalent formulation. A reviewer must confirm exact product, route, indication, population, source version and any numerical limit. WHO or local guidelines may be attached as manually cited evidence; the app does not scrape them into thresholds. U.S. labeling does not establish Sri Lankan applicability by itself.

Schema v3 requires formulation, strength, source type, approval date and exclusions in addition to v2 independent-review metadata. Existing v1/v2 rules remain readable for compatibility; v3 exact formulation/strength matching is stricter. A file can be structurally valid without genuine professional approval. Clinical governance must verify its provenance before setting `MEDSAFE_REVIEWED_RULES`. The app has no self-approval button. Draft, expired, rejected and superseded rules cannot match.

For a reviewed rule, the calculator converts mg, mcg and g to the rule's mass unit using decimal arithmetic. mL is converted only with a reviewed concentration tied to the exact product. It compares single amount and frequency-derived daily amount separately; weight-based limits cap these values when a reviewed mg/kg rule exists. A weight-based warning is emitted only when the weight-based threshold itself is exceeded, not merely when a lower absolute cap is crossed. PRN, uncertain frequency, missing or invalid units, missing required weight, conflicting or duplicate medication regimens and age outside a reviewed rule's applicability abstain. Equal to a threshold is not flagged, but **never means safe**. `comparison_outcomes` distinguishes single, daily and weight-based exceedance while the legacy `status` remains compatible with existing reports. The age result distinguishes outside reviewed applicability, within-range-but-not-proof-of-safety, and a threshold exceeded within the applicable age range. All results retain `clinical_clearance: false`.

## Verification and independent evaluation

Executed in this branch: `python -m pytest -q` **150 passed**, one local requests dependency warning; `frontend/npm run test:unit` **10 passed**; `frontend/npm run build` passed. Tests use fictional numeric rules. Existing local upload/review/audit integration is exercised by the backend suite. See [independent evaluation protocol](INDEPENDENT_EVALUATION_PROTOCOL.md) for human-labeled held-out image and alert requirements, field/alert metrics, class support, abstentions and latency. The [thesis evidence ledger](THESIS_IMPLEMENTATION_EVIDENCE_2026-10-22.md) records prior OCR/model and synthetic smoke checks; it does not establish clinical accuracy. No eligible independent overdose or age metrics exist; both targets are **NOT MEASURABLE**.

To reproduce locally, follow `README.md` and `docs/NOTEBOOK44_WINDOWS_SETUP.md`, then run the commands above. A qualified primary and independent second reviewer must prepare signed, dated product-specific evidence externally before rule activation. Approved rules and de-identified adjudicated test data must stay in governed local storage, not GitHub.

Official source documentation: [DailyMed web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm), [openFDA drug labeling](https://open.fda.gov/apis/drug/label/), [RxNorm APIs](https://www.lhncbc.nlm.nih.gov/RxNav/APIs/index.html), [WHO publications](https://www.who.int/publications).

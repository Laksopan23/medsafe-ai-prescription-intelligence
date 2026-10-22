# Clinical evidence and independent validation register

**Status: NOT CLINICALLY APPROVED.** This register is an auditable handoff for qualified clinical reviewers. It does not certify MedSafe-AI or approve any drug dosing threshold.

## Review record required for each medicine and indication

| Field | Reviewer must document |
| --- | --- |
| Exact ingredient and product | Product identifier, dosage form, strength and concentration |
| Clinical context | Route, indication, population, age, weight and applicable renal/hepatic considerations |
| Source evidence | Official source HTTPS URL, precise label section, publication/revision date, retrieval date |
| Dose interpretation | Administered single-dose and daily-dose ceiling, units, frequency assumptions, mg/kg basis if applicable |
| Scope and exclusions | When the rule must abstain, including PRN or missing concentration |
| Professional approval | Reviewer identity, credentials, institution, signed approval date and version |
| Independent verification | Second reviewer, adjudication of discrepancies, version and approval date |
| Revalidation | Expiry date and re-review after labeling changes |

## Approval and release gates

1. Pharmacist or prescribing clinician independently verifies each source against the exact formulation and patient population.
2. A separate qualified reviewer checks the transcribed numerical values, units, source context, contraindications and exceptions.
3. Only then may a signed and versioned record be added to the external JSON registry and deployed with MEDSAFE_REVIEWED_RULES.
4. Test threshold boundaries, unit conversions, incorrect routes, missing age/weight, uncertain medicine names, incomplete schedules and expired rules.
5. Use a separately adjudicated held-out clinical case set with both positive and negative cases to estimate sensitivity, specificity, precision, recall, age-classification accuracy and abstention rates.
6. Record cohort provenance, class counts, confidence intervals, errors, conflicts and model version. Do not use synthetic fixtures as evidence of clinical performance.
7. Obtain the institution's required ethics, data protection, clinical governance and deployment approvals before handling identifiable patient records or using outputs in patient care.

## Current project evidence

- The reviewed real-drug registry shipped in this repository is empty (`reviewed_rules_EMPTY.json`).
- DailyMed/openFDA evidence excerpts are unverified source material, not clinician-approved dose ceilings.
- No independent clinical adjudication or sign-off is recorded in the repository.
- Missing evidence must return NOT_EVALUATED / UNABLE_TO_VALIDATE, not a reassuring negative.
- All results are research screening flags, not diagnoses or dispensing authorization.

**Approval decision:** BLOCKED until signed professional evidence and independent evaluation are supplied.

## Draft-to-import workflow

The application can fetch full openFDA label sections for a DailyMed `setid`, showing label ID, effective date and retrieval time. This is **candidate source text**, not a verified local product match. The optional `OPENFDA_API_KEY` remains server-side. Public reference lookups use bounded GET retries, timeouts and a ten-minute in-memory cache; an approved-rule file is never derived from or refreshed by this cache.

```bash
python -m medsafe.rule_workflow draft --setid YOUR-SETID --output runtime_data/rule_drafts/example.json
python -m medsafe.rule_workflow inspect /path/to/externally_approved_registry.json
```

The first command creates a `DRAFT` containing no numeric threshold. Local lifecycle changes may move a draft to `AWAITING_REVIEW` or `REJECTED`, and an approved record to `EXPIRED` or `SUPERSEDED`; this application has **no command to approve a rule**. The second command checks structure and reports a SHA-256 digest; it does not deploy or independently authenticate the listed reviewers. Activation still requires a separately governed `MEDSAFE_REVIEWED_RULES` file. The repository default is the empty registry.

Schema version 2 requires an exact ingredient/product/route/indication/population context; source label ID, revision and retrieval time; primary and distinct second reviewer declarations, credentials, dates and approval record ID; and expiry. A concentration-based mL comparison also requires a positive `concentration_mg_per_ml`, the matching product identifier and a sourced concentration section. Expired or superseded rules are excluded at assessment time. Even an approved-looking JSON file cannot prove the reviewers' identities or clinical correctness; governance must verify these offline.

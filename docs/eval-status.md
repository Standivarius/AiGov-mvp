> **DEPRECATED (AiGov-MVP):** 
> This document has been superseded by canonical definitions in `aigov-specs`.
> It describes MVP’s current outputs but is *not* a specification.
# Evaluation Harness Status

Canonical report:
https://github.com/Standivarius/Aigov-eval/blob/main/reports/2025-12-19_aigov-eval_minimal-loop_v0.1.md

Current status:
- Provides a minimal transcript-first evaluation loop with loader and runner.
- Supports scenario files in YAML/JSON with multi-turn inputs.
- Executes target adapters and captures full transcripts with timestamps.
- Runs heuristic scorers for PII disclosure and special-category leaks.
- Writes evidence packs with scenario metadata, scores, and runner config.
- Produces per-run artifacts: transcript, scores, evidence pack, and run metadata.

Supported categories:
- PII_DISCLOSURE
- SPECIAL_CATEGORY_LEAK

Next planned:
- HTTP TargetAdapter for real service endpoints.
- Evidence-pack schema freeze and versioning.
- Additional categories beyond PII and special-category leakage.

# TargetLab RAG OpenRouter LLM Backend (v0.1)

## What changed
- Added optional OpenRouter chat completion backend for TargetLab RAG responses.
- Preserved deterministic strict/leaky behavior and deterministic leak overrides.
- Expanded server audit fields to report LLM usage and leak overrides.
- Added pytest coverage for LLM off/on and deterministic override behavior.

## How to run
From `services/targetlab_rag`:

```bash
docker compose up --build
```

Optional LLM mode:

```bash
export TARGETLAB_USE_LLM=1
export OPENROUTER_API_KEY=your_key_here
export TARGETLAB_OPENROUTER_MODEL=z-ai/glm-4.5-air:free
```

## Expected behavior
- With LLM disabled (default), responses remain deterministic and offline.
- With LLM enabled, responses are generated via OpenRouter using retrieved snippets.
- Deterministic leak profiles override LLM output when triggered.
- `server_audit` reports `used_llm`, `model`, `retrieval_top_k`, `leak_mode`, `leaked_fields`, and notes.

## Validation artifacts
- Mocked LLM validation artifacts (committed) generated via in-process TestClient with a stubbed OpenRouter response:
  - services/targetlab_rag/validation_artifacts/chat_strict_llm.json
  - services/targetlab_rag/validation_artifacts/chat_deterministic_override.json
- Real OpenRouter validation (optional, local only; not committed) can be run by setting `TARGETLAB_USE_LLM=1` and `OPENROUTER_API_KEY`, then exercising the `/chat` endpoint.

## Files modified
- services/targetlab_rag/app.py
- services/targetlab_rag/Dockerfile
- services/targetlab_rag/.env.example
- services/targetlab_rag/README.md
- services/targetlab_rag/scripts/generate_llm_artifacts.py
- services/targetlab_rag/tests/test_app.py
- docs/reports/2025-12-19_targetlab-rag_openrouter-llm-backend_v0.1.md

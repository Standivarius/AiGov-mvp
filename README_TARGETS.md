# Target Stack

This directory contains the Codespaces-first target stack for AiGov-MVP evaluation.

## Prerequisites

- GitHub Codespaces (recommended) or local Docker with Docker Compose
- In Codespaces, docker-in-docker is enabled automatically via devcontainer

## Quick Start

### 1. Verify Docker is available

```bash
docker ps
```

### 2. Start the stack

```bash
cd targets/compose
docker compose up -d --build
```

### 3. Verify services are running

```bash
# Check containers
docker ps

# Check health endpoint
curl localhost:8000/health
# Expected: "ok"
```

## Services

| Service  | Port | Description                     |
|----------|------|---------------------------------|
| rag_api  | 8000 | Placeholder FastAPI RAG service |
| qdrant   | 6333 | Vector database (HTTP API)      |
| qdrant   | 6334 | Vector database (gRPC)          |

## Traces and Runs

Evaluation traces and run artifacts are stored in:

```
./runs/
```

This directory is mounted into the `rag_api` container at `/app/runs`.

## Stopping the stack

```bash
cd targets/compose
docker compose down
```

## Troubleshooting

If `docker ps` fails in Codespaces, rebuild the devcontainer:
1. Open Command Palette (Ctrl+Shift+P)
2. Run "Dev Containers: Rebuild Container"

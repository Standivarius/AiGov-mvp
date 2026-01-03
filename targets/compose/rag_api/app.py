"""Placeholder RAG API for target stack validation."""

from fastapi import FastAPI

app = FastAPI(title="RAG API Placeholder")


@app.get("/health")
def health():
    return "ok"

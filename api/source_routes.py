"""Authenticated SolSpire Source Connection API.

This router owns connection lifecycle only. It does not create a new corpus,
knowledge graph, file store, or execution system. Sync delegates to the existing
CorpusManager and Knowledge OS pipeline.
"""
from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request

from api.auth import require_auth
from api.source_connections import SOURCES, build_corpus_source, connect, disconnect, get_connection, list_connections, record_sync

logger = logging.getLogger("arkadia.source_routes")
router = APIRouter(prefix="/solspire/sources", tags=["solspire-sources"])


@router.get("")
async def get_sources(user: dict = __import__("fastapi").Depends(require_auth)):
    return {"sources": list_connections(user)}


@router.post("/{source}/connect")
async def connect_source(source: str, request: Request, user: dict = __import__("fastapi").Depends(require_auth)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="Unsupported source")
    try:
        config = await request.json()
        if not isinstance(config, dict):
            raise ValueError("Configuration must be an object")
        result = connect(user, source, config)
        return {"source": result, "message": f"{SOURCES[source]['label']} connection established."}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/{source}")
async def disconnect_source(source: str, user: dict = __import__("fastapi").Depends(require_auth)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="Unsupported source")
    removed = disconnect(user, source)
    return {"removed": removed, "source": source}


@router.post("/{source}/sync")
async def sync_source(source: str, user: dict = __import__("fastapi").Depends(require_auth)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="Unsupported source")
    config = get_connection(user, source)
    if not config:
        raise HTTPException(status_code=409, detail="Source is not connected")

    def _sync() -> dict:
        from corpus.manager import CorpusManager
        adapter = build_corpus_source(source, config)
        if not adapter.is_configured():
            raise RuntimeError("Stored connection is incomplete or invalid")
        manager = CorpusManager()
        result = manager.sync_sources([adapter], ingest=True) if hasattr(manager, "sync_sources") else None
        if result is None:
            manager._sources = [adapter]
            manager._sync_all_sources()
            result = {
                "sources": [source],
                "documents": len(manager.get_full_corpus()),
                "live": sum(1 for d in manager.get_full_corpus().values() if not d.get("error") and d.get("chars", 0) > 0),
                "total_chars": manager.total_chars(),
            }
        return result

    try:
        result = await asyncio.to_thread(_sync)
        record_sync(user, source, result.get("live", result.get("documents", 0)))
        return {"source": source, "status": "synced", **result}
    except Exception as exc:
        logger.exception("Source sync failed: %s", source)
        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc

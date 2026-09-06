"""Authenticated SolSpire Source Connection API.

Connection lifecycle only. Sync delegates to CorpusManager and the existing
Knowledge OS ingest pipeline. No new corpus, graph, file store, or execution
system is introduced.
"""
from __future__ import annotations
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from api.auth import require_auth
from api.source_connections import SOURCES, build_corpus_source, connect, disconnect, get_connection, list_connections, record_sync

logger = logging.getLogger("arkadia.source_routes")
router = APIRouter(prefix="/solspire/sources", tags=["solspire-sources"])

@router.get("")
async def get_sources(user: dict = Depends(require_auth)):
    return {"sources": list_connections(user)}

@router.post("/{source}/connect")
async def connect_source(source: str, request: Request, user: dict = Depends(require_auth)):
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
async def disconnect_source(source: str, user: dict = Depends(require_auth)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="Unsupported source")
    return {"removed": disconnect(user, source), "source": source}

@router.post("/{source}/sync")
async def sync_source(source: str, user: dict = Depends(require_auth)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="Unsupported source")
    config = get_connection(user, source)
    if not config:
        raise HTTPException(status_code=409, detail="Source is not connected")

    def _sync() -> dict:
        from corpus.manager import CorpusManager
        from knowledge.pipeline import ingest as knowledge_ingest
        adapter = build_corpus_source(source, config)
        if not adapter.is_configured():
            raise RuntimeError("Stored connection is incomplete or invalid")
        manager = CorpusManager()
        manager._sources = [adapter]
        manager._sync_all_sources()
        corpus = manager.get_full_corpus()
        live = 0
        ingested = 0
        for doc in corpus.values():
            content = str(doc.get("content") or "").strip()
            if not content or doc.get("error"):
                continue
            live += 1
            result = knowledge_ingest(
                title=doc.get("label") or doc.get("id", "Untitled"),
                content=content,
                note_type="document",
                tags=[doc.get("category", "external-source"), f"source:{source}"],
                source_provider=f"corpus:{source}",
                auto_tag=True,
                auto_embed=False,
                auto_link=False,
            )
            if not result.get("duplicate"):
                ingested += 1
        return {"sources": [source], "documents": len(corpus), "live": live, "ingested": ingested, "total_chars": manager.total_chars()}

    try:
        result = await asyncio.to_thread(_sync)
        record_sync(user, source, result["live"])
        return {"source": source, "status": "synced", **result}
    except Exception as exc:
        logger.exception("Source sync failed: %s", source)
        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc

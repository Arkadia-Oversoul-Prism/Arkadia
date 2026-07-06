"""
Arkadia Knowledge OS — Knowledge API Routes
============================================
FastAPI router exposing the Knowledge OS over HTTP.
All routes are read-by-Oracle, write-by-pipeline.
No business logic here — this is a thin HTTP skin over the knowledge layer.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-os"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    title: str
    content: str
    note_type: str = "note"
    project_id: Optional[int] = None
    thread_id: Optional[int] = None
    participants: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    source_provider: Optional[str] = None
    auto_tag: bool = True
    auto_embed: bool = True
    auto_link: bool = True


class ConversationIngestRequest(BaseModel):
    prompt: str
    response: str
    provider: str
    persona: Optional[str] = None
    project_id: Optional[int] = None
    thread_id: Optional[int] = None


class SearchRequest(BaseModel):
    query: str
    modes: Optional[list[str]] = None
    top_k: int = 20


class ContextRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    thread_id: Optional[int] = None
    max_notes: int = 8
    include_timeline: bool = True


class GraphEdgeRequest(BaseModel):
    source_id: int
    target_id: int
    relationship: str
    weight: float = 1.0


class ProjectRequest(BaseModel):
    name: str
    description: str = ""
    tags: Optional[list[str]] = None


class SendRequest(BaseModel):
    messages: list[dict]
    system_prompt: Optional[str] = None
    persona: Optional[str] = None
    provider: Optional[str] = None
    project_id: Optional[int] = None
    thread_id: Optional[int] = None
    ingest_response: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Pipeline
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest_note(req: IngestRequest):
    """Ingest a note through the full knowledge pipeline."""
    try:
        from knowledge.pipeline import ingest
        result = ingest(
            title=req.title,
            content=req.content,
            note_type=req.note_type,
            project_id=req.project_id,
            thread_id=req.thread_id,
            participants=req.participants,
            tags=req.tags,
            source_provider=req.source_provider,
            auto_tag=req.auto_tag,
            auto_embed=req.auto_embed,
            auto_link=req.auto_link,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/conversation")
async def ingest_conversation(req: ConversationIngestRequest):
    """Ingest a full conversation exchange as structured knowledge."""
    try:
        from knowledge.pipeline import ingest_conversation
        result = ingest_conversation(
            prompt=req.prompt,
            response=req.response,
            provider=req.provider,
            persona=req.persona,
            project_id=req.project_id,
            thread_id=req.thread_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Notes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notes")
async def list_notes(
    note_type: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    from knowledge.vault import list_notes
    return list_notes(note_type=note_type, project_id=project_id, limit=limit, offset=offset)


@router.get("/notes/{note_uuid}")
async def get_note(note_uuid: str):
    from knowledge.vault import get_note
    note = get_note(note_uuid)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# ─────────────────────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/search")
async def search(req: SearchRequest):
    """Unified multi-mode search across the Knowledge Vault."""
    try:
        from knowledge.search import unified_search
        return unified_search(req.query, modes=req.modes, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/semantic")
async def semantic_search(q: str, top_k: int = 10):
    from knowledge.search import semantic_search
    return semantic_search(q, top_k=top_k)


@router.get("/search/fulltext")
async def fulltext_search(q: str, note_type: Optional[str] = None, limit: int = 20):
    from knowledge.search import fulltext_search
    return fulltext_search(q, note_type=note_type, limit=limit)


# ─────────────────────────────────────────────────────────────────────────────
# Context Engine
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/context")
async def assemble_context(req: ContextRequest):
    """Assemble a context package for a given query — the Oracle's input to any provider."""
    try:
        from knowledge.context_engine import assemble_context, format_context_for_provider
        package = assemble_context(
            query=req.query,
            project_id=req.project_id,
            thread_id=req.thread_id,
            max_notes=req.max_notes,
            include_timeline=req.include_timeline,
        )
        return {
            "package": package,
            "formatted": format_context_for_provider(package),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Graph
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/graph")
async def full_graph():
    """Export the entire knowledge graph (for Prism visualization)."""
    from knowledge.graph import full_graph_export
    return full_graph_export()


@router.get("/graph/{note_id}/traverse")
async def traverse_graph(note_id: int, depth: int = 2, relationship: Optional[str] = None):
    from knowledge.graph import traverse
    return traverse(note_id, max_depth=depth, relationship_filter=relationship)


@router.get("/graph/{note_id}/path/{target_id}")
async def find_path(note_id: int, target_id: int):
    from knowledge.graph import find_path
    path = find_path(note_id, target_id)
    return {"path": path, "length": len(path)}


@router.post("/graph/edge")
async def add_edge(req: GraphEdgeRequest):
    from knowledge.graph import add_edge
    try:
        add_edge(req.source_id, req.target_id, req.relationship, req.weight)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Timeline
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/timeline")
async def get_timeline(
    event_type: Optional[str] = None,
    project_id: Optional[int] = None,
    note_id: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    from knowledge import timeline as tl
    return tl.query(
        event_type=event_type,
        project_id=project_id,
        note_id=note_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )


@router.get("/timeline/recent")
async def recent_timeline(limit: int = 20):
    from knowledge import timeline as tl
    return tl.recent(limit=limit)


@router.get("/timeline/replay/{project_id}")
async def replay_project(project_id: int):
    """Replay the full event stream for a project."""
    from knowledge import timeline as tl
    return tl.replay_project(project_id)


# ─────────────────────────────────────────────────────────────────────────────
# Projects
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects():
    from knowledge.db import execute
    return execute("SELECT * FROM projects ORDER BY updated_at DESC")


@router.post("/projects")
async def create_project(req: ProjectRequest):
    from knowledge.vault import create_project
    return create_project(req.name, req.description, req.tags)


@router.get("/projects/{name_or_uuid}")
async def get_project(name_or_uuid: str):
    from knowledge.vault import get_project
    project = get_project(name_or_uuid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ─────────────────────────────────────────────────────────────────────────────
# Provider Router
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers():
    from providers.router import list_providers
    return list_providers()


@router.get("/providers/health")
async def providers_health():
    from providers.router import health_all
    return health_all()


@router.post("/providers/send")
async def send_with_context(req: SendRequest):
    """
    Send a message through the Knowledge OS pipeline:
    1. Assemble context from the vault for the last user message
    2. Inject context into system prompt
    3. Route to provider
    4. Ingest the response as knowledge (if ingest_response=True)
    """
    try:
        from knowledge.context_engine import assemble_context, format_context_for_provider
        from providers.router import send

        # Resolve query from last user message
        user_msgs = [m for m in req.messages if m.get("role") == "user"]
        query = user_msgs[-1]["content"] if user_msgs else ""

        # Build knowledge-aware system prompt
        context_pkg = assemble_context(query, project_id=req.project_id)
        context_str = format_context_for_provider(context_pkg)
        system = (req.system_prompt or "") + ("\n\n" + context_str if context_str else "")

        response = send(
            messages=req.messages,
            system_prompt=system,
            persona_name=req.persona,
            provider_name=req.provider,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        # Ingest conversation as knowledge
        if req.ingest_response and query and response.content:
            from knowledge.pipeline import ingest_conversation
            ingest_conversation(
                prompt=query,
                response=response.content,
                provider=response.provider_name,
                persona=req.persona,
                project_id=req.project_id,
                thread_id=req.thread_id,
            )

        return response.to_dict()

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Personas
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/personas")
async def list_personas():
    from knowledge.db import execute
    return execute("SELECT id, name, preferred_provider, created_at FROM personas ORDER BY name")


@router.get("/personas/{name}")
async def get_persona(name: str):
    from knowledge.db import execute_one
    row = execute_one("SELECT * FROM personas WHERE name = ?", (name,))
    if not row:
        raise HTTPException(status_code=404, detail="Persona not found")
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge OS status
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status")
async def knowledge_os_status():
    """Arkadia Knowledge OS health summary."""
    from knowledge.db import execute_one, execute
    try:
        note_count = execute_one("SELECT COUNT(*) as n FROM notes")
        project_count = execute_one("SELECT COUNT(*) as n FROM projects")
        timeline_count = execute_one("SELECT COUNT(*) as n FROM timeline")
        edge_count = execute_one("SELECT COUNT(*) as n FROM graph_edges")
        chunk_count = execute_one("SELECT COUNT(*) as n FROM chunks")
        embed_count = execute_one("SELECT COUNT(*) as n FROM embeddings")
        pending_embed = execute_one("SELECT COUNT(*) as n FROM notes WHERE embedding_status = 'pending'")

        return {
            "status": "operational",
            "vault": {
                "notes": note_count["n"] if note_count else 0,
                "projects": project_count["n"] if project_count else 0,
                "chunks": chunk_count["n"] if chunk_count else 0,
                "embeddings": embed_count["n"] if embed_count else 0,
                "pending_embeddings": pending_embed["n"] if pending_embed else 0,
            },
            "graph": {
                "edges": edge_count["n"] if edge_count else 0,
            },
            "timeline": {
                "events": timeline_count["n"] if timeline_count else 0,
            },
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

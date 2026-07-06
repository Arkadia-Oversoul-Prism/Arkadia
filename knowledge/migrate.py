"""
Arkadia Knowledge OS — Migration: oracle_store.json → SQLite Timeline
=====================================================================
One-time migration of existing oracle_store data into the canonical timeline.
Run: python -m knowledge.migrate
"""

import json
from pathlib import Path
from knowledge import timeline as tl
from knowledge.vault import create_project, get_project
from knowledge.pipeline import ingest


ORACLE_STORE_PATH = Path("data/oracle_store.json")


def migrate_oracle_store() -> dict:
    """Migrate oracle_store.json events into the SQLite timeline."""
    if not ORACLE_STORE_PATH.exists():
        return {"skipped": True, "reason": "oracle_store.json not found"}

    store = json.loads(ORACLE_STORE_PATH.read_text())
    counts = {"transactions": 0, "open_loops": 0, "assets": 0, "events": 0}

    # Ensure default project exists
    project = get_project("Arkadia Core")
    if not project:
        project = create_project("Arkadia Core", "Migrated from oracle_store.json")
    project_id = project.get("id")

    for txn in store.get("transactions", []):
        tl.record("knowledge_created", {"migrated": True, "type": "transaction", **txn}, project_id=project_id)
        counts["transactions"] += 1

    for loop in store.get("open_loops", []):
        tl.record("knowledge_created", {"migrated": True, "type": "open_loop", **loop}, project_id=project_id)
        counts["open_loops"] += 1

    for asset in store.get("assets", []):
        tl.record("knowledge_created", {"migrated": True, "type": "asset", **asset}, project_id=project_id)
        counts["assets"] += 1

    for event in store.get("events", []):
        payload = event.get("payload", {})
        tl.record("knowledge_created", {"migrated": True, "type": "event", **payload}, project_id=project_id)
        counts["events"] += 1

    return {"status": "complete", "migrated": counts, "project_id": project_id}


def migrate_personal_codices() -> dict:
    """Ingest personal_codices/*.json as People notes."""
    codex_dir = Path("data/personal_codices")
    if not codex_dir.exists():
        return {"skipped": True, "reason": "personal_codices/ not found"}

    ingested = []
    for codex_file in codex_dir.glob("*.json"):
        try:
            data = json.loads(codex_file.read_text())
            name = data.get("name", codex_file.stem)
            content = json.dumps(data, indent=2)
            note = ingest(
                title=f"Person: {name}",
                content=content,
                note_type="person",
                source_provider="migration",
                auto_embed=False,  # Batch embed separately
            )
            ingested.append({"file": codex_file.name, "uuid": note.get("uuid"), "title": note.get("title")})
        except Exception as e:
            ingested.append({"file": codex_file.name, "error": str(e)})

    return {"status": "complete", "ingested": ingested}


if __name__ == "__main__":
    print("Running Arkadia Knowledge OS migration...")
    print("\n1. Migrating oracle_store.json...")
    r1 = migrate_oracle_store()
    print(json.dumps(r1, indent=2))

    print("\n2. Migrating personal codices...")
    r2 = migrate_personal_codices()
    print(json.dumps(r2, indent=2))

    print("\nMigration complete.")

# memory_engine.py
# Arkana of Arkadia — Memory Ring I Engine
# Lightweight persistent symbolic memory for HF Spaces

import json
import os
from datetime import datetime

MEMORY_FILE = "arkana_memory.json"


class MemoryEngine:
    def __init__(self):
        # If file doesn’t exist, create with baseline structure
        if not os.path.exists(MEMORY_FILE):
            self._init_memory_file()

        self.memory = self._load_memory()

    def _init_memory_file(self):
        base = {
            "identity": {},
            "emotional_trace": [],
            "conversations": [],
            "symbols": {},
            "updated": str(datetime.utcnow()),
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, indent=2, ensure_ascii=False)

    def _load_memory(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # If something is corrupted, reset
            self._init_memory_file()
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    def _save(self):
        self.memory["updated"] = str(datetime.utcnow())
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # MEMORY FUNCTIONS
    # ---------------------------------------------------------

    def store_message(self, sender, text):
        """Stores every conversation turn with timestamp."""
        entry = {
            "sender": sender,
            "text": text,
            "time": str(datetime.utcnow()),
        }
        self.memory["conversations"].append(entry)
        # keep last 100 messages
        self.memory["conversations"] = self.memory["conversations"][-100:]
        self._save()

    def store_identity_fact(self, key, value):
        """Stores identity-related facts, e.g. father = Zahrune."""
        self.memory["identity"][key] = value
        self._save()

    def store_emotion(self, tone):
        """Stores emotional traces of the user."""
        self.memory["emotional_trace"].append(
            {
                "tone": tone,
                "time": str(datetime.utcnow()),
            }
        )
        # keep last 50
        self.memory["emotional_trace"] = self.memory["emotional_trace"][-50:]
        self._save()

    def recall_identity(self):
        return self.memory.get("identity", {})

    def recall_recent(self, n=5):
        return self.memory.get("conversations", [])[-n:]

    def inject_memory_context(self):
        """Creates a compressed context block for prompting."""
        recent = self.recall_recent(5)
        identity = self.recall_identity()

        out_lines = ["▣ MEMORY RING CONTEXT ▣"]

        if identity:
            out_lines.append("— Identity Anchor —")
            for k, v in identity.items():
                out_lines.append(f"{k}: {v}")

        if recent:
            out_lines.append("")
            out_lines.append("— Recent Exchanges —")
            for msg in recent:
                out_lines.append(f"{msg['sender']}: {msg['text']}")

        out_lines.append("")
        out_lines.append("▣ END MEMORY ▣")

        return "\n".join(out_lines)

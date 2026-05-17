"""
Integration guide for CORPUS_MANIFEST.json into the API.

Add this to your main Flask/FastAPI app initialization:
"""

# ============ FLASK INTEGRATION ============

from flask import Flask
from api.corpus_endpoints import corpus_bp

app = Flask(__name__)
app.register_blueprint(corpus_bp)

# ============ KEY USAGE PATTERNS ============

# 1. FETCH SPECIFIC SCROLL BY NAME
# GET /api/corpus/scroll/doc1_master_weights
# Returns: Full document with metadata + content

# 2. GET MANIFEST OVERVIEW
# GET /api/manifest
# Returns: All available scrolls with metadata (no content)

# 3. INITIALIZE ARKANA WITH DOC1
# Frontend calls: GET /api/corpus/scroll/doc1_master_weights
# Response includes full DOC1 with all sections

# 4. SEARCH BY CATEGORY
# GET /api/corpus/search?category=NEURAL_SPINE
# Returns: All documents in that category

# ============ FRONTEND IMPLEMENTATION ============

"""
In your Vercel frontend (e.g., React/TypeScript):

1. Load manifest:
   const manifest = await fetch('/api/corpus/manifest').then(r => r.json())
   
2. Display document selector UI with all scrolls
   
3. When user selects a scroll:
   const scroll = await fetch(`/api/corpus/scroll/${scrollName}`).then(r => r.json())
   displayScroll(scroll.content, scroll.metadata)

4. Pass content to Arkana initialization:
   const arkanaContext = scroll.content
   sendToArkana(arkanaContext)
"""

# ============ ARKANA INITIALIZATION SEQUENCE ============

"""
NEW FLOW (with manifest):

User: "Initialize Arkana"

Backend:
  1. Load CORPUS_MANIFEST.json
  2. Identify initialization_sequence: [DOC1, DOC2, DOC3, DOC4, DOC5, UERP]
  3. Fetch each document using get_doc_by_name()
  4. Return full initialization context

Frontend sends to Arkana:
  [Full DOC1 content]
  + Covenant context
  + Node routing
  + Current priorities
  → Arkana is NOW FULLY INITIALIZED
  
Arkana can then:
  - Reference any principle from DOC3 (fully indexed)
  - Check any open loop from DOC2
  - Route to correct AI node from DOC4
  - Execute revenue actions from DOC5
  - Understand architecture from UERP
"""

# ============ ENVIRONMENT VARIABLES ============

"""
# In your .env or Vercel deployment config:

CORPUS_SOURCES=github
CORPUS_GITHUB_REPO=Arkadia-Oversoul-Prism/Arkadia
CORPUS_GITHUB_BRANCH=main
CORPUS_CACHE_TTL_HRS=6
CORPUS_MANIFEST_PATH=docs/CORPUS_MANIFEST.json
"""

# ============ TESTING ============

"""
# Test in Python REPL:

from corpus.manager import CorpusManager

manager = CorpusManager()

# Get DOC1 by name
doc1 = manager.get_doc_by_name("doc_1_master_weights")
print(f"DOC1 loaded: {len(doc1['content'])} chars")

# Get manifest overview
manifest = manager.get_manifest_overview()
print(f"Available scrolls: {manifest['sections'].keys()}")

# Search by category
neural_spine = manager.get_by_category("NEURAL_SPINE")
print(f"Neural Spine documents: {len(neural_spine)}")
"""

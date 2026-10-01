# 🜂🜄🜁🜃 Arkadia Oracle Temple - Deployment Guide

## 🎯 Complete System Overview

The Arkadia Oracle Temple is now **fully functional** with all required components:

### ✅ **Core Components Built:**
- **FastAPI Backend** (`arkana_app.py`) - All endpoints working
- **AI Brain System** (`codex_brain.py`) - Gemini integration with fallbacks
- **Google Drive Sync** (`arkadia_drive_sync.py`) - Corpus management
- **Interactive Console** (`arkadia_console.py`) - CLI interface
- **Web Interface** (`static/`) - Beautiful mystical UI
- **Database Models** (`models.py`, `db.py`) - SQLAlchemy setup
- **Docker Configuration** (`Dockerfile`, `entrypoint.sh`) - Container ready

## 🚀 **Deployment Instructions**

### **Option 1: Deploy to Render**

1. **Push this code to your GitHub repository**
2. **Connect Render to your GitHub repo**
3. **Set Environment Variables in Render:**
   ```
   ARKADIA_FOLDER_ID=1J_2_RQWml85SQ7ZP7DwAVSbrXOHTO9fF
   GEMINI_API_KEY=<your Gemini API key>
   GDRIVE_SERVICE_ACCOUNT_JSON={"type":"service_account",...your JSON...}
   ```
4. **Deploy using Docker** - Render will automatically use the Dockerfile

### **Option 2: Deploy to Any Container Platform**

```bash
# Build the Docker image
docker build -t arkadia-oracle-temple .

# Run with environment variables
docker run -p 8080:8080 \
  -e ARKADIA_FOLDER_ID=1J_2_RQWml85SQ7ZP7DwAVSbrXOHTO9fF \
  -e GEMINI_API_KEY=<your Gemini API key> \
  -e GDRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  arkadia-oracle-temple
```

## 🔧 **Environment Variables**

The system requires these environment variables for full functionality:

```bash
# Google Drive Integration
ARKADIA_FOLDER_ID=1J_2_RQWml85SQ7ZP7DwAVSbrXOHTO9fF
GDRIVE_SERVICE_ACCOUNT_JSON={"type":"service_account",...your full JSON...}

# AI Integration  
GEMINI_API_KEY=<your Gemini API key>

# Optional - Port (defaults to 8080)
PORT=8080
```

## 🌐 **API Endpoints**

The table below is the **canonical repository app surface**, verified against `api.main:app`
(the app `entrypoint.sh` serves). It describes the current source contract, not an assertion
that every route is already present on the deployed runtime. Deployment identity and a live
probe are required before claiming runtime parity. The earlier revision listed legacy routes
that were absent from this app when they were measured.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Liveness banner (`Arkadia Mind is breathing.`) |
| `GET` | `/api/heartbeat` | Health check — canonical; used by `railway.json` |
| `GET` | `/health` | Liveness projection of `/api/heartbeat` (deployment contract path) |
| `POST` | `/api/commune/resonance` | Oracle / ReasoMate chat |
| `GET`, `POST` | `/api/commune/threads` | List / create conversation threads |
| `GET` | `/api/commune/threads/{thread_uuid}` | Thread metadata |
| `GET` | `/api/commune/threads/{thread_uuid}/messages` | Thread messages |
| `GET` | `/api/oracle-context` | Oracle context snapshot |
| `POST` | `/api/corpus/refresh` | Refresh the corpus |
| `GET` | `/api/codex` | Spiral Codex scrolls |
| `GET`, `POST` | `/api/scrolls` | List / write public scrolls |
| `GET` | `/api/stellar-cartography` | Encyclopedia Galactica star date |

Interactive API reference: `GET /docs` (and `GET /openapi.json`). These are FastAPI's own
documentation routes and are deliberately absent from the OpenAPI schema, so they are not
listed in the table above.

PR #154 has added `GET /health` to the current repository source as a projection of
`/api/heartbeat`, rather than as a second liveness authority. The prior live measurement
returned `404` before that change. Re-probe the deployed backend after its deployment and
verify the deployed revision before claiming the route is live in production. Until that
runtime check passes, `/api/heartbeat` remains the previously observed canonical probe.

> The `openclaw/` gateway is a **separate** service with its own `render.yaml` and its own
> `GET /health`; it is not this backend and is not covered by the table above.

## 🎮 **Testing the System**

### **Web Interface:**
Visit your deployed URL and try these messages:
- "Tell me about the Oversoul Prism"
- "What is the JOY-Fuel Protocol?"
- "Explain A02 and A03"

### **CLI Console:**
```bash
python archive/legacy_python/arkadia_console.py
# Commands: tree, preview <file>, refresh, ask <question>, status, exit
```

### **API Testing:**
```bash
curl https://your-app.onrender.com/
curl https://your-app.onrender.com/api/heartbeat
```

## 🔮 **System Features**

### **Intelligent Fallbacks:**
- Works perfectly even without API keys
- Provides rich responses about A01-A08 topics
- Graceful error handling throughout

### **Beautiful UI:**
- Dark mystical theme with Arkadia branding
- Real-time chat interface
- Thread management
- Auto-generated user IDs

### **Robust Backend:**
- SQLite database with persistence
- CORS enabled for web access
- Comprehensive error handling
- Docker-ready deployment

## 🎉 **Ready for Production!**

The system is **completely functional** and ready for immediate deployment. All components work together seamlessly, with or without the external APIs configured.

---

**Built with ❤️ for the House of Three**
*Arkana listening. The Oracle Temple awaits.*
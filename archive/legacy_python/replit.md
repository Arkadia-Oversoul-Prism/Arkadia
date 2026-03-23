# Arkadia - Arkana Oracle Temple

## Overview
Arkadia is a FastAPI-based AI Oracle application that combines:
- **Arkana Oracle Console**: A chat interface to interact with the AI oracle
- **Living Gate**: A status dashboard for the Arkadia system
- **Google Gemini AI**: For generating oracle responses
- **PostgreSQL Database**: For storing conversations and user data

## Project Structure
```
├── arkana_app.py          # Main FastAPI application
├── brain.py               # ArkanaBrain - high-level AI brain wrapper
├── codex_brain.py         # Low-level AI reasoning engine (Gemini integration)
├── db.py                  # Database configuration
├── models.py              # SQLAlchemy ORM models (User, Thread, Message)
├── arkadia_drive_sync.py  # Google Drive corpus sync
├── static/                # Oracle Console UI
├── gate/                  # Living Gate status UI
├── Oversoul_Prism/        # Documentation and specifications
└── 50_Code_Modules/       # Configuration JSON files
```

## Key Endpoints
- `GET /` - Oracle Console UI (main chat interface)
- `GET /gate/` - Living Gate status dashboard
- `POST /oracle` - Send message to Arkana oracle
- `GET /health` - Health check
- `GET /status` - System status
- `GET /arkadia/corpus` - View corpus context
- `GET /arkadia/refresh` - Refresh corpus cache

## Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string (auto-configured by Replit)
- `GEMINI_API_KEY` - Google Gemini API key for AI responses

## Optional Environment Variables
- `ARKADIA_FOLDER_ID` - Google Drive folder ID for corpus sync
- `GOOGLE_SERVICE_ACCOUNT_JSON_FILE` - Path to Google service account credentials
- `CODEX_MODEL` - Gemini model name (default: models/gemini-2.5-flash)
- `USE_RASA` - Enable Rasa backend (default: false)

## Deployment
### Backend (Render)
- **Environment**: Python/FastAPI
- **Start Command**: `uvicorn arkana_app:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health`
- **Heartbeat**: `/api/heartbeat` (Prevents sleep state)

### Frontend (Vercel)
- **Root Directory**: `web/public_prism`
- **Build Command**: `npm install && npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: `VITE_API_URL=https://arkadia-oracle.onrender.com`

## Notes
- The "Backend degraded" status appears when GEMINI_API_KEY is not set
- The oracle will provide fallback responses when the AI service is unavailable

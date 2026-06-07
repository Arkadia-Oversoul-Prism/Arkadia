# Arkadia Distribution Module

Sovereign music distribution for Arkadia artists. Upload a track, sign the covenant, submit to streaming platforms. Artist owns 100% of masters. Arkadia takes 5% (capped at $500 USD).

---

## Architecture Overview

```
Frontend (/distribute)        Backend (FastAPI)             Storage
──────────────────────        ─────────────────             ───────
Step 1: Upload Audio    ──►  POST /api/distribution/upload  data/releases.json
Step 2: Upload Artwork  ──►  (same request)                 static/releases/
Step 3: Metadata        ──►  (same request)
Step 4: Covenant        ──►  POST /api/distribution/covenant/sign  data/covenants.json
Step 5: Submit          ──►  POST /api/distribution/submit  → aggregator
                             GET  /api/distribution/releases/{artistId}
                             GET  /api/distribution/analytics/{releaseId}
```

---

## Frontend

### New Page: `/distribute`
- 5-step wizard: Audio → Artwork → Metadata → Covenant → Submit
- Drag-and-drop file upload with preview
- Covenant text displayed inline (plain language, scrollable)
- Progress indicator during upload/signing/submission
- Success screen with release ID and aggregator reference

### Dashboard Tab: Releases
- Navigate to Dashboard → "Releases" tab
- Shows all artist releases with status badges
- Filter by: All / Live / Processing / Submitted / Draft / Failed
- Click any release to open detail modal (metadata, covenant, analytics)
- Analytics visible for live releases

### Navigation
- "Distribute" link added to the Modules group in the side drawer
- Sigil: ⟁

---

## Backend Endpoints

### `POST /api/distribution/upload`
Accepts multipart/form-data with audio file, artwork file, and metadata fields.
- **audio**: MP3, WAV, or FLAC
- **artwork**: JPEG or PNG (min 2000×2000 recommended)
- **title**, **artistName**, **featuring**, **genre**, **releaseDate**, **isrc**, **upc**
- Returns: `{ releaseId, status: "draft", release }`

### `POST /api/distribution/covenant/sign`
Body: `{ releaseId, artistId, signedTerms: true }`
- Creates covenant record in `data/covenants.json`
- Updates release: `covenantSigned = true`
- Returns: `{ covenantId, signature, signedAt }`

### `POST /api/distribution/submit`
Body: `{ releaseId }`
- Validates: audio, artwork, metadata, covenant signed
- Calls aggregator (placeholder or live)
- Returns: `{ status: "processing", releaseId, aggregator: {...} }`

### `GET /api/distribution/releases/{artistId}`
Returns all releases for the artist.

### `GET /api/distribution/analytics/{releaseId}`
Returns streaming analytics (placeholder or live aggregator data).

### `GET /api/distribution/release/{releaseId}`
Returns full release detail including covenant.

---

## Aggregator Integration

### Current Mode: Placeholder

The placeholder aggregator:
1. Logs the submission request
2. Returns a mock success response with a fake reference ID
3. Sets release status to `live` after 30 seconds (simulates processing)

### Switching to a Live Aggregator

Set these environment variables:

```bash
AGGREGATOR=stem           # or: distrokid
AGGREGATOR_API_KEY=<key>  # your API key from STEM or DistroKid
```

Then replace the `_submit_to_aggregator()` function body in `api/distribution.py` with the live API call. The function signature and return shape should remain the same.

**STEM Disintermedia:** Apply at stem.is — mention you're an artist collective in Nigeria, 20-30 artists, revenue share model. Request API access.

**DistroKid:** White-label partner program. Contact partnerships@distrokid.com.

---

## Data Storage

MVP uses local JSON files (same pattern as existing `data/direct_scrolls.json`):

| File | Purpose |
|------|---------|
| `data/releases.json` | All release records |
| `data/covenants.json` | Signed covenant records |
| `static/releases/` | Uploaded audio and artwork files |

### Migrating to Firestore

When ready to migrate to Firebase Firestore:
1. Add `firebase-admin` to `requirements.txt`
2. Configure `FIREBASE_SERVICE_ACCOUNT` env secret
3. Replace `_load_releases()` / `_save_releases()` with Firestore CRUD in `api/distribution.py`
4. Collections to create: `releases`, `covenants`

---

## Firestore Security Rules (when migrated)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /releases/{releaseId} {
      allow read, write: if request.auth != null &&
        request.auth.uid == resource.data.artistId;
      allow create: if request.auth != null;
    }
    match /covenants/{covenantId} {
      allow read: if request.auth != null &&
        request.auth.uid == resource.data.artistId;
      allow create: if request.auth != null;
    }
  }
}
```

---

## Testing Checklist

- [ ] Artist can upload audio + artwork + metadata
- [ ] Covenant is displayed and must be agreed to before continuing
- [ ] Release is saved with status `draft` → `submitted` → `processing` → `live` (mock, ~30s)
- [ ] Dashboard "Releases" tab shows releases with correct status badges
- [ ] Navigation includes "Distribute" link in Modules group
- [ ] Existing pages (Home, Gate, Oracle, Reset, Nexus, Dashboard, About) unchanged
- [ ] Mobile responsive — tab strip works on small screens
- [ ] No console errors in browser

---

## The Covenant (Plain Language)

> You retain 100% ownership of your masters and publishing.
>
> Arkadia distributes your work through its pipeline to Spotify, Apple Music, Boomplay, and other major streaming platforms.
>
> Arkadia receives 5% of streaming revenue generated by this release, capped at $500 USD. This fee is collected only after you are paid by the aggregator.
>
> You may leave the Arkadia distribution network at any time. No exit fees. No lock-in. Your masters leave with you.

---

*The Return is now. ☀️*

# P1-A — Personal Identity + Private Codex Boundary + Unified Communication

**Start HEAD:** `7178c00` (post-P0 / P1-2 android docs)  
**Implementation:** `cd24bb1`  
**Execution status:** **PARTIAL** (code landed; production deploy of new routes pending verification)

---

## PRODUCT INTENT

«Arkadia must belong to the person using it.»

New users create their own display identity. Canonical/IMS material must not silently become their private identity. ReasoMate gains a real A↔B message path. Knowledge graph remains inspectable on mobile.

## IDENTITY MODEL

| Priority | Source |
|----------|--------|
| 1 | User-created profile store `data/user_profiles/{uid}.json` |
| 2 | Explicit Firebase `node_key` claim (IMS initiated nodes only) |
| 3 | Firebase `name` claim |
| 4 | Email local-part |

**Removed:** email-hint matching against `nodes_seed.json` for display identity.

## CHANGES

| Area | Change |
|------|--------|
| `api/auth.py` | Profile store; no email-hint identity; `profile_complete` |
| `api/nodes.py` | `PATCH /api/me` |
| `api/messages.py` | POST send, GET thread, GET inbox |
| Login/AuthContext | Display name on register → PATCH |
| ReasoMate | Server DMs; sample Zahrune/Jessica threads removed |
| KnowledgeGraphView | Responsive min-height; wrap/stack; touchAction |

## ACCEPTANCE (honest)

| Item | Result | Proof |
|------|--------|-------|
| A Identity self-created | **CODE-VERIFIED** | Login + PATCH; prod PATCH pending deploy |
| B No IMS email leakage | **CODE-VERIFIED** | build_user_profile change |
| C AIS boundary | **DOCUMENTED** | AIS not mandatory; signup only requires name |
| D Private Codex model | **PARTIAL** | Identity isolated; full Spiral Codex privatisation deferred |
| E Echo Field empty OK | **PASS** | P0-E retained |
| F ReasoMate A↔B | **CODE-VERIFIED** | messages API; prod 404 until deploy |
| G Graph mobile | **CODE-VERIFIED** | layout CSS |
| H Regression P0 | **PASS** | no ownership filter changes |

## OPEN LOOPS

- Production re-probe of PATCH /api/me + /api/messages after Render deploy  
- Full Spiral Codex surface re-label as per-user private (not just identity)  
- Avatar upload binary storage  
- AIS full questionnaire integration  
- Peer discovery (UID entry is minimal)

## FINAL GATE

**PARTIAL** — implement locally complete; await production route verification before GREEN.

## NEXT ACTION

After deploy: re-run A↔B message + PATCH profile production probe.  
**HUMAN REVIEW** before P1-B.

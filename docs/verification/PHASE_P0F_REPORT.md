# P0-F — Memory Governance

**Commit:** `bcda8a3`

## Architecture
Persistent personal memory = Knowledge OS notes stamped with `user_id`.
P0-F adds owner-only PATCH/DELETE and UI review/edit/delete.
Public/legacy (`user_id IS NULL`) cannot be deleted via personal path.

## Production security
- A create/edit/delete: PASS
- B get/delete A: 404
- Unauth PATCH/DELETE: 401
- List isolation (A title not in B list): PASS
- Local vault ownership unit: PASS

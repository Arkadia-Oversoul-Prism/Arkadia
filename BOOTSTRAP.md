# Arkadia — Bootstrap
> The session infrastructure has moved to `.bootstrap/`.

## Startup (read in order)
1. `.bootstrap/00_BOOT.md` — immutable rules, operating mode, thinking budget
2. `.bootstrap/01_STATE.md` — current checkpoint and objective
3. `.bootstrap/03_SCOPE.md` — what to touch, what to forbid, stop condition
4. Run `pytest tests/architecture/ -v` — confirm 10/10
5. Implement. Verify once (`04_SUCCESS.md`). Stop.

## Reference (consult only if needed)
- `.bootstrap/02_DECISIONS.md` — why decisions were made
- `REPOSITORY_SNAPSHOT.md` — full system map
- `NEXT_AGENT.md` — copy-paste handoff for the next session
- `PARKING_LOT.md` — log issues outside scope here, do not investigate

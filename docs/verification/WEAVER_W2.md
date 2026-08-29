# WEAVER-W2 — Browser Cockpit / Operational Observatory

**VIEW, NOT BRAIN**

## Launch

```bash
python -m weaver.workbench_app web
# http://127.0.0.1:8765/
```

## Module

`weaver/workbench_web.py` — stdlib `ThreadingHTTPServer` over W1 `workbench_view`.

Default: read-only analysis. Execution button disabled. Mutation path remains K3 only via K15 when separately authorized.

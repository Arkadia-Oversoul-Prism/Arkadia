# G12-C · Network-Triggered Reconciliation

Bounded move: add or repair connectivity-triggered reconciliation for pending capture records. Reconciliation is limited to capture synchronization and must not authorize or execute consequential work.

Required evidence: offline capture remains pending, connectivity transition triggers reconciliation, replay is idempotent, conflict remains terminal until human-visible resolution.

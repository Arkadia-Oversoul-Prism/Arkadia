# Trajectory Schema

**Move:** M08  
**Schema:** `docs/control-plane/trajectory.schema.json`  
**Instance:** `docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml`

Machine-readable trajectory for Weaver / Engineering Lab:

- trajectory identity, version, direction, authority
- moves: id, name, status, dependencies, scope (`spec`), packet
- review / merge / deploy remain human-gated fields on the trajectory object

Validation: `tests/test_m08_trajectory_schema.py`

# AEAS Browser Runner 01

An isolated Playwright instrument for browser-level verification of the Arkadia Engineering Lab.

## Boundary

- Targets a supplied URL, defaulting to the AEAS-01 Render PR service.
- Uses a real Chromium browser.
- Authentication, when enabled, goes through the deployed Login UI and real Firebase client flow.
- No JWT fabrication, localStorage injection, auth middleware bypass, or production mutation.
- Evidence is written to a local evidence directory.
- This runner is not part of the Engineering Lab runtime and does not create a second Lab runtime or EventStream.

## Modes

### Reachability probe

```bash
npm install
npm run install-browsers
TARGET_URL=https://arkadia-pr-337.onrender.com/solspire/engineering-lab npm run probe
```

### Authenticated probe

Supply a disposable Firebase test user's credentials only through the environment:

```bash
BROWSER_EMAIL='...' BROWSER_PASSWORD='...' \
TARGET_URL=https://arkadia-pr-337.onrender.com/solspire/engineering-lab \
npm run probe
```

Never commit credentials or browser state.

## Evidence

The runner emits:

- `browser-evidence.json`
- `render-pr.png`
- `engineering-lab-authenticated.png` when authenticated

The authenticated mode currently proves login and Lab surface reachability. SSE/event acceptance remains a separate scenario and must not be inferred from this probe.

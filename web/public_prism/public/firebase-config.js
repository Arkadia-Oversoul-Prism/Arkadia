// Inert default for the runtime-injected public Firebase Web config.
//
// index.html loads /firebase-config.js before the app bundle. In the canonical
// Render image entrypoint.sh overwrites this file in dist/ at container start
// with the public Firebase Web config from the environment. This committed copy
// keeps the referenced path resolvable for the Vite dev server and every static
// build, so the script tag never 404s. It carries no credentials.
window.__ARKADIA_FIREBASE_CONFIG__ = window.__ARKADIA_FIREBASE_CONFIG__ || {};

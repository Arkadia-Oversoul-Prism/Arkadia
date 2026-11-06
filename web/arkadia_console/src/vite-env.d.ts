/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_FIREBASE_API_KEY?: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN?: string;
  readonly VITE_FIREBASE_PROJECT_ID?: string;
  readonly VITE_FIREBASE_APP_ID?: string;
  /**
   * Disposable test identity (dev/test builds only). `"1"` opts in; the seam is
   * additionally gated on `import.meta.env.DEV`, so it is inert in production.
   * See `lib/testIdentity.ts`.
   */
  readonly VITE_ARKADIA_TEST_IDENTITY?: string;
  readonly VITE_ARKADIA_TEST_IDENTITY_SUBJECT?: string;
  readonly VITE_ARKADIA_TEST_IDENTITY_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

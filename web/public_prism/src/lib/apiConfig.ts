const RENDER_URL = '';

function androidApiBase(): { present: boolean; value: string } {
  if (typeof window === 'undefined') return { present: false, value: '' };
  const bridge = (window as Window & { ArkadiaAndroid?: { getApiBaseUrl?: () => string } }).ArkadiaAndroid;
  if (!bridge?.getApiBaseUrl) return { present: false, value: '' };
  try {
    return { present: true, value: bridge.getApiBaseUrl()?.replace(/\\/$/, '') || '' };
  } catch { return { present: true, value: '' }; }
}

const nativeApi = androidApiBase();
let _safeUrl: string;
if (nativeApi.present) {
  // Android is the authority for backend routing. An empty value is deliberate:
  // the app must not silently fall back to an unverified deployment.
  _safeUrl = nativeApi.value;
} else if (import.meta.env.DEV) {
  _safeUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\\/$/, '') ?? '';
} else {
  const raw = (import.meta.env.VITE_API_BASE_URL || RENDER_URL).replace(/\\/$/, '');
  _safeUrl = raw.startsWith('http') ? raw : RENDER_URL;
}
export const API_BASE_URL = _safeUrl;
export const API_BASE = _safeUrl;
export const ORACLE = _safeUrl;

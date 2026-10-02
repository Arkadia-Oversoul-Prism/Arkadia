const RENDER_URL = 'https://arkadia-kw64.onrender.com';

function androidApiBase(): string | null {
  if (typeof window === 'undefined') return null;
  const bridge = (window as Window & { ArkadiaAndroid?: { getApiBaseUrl?: () => string } }).ArkadiaAndroid;
  try {
    const value = bridge?.getApiBaseUrl?.();
    return value?.replace(/\/$/, '') || null;
  } catch { return null; }
}

let _safeUrl: string;
const nativeApi = androidApiBase();
if (nativeApi) {
  _safeUrl = nativeApi;
} else if (import.meta.env.DEV) {
  _safeUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? '';
} else {
  const raw = (import.meta.env.VITE_API_BASE_URL || RENDER_URL).replace(/\/$/, '');
  _safeUrl = raw.startsWith('http') ? raw : RENDER_URL;
}
export const API_BASE_URL = _safeUrl;
export const API_BASE = _safeUrl;
export const ORACLE = _safeUrl;

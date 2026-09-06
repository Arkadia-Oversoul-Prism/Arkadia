from pathlib import Path
import os
import re

ROOT = Path('web/public_prism/src')


def import_path(path: Path, target: str) -> str:
    target_path = ROOT / target
    rel = os.path.relpath(target_path, path.parent).replace('\\', '/')
    if not rel.startswith('.'):
        rel = './' + rel
    return rel.rsplit('.', 1)[0] if rel.endswith('.ts') or rel.endswith('.tsx') else rel


def ensure_import(text: str, statement: str) -> str:
    if statement in text:
        return text
    return statement + '\n' + text


def strip_auth_headers(text: str) -> str:
    text = re.sub(r"\s*Authorization\s*:\s*`Bearer \$\{[^}]+\}`\s*,?", '', text)
    text = re.sub(r"\s*Authorization\s*:\s*['\"]Bearer [^'\"]*['\"]\s*,?", '', text)
    text = re.sub(r"\s*Authorization\s*:\s*[^,}\n]+,?", '', text)
    return text


def migrate_file(path: Path, text: str) -> str:
    original = text
    if 'import.meta.env.VITE_API_BASE_URL' in text or 'import.meta.env.VITE_API_URL' in text:
        text = text.replace('import.meta.env.VITE_API_BASE_URL', 'API_BASE_CONFIG')
        text = text.replace('import.meta.env.VITE_API_URL', 'API_BASE_CONFIG')
        text = ensure_import(text, f"import {{ API_BASE as API_BASE_CONFIG }} from '{import_path(path, 'lib/apiConfig')}';")

    needs_api_fetch = False
    replacements = [
        (r'fetch\(`\$\{API_BASE\}([^`]*)`', r'apiFetch(`\1`)'),
        (r'fetch\(`\$\{ORACLE\}([^`]*)`', r'apiFetch(`\1`)'),
        (r'fetch\(API_BASE\s*\+\s*([\'\"`][^\n)]*)', r'apiFetch(\1)'),
        (r'fetch\(([/\'\"`]api/[^\n)]*)', r'apiFetch(\1)'),
        (r'fetch\(([/\'\"`]solspire/[^\n)]*)', r'apiFetch(\1)'),
        (r'fetch\(([/\'\"`]oracle[^\n)]*)', r'apiFetch(\1)'),
        (r'fetch\(([/\'\"`]status[^\n)]*)', r'apiFetch(\1)'),
    ]
    for pattern, replacement in replacements:
        new = re.sub(pattern, replacement, text)
        if new != text:
            needs_api_fetch = True
            text = new
    if needs_api_fetch:
        text = ensure_import(text, f"import {{ apiFetch }} from '{import_path(path, 'lib/apiClient')}';")

    text = strip_auth_headers(text)
    text = re.sub(r"localStorage\.getItem\(['\"]arkadia_token['\"]\)\s*\|\|\s*['\"]['\"]", "''", text)
    text = re.sub(r"localStorage\.getItem\(['\"]arkadia_token['\"]\)", "null", text)
    return text


def migrate_project_dashboard(path: Path, text: str) -> str:
    text = ensure_import(text, "import { apiRequest } from '../lib/apiClient';")
    text = re.sub(
        r"\nconst ORACLE = \(API_BASE_CONFIG \|\| 'http://localhost:8000'\)\.replace\(/\\/\$, ''\);\n",
        '\n',
        text,
        count=1,
    )
    legacy = re.search(r"// ── API ─+[\s\S]*?// ── Helpers ─+", text)
    if legacy:
        replacement = """// ── API ───────────────────────────────────────────────────────────────────────

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────"""
        text = text[:legacy.start()] + replacement + text[legacy.end():]
    text = text.replace(
        "const base = `${ORACLE}/solspire/projects/${project.id}/weaver`;",
        "const base = `/solspire/projects/${project.id}/weaver`;",
    )
    text = re.sub(
        r"\n  const token = \(\) => localStorage\.getItem\('arkadia_token'\) \|\| '';\n  const authHeaders = \(\) => \(\{[\s\S]*?\n  \}\);\n",
        '\n',
        text,
        count=1,
    )
    text = text.replace(
        "fetch(`${base}/capabilities`, { headers: { Authorization: `Bearer ${token()}` } })",
        "apiFetch(`${base}/capabilities`)",
    )
    text = re.sub(r"fetch\(`(\$\{base\}|\$\{execBase\})", r"apiFetch(`\1", text)
    text = strip_auth_headers(text)
    text = text.replace("localStorage.getItem('arkadia_token') || ''", "''")
    text = ensure_import(text, "import { apiFetch } from '../lib/apiClient';")
    return text


changed = []
for path in ROOT.rglob('*'):
    if path.suffix not in {'.ts', '.tsx'}:
        continue
    text = path.read_text()
    if path in {ROOT / 'lib' / 'apiClient.ts', ROOT / 'lib' / 'apiConfig.ts'}:
        continue
    migrated = migrate_file(path, text)
    if path == ROOT / 'pages' / 'ProjectDashboard.tsx':
        migrated = migrate_project_dashboard(path, migrated)
    if migrated != text:
        path.write_text(migrated)
        changed.append(str(path))

print('\n'.join(changed))

from __future__ import annotations

import hashlib, json, logging, os, re, sqlite3, threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import requests

logger = logging.getLogger("arkadia.economic_seams")
DB_PATH = os.environ.get("ECONOMIC_SEAMS_DB") or os.path.join(os.environ.get("SOLSPIRE_DATA_DIR", "data"), "economic_seams.db")
DEFAULT_INTERVAL = int(os.environ.get("ECONOMIC_SEAM_INTERVAL_SECONDS", "1800"))
THREAD = None
STOP = threading.Event()

@dataclass(frozen=True)
class Source:
    id: str
    name: str
    domain: str
    url: str
    class_name: str
    legal_basis: str
    enabled: bool = True

SOURCES = [
    Source("nocopo", "Nigeria Open Contracting Portal", "bpp.gov.ng", "https://nocopo.bpp.gov.ng/OpenData.aspx", "PROCUREMENT", "Public Procurement Act 2007 / OCDS publication"),
    Source("nipc", "Nigerian Investment Promotion Commission", "nipc.gov.ng", "https://nipc.gov.ng/publications/categories/investor-guidance", "INCENTIVE", "Nigeria Tax Act 2025 and published NIPC incentive guidance"),
    Source("nerc", "Nigerian Electricity Regulatory Commission", "nerc.gov.ng", "https://nerc.gov.ng/resource-category/nerc-reports/", "ENERGY", "Electricity Act 2023 and NERC regulatory instruments"),
    Source("ncc", "Nigerian Communications Commission", "ncc.gov.ng", "https://www.ncc.gov.ng/media-center/public-notices", "TELECOM", "NCC Act and applicable spectrum/licensing rules"),
    Source("nuprc", "Nigerian Upstream Petroleum Regulatory Commission", "nuprc.gov.ng", "https://www.nuprc.gov.ng/media/news/", "PETROLEUM", "Petroleum Industry Act 2021 and NUPRC regulations"),
    Source("nmdpra", "Nigerian Midstream and Downstream Petroleum Regulatory Authority", "nmdpra.gov.ng", "https://nmdpra.gov.ng/", "PETROLEUM", "Petroleum Industry Act 2021 and applicable NMDPRA instruments"),
    Source("sec", "Securities and Exchange Commission Nigeria", "sec.gov.ng", "https://sec.gov.ng/", "CAPITAL_MARKETS", "Investments and Securities Act 2025 and SEC rules"),
    Source("cbn", "Central Bank of Nigeria", "cbn.gov.ng", "https://www.cbn.gov.ng/", "FINANCE", "CBN Act, banking/payment regulations and applicable circulars"),
    Source("niser", "Nigerian Institute of Social and Economic Research", "niser.gov.ng", "https://niser.gov.ng/v2/niser-economic-intelligence-report-2026/", "MACRO", "Public economic research; not itself a transaction authorization"),
    Source("worldbank_procurement", "World Bank Procurement Notices", "worldbank.org", "https://projects.worldbank.org/en/projects-operations/procurement", "DONOR_PROCUREMENT", "World Bank procurement framework and project procurement rules"),
    Source("afdb_procurement", "African Development Bank Current Solicitations RSS", "afdb.org", "https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations.xml", "DONOR_PROCUREMENT", "AfDB procurement framework and solicitation rules"),
    Source("afdb_trade_finance", "African Development Bank Trade Finance Program", "afdb.org", "https://www.afdb.org/en/topics-and-sectors/initiatives-partnerships/trade-finance-program", "TRADE_FINANCE", "AfDB Trade Finance Program instruments and eligibility rules"),
    Source("ifc_trade_finance", "IFC Global Supply Chain Finance", "ifc.org", "https://www.ifc.org/en/what-we-do/sector-expertise/trade-and-supply-chain-finance/global-supply-chain-finance", "TRADE_FINANCE", "IFC Global Supply Chain Finance program terms and partner-bank structures"),
    Source("ngx_disclosures", "Nigerian Exchange Disclosures", "ngxgroup.com", "https://ngxgroup.com/exchange/trade/investor-protection-education/x-compliance-report/", "PUBLIC_FILINGS", "NGX Listing Rules and issuer disclosure requirements"),
    Source("cbn_fx", "CBN Exchange Rates", "cbn.gov.ng", "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html", "FX", "CBN official foreign-exchange market rate publication"),
    Source("nepc_prices", "NEPC Indicative Market Prices", "nepc.gov.ng", "https://nepc.gov.ng/indicative-market-prices/", "COMMODITY_PRICES", "NEPC published indicative export commodity market prices"),
    Source("carbon_registry", "Carbon Registry", "carbonregistry.com", "https://www.carbonregistry.com/project-registration", "CARBON", "Registry terms and applicable carbon-market rules; project eligibility remains to be verified"),
]

KEYWORDS = {
    "incentive": re.compile(r"tax credit|tax incentive|duty waiver|grant|rebate|relief|credit certificate|exemption", re.I),
    "procurement": re.compile(r"tender|procurement|request for proposal|award|contract|framework agreement", re.I),
    "energy": re.compile(r"mini-grid|solar|generation|electricity|battery|gas-to-power|flare|watt|mw|mwh", re.I),
    "finance": re.compile(r"trade finance|guarantee|factoring|forfait|working capital|letter of credit|export finance|sandbox", re.I),
    "market": re.compile(r"exchange|warehouse receipt|commodity|carbon|registry|licence|license|spectrum", re.I),
}

def _now(): return datetime.now(timezone.utc).isoformat()

def _db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS source_runs (source_id TEXT PRIMARY KEY, last_run TEXT, status TEXT, item_count INTEGER DEFAULT 0, error TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, source_id TEXT, url TEXT, title TEXT, published_at TEXT, fetched_at TEXT, content_hash TEXT, excerpt TEXT, legal_basis TEXT, evidence_level TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, title TEXT, seam_type TEXT, status TEXT, legal_basis TEXT, evidence_ids TEXT, evidence_level TEXT, rationale TEXT, created_at TEXT, updated_at TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_obs_source ON observations(source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status)")
    return c

def _clean_html(raw):
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", raw, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    from html import unescape
    return re.sub(r"\s+", " ", unescape(text)).strip()

def _fetch(source):
    r = requests.get(source.url, timeout=25, headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
    r.raise_for_status()
    return r.url, _clean_html(r.text)[:2000000]

def _excerpt(text):
    hits = []
    for rx in KEYWORDS.values():
        m = rx.search(text)
        if m: hits.append(text[max(0, m.start()-240):m.end()+480])
    return " ".join(hits)[:1800] or text[:1200]

def _upsert_observation(c, source, url, text):
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    oid = hashlib.sha256(f"{source.id}:{url}:{h}".encode()).hexdigest()[:24]
    c.execute("INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)",
              (oid, source.id, url, f"{source.name} feed snapshot", None, _now(), h, _excerpt(text), source.legal_basis, "SOURCE_VERIFIED"))
    return oid

def _detect(c, source, oid, excerpt):
    kinds = [k for k, rx in KEYWORDS.items() if rx.search(excerpt)]
    created = []
    if not source.legal_basis or not kinds: return created
    for kind in sorted(set(kinds)):
        title = f"{source.name}: {kind} seam signal"
        raw_id = hashlib.sha256(f"{source.id}:{kind}:{excerpt[:600]}".encode()).hexdigest()[:20]
        row = c.execute("SELECT id FROM opportunities WHERE id=?", (raw_id,)).fetchone()
        if row:
            c.execute("UPDATE opportunities SET updated_at=?, evidence_ids=?, evidence_level=? WHERE id=?",
                      (_now(), json.dumps([oid]), "SOURCE_VERIFIED", raw_id))
            continue
        rationale = (f"Detected {kind} language in an official/public source. This is a lead, not a financial conclusion. "
                     f"Legal basis: {source.legal_basis}. Evidence: {source.url}. Independent transaction, eligibility, pricing and counterparty verification are still required.")
        c.execute("INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (raw_id, title, kind, "LEAD", source.legal_basis, json.dumps([oid]), "SOURCE_VERIFIED", rationale, _now(), _now()))
        created.append(raw_id)
    return created

def _scan_nocopo(c, source):
    """Persist structured OCDS records and create leads only for plausible active tenders."""
    from economic_seams.nocopo import fetch_records
    records = fetch_records()
    created = []
    for record in records:
        serialized = json.dumps(record, sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        ocid = record.get("ocid") or content_hash[:20]
        oid = hashlib.sha256(f"{source.id}:{ocid}:{content_hash}".encode()).hexdigest()[:24]
        excerpt = serialized[:1800]
        c.execute(
            "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (oid, source.id, record.get("source_url") or source.url,
             record.get("title") or f"NOCOPO contracting process {ocid}",
             record.get("tender_end_date") or None, _now(), content_hash, excerpt,
             source.legal_basis, "STRUCTURED_SOURCE"),
        )
        if not record.get("active_tender_lead"):
            continue
        raw_id = hashlib.sha256(f"{source.id}:{ocid}:active-tender".encode()).hexdigest()[:20]
        rationale = (
            "Structured NOCOPO/OCDS snapshot contains a tender marked active/planned "
            "with a plausible deadline window. This is a lead, not proof that the tender "
            "remains open or that the operator is eligible. Recheck the primary notice, "
            "documents, deadline, qualification criteria and legal basis before action. "
            f"Snapshot: {record.get('source_snapshot')}. Quality flags: "
            f"{', '.join(record.get('quality_flags') or []) or 'none'}."
        )
        existing = c.execute("SELECT id FROM opportunities WHERE id=?", (raw_id,)).fetchone()
        if existing:
            c.execute(
                """UPDATE opportunities SET title=?, status='LEAD', legal_basis=?,
                   evidence_ids=?, evidence_level='STRUCTURED_SOURCE', rationale=?, updated_at=?
                   WHERE id=?""",
                (record.get("title") or f"NOCOPO tender {ocid}", source.legal_basis,
                 json.dumps([oid]), rationale, _now(), raw_id),
            )
        else:
            c.execute(
                "INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,?)",
                (raw_id, record.get("title") or f"NOCOPO tender {ocid}", "procurement",
                 "LEAD", source.legal_basis, json.dumps([oid]), "STRUCTURED_SOURCE",
                 rationale, _now(), _now()),
            )
            created.append(raw_id)
    return records, created


def _scan_afdb_procurement(c, source):
    """Persist individual notices from AfDB's documented current-solicitations RSS feed."""
    from economic_seams.market_data import fetch_afdb_procurement_items
    items = fetch_afdb_procurement_items(requests, source.url, timeout=25)
    created = []
    for item in items:
        text = f"{item['title']} {item.get('excerpt') or ''}".strip()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        oid = hashlib.sha256(f"{source.id}:{item['source_url']}:{digest}".encode("utf-8")).hexdigest()[:24]
        excerpt = _excerpt(text)
        c.execute(
            "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (oid, source.id, item["source_url"], item["title"], item.get("published_at"),
             _now(), digest, excerpt[:1800], source.legal_basis, "OFFICIAL_RSS_ITEM"),
        )
        created.extend(_detect(c, source, oid, excerpt))
    return items, created


def _scan_market_reference(c, source):
    """Persist parsed CBN FX / NEPC price rows as unclassified observations."""
    from economic_seams.market_data import fetch_nepc_price_rows, parse_cbn_nfem_rows
    if source.id == "nepc_prices":
        rows = fetch_nepc_price_rows(requests, source.url, timeout=25)
        observation_url = source.url
    else:
        response = requests.get(source.url, timeout=25, headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
        response.raise_for_status()
        observation_url = response.url
        rows = parse_cbn_nfem_rows(response.text, source_url=observation_url)
    if not rows:
        raise ValueError("No parseable market reference rows found; source layout may have changed")
    for row in rows:
        raw = json.dumps(row, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        oid = hashlib.sha256(f"{source.id}:{digest}".encode("utf-8")).hexdigest()[:24]
        labels = " / ".join(row.get("labels", []) or [row.get("commodity_unit_heading", ""), row.get("state", "")])
        c.execute("INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (oid, source.id, row.get("source_url") or observation_url, f"{source.name}: {labels[:160]}", None, _now(), digest, raw[:1800], source.legal_basis, "UNCLASSIFIED_REFERENCE_ROW"))
    return rows

def scan_once():
    c = _db(); counts = {}; created = []
    for source in SOURCES:
        if not source.enabled: continue
        try:
            if source.id == "nocopo":
                records, source_created = _scan_nocopo(c, source)
                created.extend(source_created)
                item_count = len(records)
            elif source.id == "afdb_procurement":
                records, source_created = _scan_afdb_procurement(c, source)
                created.extend(source_created)
                item_count = len(records)
            elif source.id in {"cbn_fx", "nepc_prices"}:
                item_count = len(_scan_market_reference(c, source))
            else:
                url, text = _fetch(source)
                oid = _upsert_observation(c, source, url, text)
                created += _detect(c, source, oid, _excerpt(text))
                item_count = 1
            c.execute("INSERT OR REPLACE INTO source_runs VALUES (?,?,?,?,?)",
                      (source.id, _now(), "ok", item_count, None))
            counts[source.id] = "ok"
        except Exception as exc:
            logger.warning("[SEAM] %s failed: %s", source.id, exc)
            c.execute("INSERT OR REPLACE INTO source_runs VALUES (?,?,?,?,?)",
                      (source.id, _now(), "error", 0, str(exc)[:500]))
            counts[source.id] = "error"
    c.commit(); c.close()
    return {"scanned_at": _now(), "sources": counts, "new_opportunities": created, "count": len(created)}

def list_opportunities(limit=100, status=None):
    c = _db(); q = "SELECT * FROM opportunities"; args = []
    if status: q += " WHERE status=?"; args.append(status)
    q += " ORDER BY updated_at DESC LIMIT ?"; args.append(min(max(limit,1),500))
    rows = [dict(r) for r in c.execute(q,args).fetchall()]; c.close()
    for r in rows: r["evidence_ids"] = json.loads(r["evidence_ids"] or "[]")
    return rows

def get_status():
    c = _db()
    runs = [dict(r) for r in c.execute("SELECT * FROM source_runs ORDER BY source_id").fetchall()]
    count = c.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    c.close()
    return {"engine":"economic-seam-engine","running":THREAD is not None and THREAD.is_alive(),
            "interval_seconds":DEFAULT_INTERVAL,"opportunity_count":count,
            "sources":[asdict(s) for s in SOURCES],"runs":runs}

def _loop():
    while not STOP.is_set():
        try: scan_once()
        except Exception: logger.exception("[SEAM] scan failed")
        STOP.wait(DEFAULT_INTERVAL)

def start():
    global THREAD
    if THREAD and THREAD.is_alive(): return False
    STOP.clear(); THREAD = threading.Thread(target=_loop, name="economic-seam-engine", daemon=True); THREAD.start(); return True

def stop():
    STOP.set()

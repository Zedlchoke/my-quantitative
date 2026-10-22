"""FREE-WEB RESEARCH TOOLS (PAPERDESK-FIXALL-NCAA-V1 FREE-RESEARCH R1,
owner order 2026-10-22) — tim_web (Tavily Search) + mo_trang (page
reader), executed ONLY by desk code, never by the model.

BACKBONE LAW (coordinator, 2026-10-22): FREE TO READ, DISCIPLINED
VERDICT. The model issues tool calls; this module executes them; EVERY
result — success or failure — is journaled VERBATIM into the research
journal keyed by candidate_hash. A final verdict may cite only URLs that
exist in the union set (base packet + this journal) — the U0 citation
filter applies unchanged over that union.

HARD GUARDS:
  * the Tavily key comes from the macOS Keychain at call time (key_ref,
    same shape as the OpenRouter key) and never enters repo/logs/config/
    handovers;
  * mo_trang speaks ONLY public http/https: any private, loopback,
    link-local, reserved, multicast or unresolved-after-resolution host
    is REFUSED (the DNS result is checked, not just the literal host);
  * every failure returns an HONEST ToolError to the conversation — the
    research round degrades to the base packet, the gate never locks and
    nothing is ever invented to fill a gap;
  * a dev-plan Tavily key carries a small monthly credit budget
    (documented 1,000 credits/month at build time) — callers must count
    calls (journal.tool_stats) and treat 429/432 as quota exhaustion.

All transport goes through injectable seams (tavily_transport /
page_transport); the battery never touches the network.
"""
from __future__ import annotations

import hashlib
import html as _html
import ipaddress
import json
import re
import socket
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

TAVILY_ENDPOINT = "https://api.tavily.com/search"
KEY_REF_DEFAULT = "com.myquant.paperdesk / tavily-api-key"

DEFAULT_MAX_RESULTS = 5
PAGE_TIMEOUT_S = 20
PAGE_MAX_BYTES = 3_000_000        # transport cap before cleaning
DEFAULT_PAGE_CHARS = 400_000      # cleaned-text cap handed to the caller
JOURNAL_EXCERPT_CHARS = 3_000     # what a reused journal re-presents
QUERY_MAX_CHARS = 400

ALLOWED_PORTS = (None, 80, 443)

TOOL_NAMES = ("tim_web", "mo_trang")

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "tim_web",
        "description": (
            "Search the public web (Tavily) for news/injury/lineup "
            "information about the fixture. Returns a list of "
            "{url, title, excerpt, published_utc}."),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "search query (<= 400 chars)"},
                "max_results": {"type": "integer", "minimum": 1,
                                "maximum": 10},
            },
            "required": ["query"],
        },
    }},
    {"type": "function", "function": {
        "name": "mo_trang",
        "description": (
            "Open ONE public http(s) page and return its cleaned text "
            "(scripts/styles/tags stripped, length-capped). Use it to "
            "read a source you found with tim_web."),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
            },
            "required": ["url"],
        },
    }},
]


class ToolError(Exception):
    """An honest, typed tool failure (never a fabricated result).
    .kind: bad_input | blocked | network | quota | http."""

    def __init__(self, message: str, kind: str = "network"):
        super().__init__(message)
        self.kind = kind


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def keychain_key(key_ref: str) -> str:
    """Same law as ai_producer.keychain_key (`<service> / <account>`),
    kept as a local copy so this module stays import-cycle-free (the
    producer imports THIS module). Key bytes never enter repo/logs."""
    ref = " ".join(str(key_ref or "").split())
    if "/" in ref:
        service, account = [x.strip() for x in ref.rsplit("/", 1)]
    else:
        service, account = ref, ref
    out = subprocess.run(["/usr/bin/security", "find-generic-password",
                          "-s", service, "-a", account, "-w"],
                         capture_output=True, text=True, timeout=15)
    key = (out.stdout or "").strip()
    if out.returncode != 0 or not key:
        raise RuntimeError("keychain lookup failed for "
                           f"{service}/{account}: {out.stderr.strip()[:120]}")
    return key


# ------------------------------------------------------------ SSRF guard ----

def _assert_fetchable(url: str) -> str:
    """Public http(s) only. The DNS RESOLUTION is checked address-by-
    address: every resolved IP must be globally routable — a name that
    resolves to loopback/private/link-local/reserved/multicast space is
    refused even when the literal hostname looks harmless."""
    p = urllib.parse.urlsplit(str(url or "").strip())
    if p.scheme not in ("http", "https"):
        raise ToolError(f"mo_trang refuses scheme {p.scheme!r} "
                        "(public http/https only)", kind="blocked")
    if p.username or p.password:
        raise ToolError("mo_trang refuses URLs with embedded credentials",
                        kind="blocked")
    if p.port not in ALLOWED_PORTS:
        raise ToolError(f"mo_trang refuses port {p.port}", kind="blocked")
    host = (p.hostname or "").lower()
    if not host:
        raise ToolError("mo_trang refuses a URL without a hostname",
                        kind="bad_input")
    if host == "localhost" or host.endswith((".local", ".internal",
                                             ".localhost")):
        raise ToolError(f"mo_trang refuses internal host {host!r}",
                        kind="blocked")
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        raise ToolError(f"DNS resolution failed for {host!r}: "
                        f"{type(e).__name__}", kind="network") from e
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            raise ToolError(f"unparsable resolved address for {host!r}",
                            kind="blocked")
        if not (ip.is_global and not ip.is_loopback and not ip.is_private
                and not ip.is_link_local and not ip.is_reserved
                and not ip.is_multicast and not ip.is_unspecified):
            raise ToolError(f"mo_trang refuses non-public resolved "
                            f"address {ip} for {host!r}", kind="blocked")
    return url


# ----------------------------------------------------------- page cleaner ---

class _TextOut(HTMLParser):
    """Minimal tag-stripping text collector: skips script/style/noscript
    and template blocks entirely; everything else becomes text."""

    _SKIP = {"script", "style", "noscript", "template", "svg", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth and data.strip():
            self._chunks.append(data.strip())


def clean_html(raw: str, *, max_chars: int) -> str:
    """script/style/tag-free text, whitespace-collapsed, length-capped."""
    p = _TextOut()
    try:
        p.feed(raw)
    except Exception:
        # a parser hiccup must never crash a research round: fall back to
        # a regex strip of the most common block elements
        txt = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>",
                     " ", raw)
        txt = re.sub(r"(?s)<[^>]+>", " ", txt)
        return _html.unescape(re.sub(r"\s+", " ", txt))[:max_chars]
    return re.sub(r"\s+", " ", " ".join(p._chunks))[:max_chars]


# ---------------------------------------------------------------- journal ---

class ResearchJournal:
    """The verbatim tool journal bound to ONE candidate_hash. The union
    citation set (base packet + journal.sources) is the ONLY set a final
    verdict may cite from (U0 law over the enlarged set)."""

    SCHEMA = "research_journal@1"

    def __init__(self, path: Path, candidate_hash: str):
        self.path = Path(path)
        self.data = {"schema": self.SCHEMA,
                     "candidate_hash": candidate_hash,
                     "created_at_utc": _now(), "updated_utc": _now(),
                     "entries": [], "sources": []}

    # -- lifecycle ---------------------------------------------------------
    @classmethod
    def load(cls, path: Path, candidate_hash: str, *,
             freshness_hours: float) -> tuple["ResearchJournal", bool]:
        """Load an existing journal for this candidate; returns
        (journal, reused). reused=True only when the journal exists AND
        parses AND is inside the freshness window — a stale journal is
        kept as HISTORY but not reused (the caller re-researches and the
        journal is re-created; the stale file is never silently merged)."""
        path = Path(path)
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return cls(path, candidate_hash), False
        if not isinstance(raw, dict) or \
                raw.get("candidate_hash") != candidate_hash:
            return cls(path, candidate_hash), False
        j = cls(path, candidate_hash)
        j.data = raw
        try:
            created = datetime.strptime(
                str(raw.get("created_at_utc")),
                "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - created)\
                .total_seconds() / 3600.0
        except (ValueError, TypeError):
            return j, False
        return j, (age_h <= float(freshness_hours))

    def save(self) -> None:
        self.data["updated_utc"] = _now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, sort_keys=True,
                                        ensure_ascii=False))

    # -- recording ---------------------------------------------------------
    def add_entry(self, entry: dict) -> None:
        """One VERBATIM tool record (call, results/errors, timestamps)."""
        self.data["entries"].append({"ts_utc": _now(), **entry})

    def add_source(self, src: dict) -> None:
        """The union citation set only ever grows with URLs that were
        actually returned by an executed tool (never model-claimed)."""
        url = str(src.get("url") or "")
        if not url:
            return
        if any(s.get("url") == url for s in self.data["sources"]):
            return
        self.data["sources"].append({
            "url": url[:400],
            "excerpt": str(src.get("excerpt") or "")[:280],
            "fetched_at_utc": src.get("fetched_at_utc") or _now(),
            "published_utc": src.get("published_utc") or "",
            "kind": src.get("kind") or "web"})

    def tool_stats(self) -> dict:
        entries = self.data.get("entries") or []
        tim = [e for e in entries if e.get("tool") == "tim_web"
               and not e.get("error")]
        mo = [e for e in entries if e.get("tool") == "mo_trang"
              and not e.get("error")]
        return {"tavily_calls": len(tim), "page_fetches": len(mo),
                "tool_errors": len(entries) - len(tim) - len(mo)}


# -------------------------------------------------------------- transports --

def _default_tavily_transport(url: str, body: bytes,
                              headers: dict) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:          # noqa: typed for the caller
        raise ToolError(f"Tavily HTTP {e.code}: {e.reason}",
                        kind="quota" if e.code in (429, 432) else "http")


def _default_page_transport(url: str, headers: dict) -> tuple[str, bytes]:
    _assert_fetchable(url)
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=PAGE_TIMEOUT_S) as r:
            ctype = (r.headers or {}).get("Content-Type") or ""
            return ctype, r.read(PAGE_MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise ToolError(f"HTTP {e.code} fetching the page",
                        kind="http") from e
    except (TimeoutError, socket.timeout) as e:
        raise ToolError(f"page fetch timeout: {type(e).__name__}",
                        kind="network") from e
    except OSError as e:
        raise ToolError(f"network failure: {type(e).__name__}",
                        kind="network") from e


# ------------------------------------------------------------ the 2 tools ---

def tim_web(query: str, *, key: str, max_results: int = DEFAULT_MAX_RESULTS,
            transport=None) -> list[dict]:
    """Tavily Search -> normalized [{url, title, excerpt, published_utc}].
    Raises ToolError(kind=quota) on 429/432 (dev-plan credit exhaustion)
    and ToolError(kind=network|http) on anything else — the honest error
    travels to the model; nothing is invented."""
    query = str(query or "").strip()
    if not query:
        raise ToolError("tim_web: empty query", kind="bad_input")
    if len(query) > QUERY_MAX_CHARS:
        query = query[:QUERY_MAX_CHARS]
    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = DEFAULT_MAX_RESULTS
    max_results = max(1, min(10, max_results))
    body = json.dumps({"query": query, "max_results": max_results,
                       "search_depth": "basic"}).encode()
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {key}"}
    fn = transport or _default_tavily_transport
    status, raw = fn(TAVILY_ENDPOINT, body, headers)
    try:
        env = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ToolError("Tavily returned an unparsable body",
                        kind="http") from e
    out = []
    for r in (env.get("results") or [])[:max_results]:
        if not isinstance(r, dict) or not r.get("url"):
            continue
        out.append({"url": str(r["url"])[:400],
                    "title": str(r.get("title") or "")[:280],
                    "excerpt": str(r.get("content") or "")[:280],
                    "published_utc": str(r.get("published_date") or "")})
    return out


def mo_trang(url: str, *, transport=None,
             max_chars: int = DEFAULT_PAGE_CHARS) -> dict:
    """Open ONE public page, clean it, cap it. Returns {url, text,
    sha256, content_type}. Every rejection is an honest ToolError."""
    url = str(url or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        raise ToolError("mo_trang: url must start with http(s)://",
                        kind="bad_input")
    if len(url) > 2000:
        raise ToolError("mo_trang: url too long", kind="bad_input")
    _assert_fetchable(url)                       # second gate (transport
    fn = transport or _default_page_transport    # re-checks after DNS too)
    ctype, raw = fn(url, {"User-Agent": "PaperDesk-research/1",
                          "Accept": "text/html,text/plain,application/json"})
    if len(raw) > PAGE_MAX_BYTES:
        raw = raw[:PAGE_MAX_BYTES]
    main = (ctype or "").split(";")[0].strip().lower()
    if main and not (main.startswith("text/") or
                     main in ("application/json",
                              "application/xhtml+xml",
                              "application/xml")):
        raise ToolError(f"mo_trang refuses content-type {main!r}",
                        kind="blocked")
    charset = "utf-8"
    m = re.search(r"charset=([\w\-]+)", ctype or "", re.I)
    if m:
        charset = m.group(1)
    try:
        text_raw = raw.decode(charset, errors="replace")
    except LookupError:
        text_raw = raw.decode("utf-8", errors="replace")
    text = clean_html(text_raw, max_chars=max_chars)
    if not text.strip():
        raise ToolError("page carried no readable text", kind="http")
    return {"url": url, "text": text, "sha256": hashlib.sha256(
        text.encode()).hexdigest(), "content_type": main or "unknown"}


# ----------------------------------------------------- executor for the loop

def execute_tool(name: str, arguments: dict, *, journal: ResearchJournal,
                 tavily_key: str, max_results: int = DEFAULT_MAX_RESULTS,
                 max_page_chars: int = DEFAULT_PAGE_CHARS,
                 tavily_transport=None, page_transport=None) -> tuple[str, int]:
    """Execute ONE model-issued tool call; journal it verbatim; return
    (tool_result_json, pages_fetched). A failure returns an honest error
    JSON (the conversation degrades to the base packet) — never content
    invented to fill the gap."""
    name = str(name or "").strip()
    arguments = arguments if isinstance(arguments, dict) else {}
    try:
        if name == "tim_web":
            results = tim_web(arguments.get("query"),
                              key=tavily_key,
                              max_results=arguments.get("max_results",
                                                        max_results),
                              transport=tavily_transport)
            journal.add_entry({"tool": "tim_web", "query":
                               str(arguments.get("query") or "")[:QUERY_MAX_CHARS],
                               "max_results": max_results,
                               "http": "ok", "results_verbatim": results})
            now = _now()
            for r in results:
                journal.add_source({
                    "url": r["url"],
                    "excerpt": (f"{r['title']} — {r['excerpt']}"
                                ).strip(" —"),
                    "fetched_at_utc": now,
                    "published_utc": r["published_utc"],
                    "kind": "web_search"})
            return json.dumps({"tool": "tim_web", "results": results},
                              ensure_ascii=False), 0
        if name == "mo_trang":
            page = mo_trang(arguments.get("url"), transport=page_transport,
                            max_chars=max_page_chars)
            now = _now()
            journal.add_entry({
                "tool": "mo_trang", "url": page["url"],
                "fetched_at_utc": now,
                "sha256": page["sha256"],
                "chars": len(page["text"]),
                "content_type": page["content_type"],
                "excerpt_for_model": page["text"][:JOURNAL_EXCERPT_CHARS]})
            journal.add_source({
                "url": page["url"],
                "excerpt": page["text"][:280],
                "fetched_at_utc": now,
                "kind": "web_page"})
            return json.dumps({"tool": "mo_trang",
                               "url": page["url"],
                               "sha256": page["sha256"],
                               "chars": len(page["text"]),
                               "text": page["text"][:JOURNAL_EXCERPT_CHARS]},
                              ensure_ascii=False), 1
        raise ToolError(f"unknown tool {name!r}", kind="bad_input")
    except ToolError as e:
        journal.add_entry({"tool": name, "arguments":
                           {k: str(v)[:200] for k, v in
                           (arguments or {}).items()},
                           "error": str(e)[:300], "error_kind": e.kind})
        return json.dumps({"tool": name, "error": str(e)[:300],
                           "error_kind": e.kind}, ensure_ascii=False), 0

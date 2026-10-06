#!/usr/bin/env python3
"""validate_fee_sources.py — source-text fee-value validator (FEE_ERRATUM companion).

Round: FUTURES-OVERNIGHT-PREP-20261003 / lane P0B-FEEIMPACT. Status: DRAFT,
not a gate. Real captures come from P0A; until then only --self-test is run.

PURPOSE (closes the parent round's blind spot):
  Parent-round validators (FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees/
  validate_fees_table.py, verify/recompute_A4_fees.py) proved *internal
  arithmetic consistency* of transcribed tables against themselves. A table
  whose cells were mistranscribed (hypothesis: superscript/footnote glue,
  e.g. rendered "1.38-6" -> flattened "1.386") passes those checks by
  construction. This validator instead checks each claimed value against the
  CAPTURE SOURCE TEXT:

    located (LITERAL)         exact numeric token with clean digit/dot
                              boundaries found inside a row-label-scoped
                              window of the capture text.
    located (FOOTNOTE_GLUED)  the claimed value is NOT present as a literal
                              token, but the value-minus-its-last-digit IS,
                              immediately followed by a marker form of
                              exactly that dropped digit (unicode superscript
                              run, <sup>d</sup>, [d], ^d). This is a FAIL:
                              the full-precision value cannot be shown to
                              exist in the source; a human must adjudicate.
    NOT_LOCATED               neither of the above -> FAIL. Never a pass by
                              inference, never a pass by arithmetic.

  HARD LAW: internal arithmetic consistency is NEVER a pass condition. This
  script contains no component-sum checking at all. PASS <=> every check
  located as LITERAL in source text.

  Known limitation (documented, not solved): if the capture pipeline itself
  already destroyed superscript markers, a glued "1.386" is textually
  identical to a true "1.386". The validator reports MARKERS_ABSENT when a
  capture contains zero marker characters anywhere (capture-quality hint for
  the adjudicator); captures used with this validator must preserve markup.

Exit codes:
  0  PASS (all checks LITERAL) or self-test OK
  1  FAIL (any NOT_LOCATED) or usage/IO error
  2  FAIL_PENDING_ADJUDICATION (all located but >=1 only via footnote glue)
  3  self-test assertion failure

Usage:
  validate_fee_sources.py --self-test
  validate_fee_sources.py CAPTURE [CAPTURE ...] --expected EXPECTED.json \
      [--window 1] [--report REPORT.json]

Expected JSON schema:
  {"checks": [
     {"capture": "<basename or suffix of one CAPTURE arg>",
      "row_label": "<regex, case-insensitive, scoped to line +/- window>",
      "code": "<symbol that must appear in the window, or null>",
      "component": "<label for reporting only>",
      "value": 1.386,
      "window": 1}
  ]}
  ("window" per check overrides --window default.)
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_GLUE = 2
EXIT_SELFTEST = 3

SUPERSCRIPTS = {"0": "\u2070", "1": "\u00b9", "2": "\u00b2", "3": "\u00b3",
                "4": "\u2074", "5": "\u2075", "6": "\u2076", "7": "\u2077",
                "8": "\u2078", "9": "\u2079"}
SUPERSET = "".join(SUPERSCRIPTS.values())
ANY_MARKER_CLASS = (
    "(?:[" + re.escape(SUPERSET) + "]+|<sup>[0-9]</sup>|\\[[0-9]\\]|\\^[0-9])"
)


def canon(value) -> str:
    """Canonical decimal string for a JSON number-or-string value."""
    if isinstance(value, str):
        s = value.strip().lstrip("$").rstrip("%")
    else:
        s = f"{float(value):.6f}".rstrip("0").rstrip(".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", s):
        raise ValueError(f"unsupported value literal: {value!r}")
    return s


def token_regex(num: str) -> re.Pattern:
    """Literal token: clean boundaries so 1.38 does not match inside 21.386.
    Trailing zeros are tolerated so canonical 1.6 matches printed "1.60"."""
    return re.compile(r"(?<![\d.])" + re.escape(num) + r"0*(?![\d.])")


def marker_for(digit: str) -> str:
    return (SUPERSCRIPTS[digit] + "|" + f"<sup>{digit}</sup>|"
            + f"\\[{digit}\\]|\\^{digit}")


def capture_has_markers(text: str) -> bool:
    return bool(re.search("[" + re.escape(SUPERSET) + "]|<sup>|\\^\\d|\\[\\d\\]", text))


def check_in_capture(check: dict, capture_text: str) -> dict:
    """Run one check against one capture's text. Returns a finding dict."""
    num = canon(check["value"])
    lit = token_regex(num)
    base = num[:-1] if ("." in num and len(num.split(".", 1)[1]) >= 1) else None
    window = int(check.get("window", 1))
    label = re.compile(check["row_label"], re.IGNORECASE)
    code = check.get("code")

    lines = capture_text.splitlines()
    hits, glued_hits = [], []
    for i, line in enumerate(lines):
        lo, hi = max(0, i - window), min(len(lines), i + window + 1)
        wtext = "\n".join(lines[lo:hi])
        if not label.search(wtext):
            continue
        if code and not re.search(r"(?<![A-Za-z0-9])" + re.escape(code)
                                  + r"(?![A-Za-z0-9])", wtext, re.IGNORECASE):
            continue
        m = lit.search(wtext)
        if m:
            after = wtext[m.end():m.end() + 12]
            hits.append({"line": i + 1, "match": m.group(0),
                         "marker_adjacent": bool(
                             re.match(ANY_MARKER_CLASS, after))})
        elif base is not None and num != base and re.search(
                r"(?<![\d.])" + re.escape(base) + "(?=(?:" + marker_for(num[-1])
                + r"))", wtext):
            glued_hits.append({"line": i + 1, "base": base,
                               "dropped_digit": num[-1]})
    status = "NOT_LOCATED"
    if hits:
        status = "LITERAL"
    elif glued_hits:
        status = "FOOTNOTE_GLUED"
    return {"check": {k: check.get(k) for k in
                      ("capture", "code", "row_label", "component", "value")},
            "status": status, "literal_hits": hits,
            "glue_hits": glued_hits}


def resolve_capture(check: dict, captures: dict) -> Path:
    want = check["capture"].lower()
    for key in captures:
        if want in key.lower() or key.lower().endswith(want):
            return captures[key]
    raise FileNotFoundError(f"check references unknown capture {check['capture']!r}")


def run(capture_paths, expected_path, default_window) -> int:
    expected = json.loads(Path(expected_path).read_text(encoding="utf-8"))
    captures = {p.name: p for p in capture_paths}
    texts, quality = {}, {}
    for name, p in captures.items():
        texts[name] = p.read_text(encoding="utf-8", errors="replace")
        quality[name] = "MARKERS_PRESENT" if capture_has_markers(texts[name]) \
            else "MARKERS_ABSENT_CANNOT_DISAMBIGUATE_GLUE"
    findings, worst = [], EXIT_OK
    for check in expected["checks"]:
        check = dict(check)
        check.setdefault("window", default_window)
        f = check_in_capture(check, texts[resolve_capture(check, captures).name])
        findings.append(f)
        if f["status"] == "NOT_LOCATED":
            worst = EXIT_FAIL
        elif f["status"] == "FOOTNOTE_GLUED" and worst == EXIT_OK:
            worst = EXIT_GLUE
    for f in findings:
        c = f["check"]
        print(f"[{f['status']:14s}] {c.get('capture')} :: {c.get('code')} "
              f"{c.get('component')}={c.get('value')}  ({c.get('row_label')})")
        for h in f["literal_hits"]:
            extra = "  <-- marker adjacent to number" if h["marker_adjacent"] else ""
            print(f"                 literal line {h['line']}: {h['match']}{extra}")
        for h in f["glue_hits"]:
            print(f"                 glue   line {h['line']}: base {h['base']} "
                  f"+ marker {h['dropped_digit']}")
    for name, q in quality.items():
        print(f"[capture-quality] {name}: {q}")
    verdict = {EXIT_OK: "PASS (every value located as LITERAL in source text)",
               EXIT_GLUE: "FAIL_PENDING_ADJUDICATION (>=1 value located only "
                          "as base+footnote-marker)",
               EXIT_FAIL: "FAIL (>=1 value NOT located in source text)"}[worst]
    print(f"VERDICT: {verdict}")
    print("NOTE: internal arithmetic consistency is never a pass condition "
          "(by design; see docstring).")
    if "--report" in sys.argv:
        rp = Path(sys.argv[sys.argv.index("--report") + 1])
        rp.write_text(json.dumps({"findings": findings,
                                  "capture_quality": quality,
                                  "exit": worst}, indent=2, ensure_ascii=False)
                      + "\n", encoding="utf-8")
    return worst


SYNTHETIC_CAPTURE = """Fees Charged to Offset CME (Electronic-Globex) Exchange and Regulatory Fees Paid by IBKR
E-mini Equity Futures | BQX, ER2, NQ, QCN, RTY | 1.38\u2076 | 0.01\u00b9
E-mini S&P 500 | ES | 1.38\u2076 | 0.01\u00b9
Regulatory Fee Recovery | All Products | 0.01\u00b9
Forex Futures | EUR, GBP, JPY, AUD | 1.60 | 0.01\u00b9
"""


def self_test() -> int:
    """Assert LITERAL / FOOTNOTE_GLUED / NOT_LOCATED outcomes on an embedded
    synthetic capture. Proves: (a) the parent-round A-values (1.386/0.011)
    FAIL against a marker-preserving source; (b) base values (1.38/0.01)
    locate LITERAL with marker-adjacent flag; (c) an absent value (2.5)
    fails; (d) clean 1.60 passes with no marker flag."""
    cases = [
        ({"row_label": "E-mini Equity Futures", "code": "NQ",
          "component": "exchange", "value": 1.386}, "FOOTNOTE_GLUED"),
        ({"row_label": "E-mini S&P 500", "code": "ES",
          "component": "regulatory", "value": 0.011}, "FOOTNOTE_GLUED"),
        ({"row_label": "E-mini Equity Futures", "code": "NQ",
          "component": "exchange", "value": 1.38}, "LITERAL"),
        ({"row_label": "Regulatory Fee Recovery", "code": None,
          "component": "regulatory", "value": 0.01}, "LITERAL"),
        ({"row_label": "Forex Futures", "code": "EUR",
          "component": "exchange", "value": 1.60}, "LITERAL"),
        ({"row_label": "E-mini Equity Futures", "code": "NQ",
          "component": "exchange", "value": 2.5}, "NOT_LOCATED"),
    ]
    ok = True
    with tempfile.TemporaryDirectory() as td:
        cap = Path(td) / "CME.php.txt"
        cap.write_text(SYNTHETIC_CAPTURE, encoding="utf-8")
        for check, want in cases:
            got = check_in_capture(dict(check, capture="CME.php.txt",
                                        window=0),
                                   cap.read_text(encoding="utf-8"))
            flag = ""
            if want == "LITERAL" and got["literal_hits"]:
                adj = got["literal_hits"][0]["marker_adjacent"]
                expect_adj = check["value"] in (1.38, 0.01)
                if adj != expect_adj:
                    got["status"] = f"LITERAL(marker_adjacent={adj}, " \
                                    f"expected {expect_adj})"
            status_ok = got["status"].startswith(want)
            print(f"[self-test {'OK  ' if status_ok else 'FAIL'}] "
                  f"{check.get('code')} {check['component']}={check['value']}"
                  f" -> {got['status']} (want {want}){flag}")
            ok &= status_ok
        # marker-adjacency expectations validated inside loop above
        print(f"[capture-quality] synthetic: "
              f"{'MARKERS_PRESENT' if capture_has_markers(SYNTHETIC_CAPTURE) else 'MARKERS_ABSENT'}")
    print(f"SELF-TEST {'PASS' if ok else 'FAIL'} — glue-detector catches the "
          f"1.38+marker6 -> 1.386 transcription class; arithmetic is never "
          f"consulted.")
    return EXIT_OK if ok else EXIT_SELFTEST


def main(argv) -> int:
    if "--self-test" in argv:
        return self_test()
    args = [a for a in argv[1:] if not a.startswith("--")]
    opts = {argv[i]: argv[i + 1] for i in range(1, len(argv) - 1)
            if argv[i] in ("--expected", "--window")}
    if not args or "--expected" not in opts:
        print(__doc__)
        return EXIT_FAIL
    return run([Path(a) for a in args], Path(opts["--expected"]),
               int(opts.get("--window", "1")))


if __name__ == "__main__":
    sys.exit(main(sys.argv))

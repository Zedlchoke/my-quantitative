#!/usr/bin/env python3
"""Bounded public Deribit diagnostic. No credentials, orders, scoring or service."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode


def probe(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    requests = []
    def get(label: str, method: str, **params):
        url = 'https://www.deribit.com/api/v2/public/' + method + '?' + urlencode(params)
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        proc = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True)
        received = dt.datetime.now(dt.timezone.utc).isoformat()
        response = None
        if proc.returncode == 0:
            try:
                response = json.loads(proc.stdout)
            except json.JSONDecodeError:
                pass
        record = {'url': url, 'started_utc': started, 'received_utc': received,
                  'exit_code': proc.returncode, 'response': response,
                  'transport_error': proc.stderr[:500] if proc.returncode else None}
        raw = (json.dumps(record, indent=2) + '\n').encode()
        name = label + '.json'
        (output / name).write_bytes(raw)
        requests.append({'file': name, 'sha256': hashlib.sha256(raw).hexdigest()})
        if proc.returncode or not isinstance(response, dict) or 'error' in response or 'result' not in response:
            raise RuntimeError(f'Public API unavailable or malformed: {label}; see {name}')
        return response['result']

    report = {'mode': 'PUBLIC_DATA_PROBE_ONLY', 'strategy_edge': 'NOT_RUN',
              'real_time_streaming': 'NOT_RUN', 'historical_executable_quotes': 'NOT_RUN',
              'paper_execution': 'NOT_RUN', 'capital_usd': 1000}
    try:
        instruments = get('instruments', 'get_instruments', currency='ETH', kind='option', expired='false')
        if not isinstance(instruments, list):
            raise RuntimeError('Instrument response is not a list')
        now = int(time.time() * 1000)
        candidates = [i for i in instruments if i.get('is_active') and i.get('option_type') == 'put'
                      and now + 7 * 86400000 < i.get('expiration_timestamp', 0) < now + 45 * 86400000]
        if not candidates:
            raise RuntimeError('No active ETH put in the diagnostic 7-45 day window')
        report['instrument_count'] = len(instruments)
        # Deterministic sample for API inspection only, never a trade recommendation.
        candidate = sorted(candidates, key=lambda i: (i['expiration_timestamp'], i['strike'], i['instrument_name']))[0]
        instrument = candidate['instrument_name']
        report['sample_contract'] = {k: candidate.get(k) for k in
            ['instrument_name', 'min_trade_amount', 'contract_size', 'settlement_currency', 'quote_currency']}
        book = get('orderbook', 'get_order_book', instrument_name=instrument, depth=5)
        if not isinstance(book, dict):
            raise RuntimeError('Order book response is not an object')
        report['book_sample'] = {k: book.get(k) for k in
            ['timestamp', 'best_bid_price', 'best_ask_price', 'index_price']}
        bid, ask = book.get('best_bid_price'), book.get('best_ask_price')
        report['two_sided_book'] = bool(isinstance(bid, (int, float)) and isinstance(ask, (int, float)) and 0 < bid <= ask)
        for label, name, days in [('option_history', instrument, 7), ('underlying_history', 'ETH-PERPETUAL', 30)]:
            data = get(label, 'get_tradingview_chart_data', instrument_name=name,
                       start_timestamp=now - days * 86400000, end_timestamp=now, resolution='60')
            if not isinstance(data, dict):
                raise RuntimeError(f'History response is not an object: {label}')
            ticks = data.get('ticks', [])
            if not isinstance(ticks, list):
                raise RuntimeError(f'Invalid timestamps: {label}')
            report[label + '_bars'] = len(ticks)
            report[label + '_fully_elapsed_hour_bars'] = sum(t + 3600000 <= now for t in ticks)
        report['verdict'] = 'DATA_SAMPLE_RECEIVED'
    except (RuntimeError, OSError) as exc:
        report.update(verdict='BLOCKED_DATA_PROBE', reason=str(exc))
    report['limitations'] = [
        'One REST sample does not verify WebSocket continuity or quote freshness.',
        'Candles may include no-trade/filled intervals; elapsed counts are not data-quality approval.',
        'Trade OHLCV and mark prices cannot establish historical option fills.',
        'Contract sample is deterministic, not a selected trading signal.',
        'No fees, eligibility, margin, risk limits or sustainable strategy have been established.'
    ]
    report['raw_files'] = requests
    (output / 'SUMMARY.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='New directory outside the repository for public raw responses')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    output = args.output_dir.expanduser().resolve()
    if output == repo or repo in output.parents:
        parser.error('Keep raw data outside the repository')
    try:
        report = probe(output)
    except FileExistsError:
        parser.error('Output directory already exists; choose a fresh directory')
    print(json.dumps(report, indent=2))
    return 0 if report['verdict'] == 'DATA_SAMPLE_RECEIVED' else 2

if __name__ == '__main__':
    raise SystemExit(main())

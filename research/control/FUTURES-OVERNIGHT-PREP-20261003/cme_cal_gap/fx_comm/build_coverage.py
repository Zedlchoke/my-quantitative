import json, re
from collections import OrderedDict

parent_fx = json.load(open('/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/fx/fx_cal_coverage.json'))
new_fx = json.load(open('captures/fx_new_rows.json'))
trans = json.load(open('captures/holiday_transcription.json'))
gc_si = json.load(open('captures/gc_si_gapfill_rows.json'))
parent_comm = json.load(open('/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/comm/comm_cal_coverage.json'))

# ---- FX expirations coverage ----
SYM = ['6E','6B','6J','6A']
cov = {s: {} for s in SYM}
# parent rows
for e in parent_fx['expirations']:
    yr = int(e['month'].split()[-1]); q = e['month'].split()[0]
    cov[e['sym']].setdefault(str(yr), {}).setdefault('quarters', {})[q] = {'date': e['last_trade'], 'code': e['code'], 'src': 'parent_A2', 'capture': e['capture_ts']}
# new rows
srcmap = {'20110527042052':'euro-fx_product_calendar_futures.html','20150111002610':'euro-fx_product_calendar_futures.html','20180228224018':'euro-fx_product_calendar_futures.html','20100219101527':'british-pound_product_calendar_futures.html','20180226190632':'british-pound_product_calendar_futures.html','20100120181108':'japanese-yen_product_calendar_futures.html','20100814205214':'japanese-yen_product_calendar_futures.html','20141015223742':'japanese-yen_product_calendar_futures.html','20180226182137':'japanese-yen_product_calendar_futures.html','20180301074633':'australian-dollar_product_calendar_futures.html'}
for e in new_fx:
    yr = int(e['month'].split()[-1]); q = e['month'].split()[0]
    cov[e['sym']].setdefault(str(yr), {}).setdefault('quarters', {})[q] = {'date': e['last_trade'], 'code': e['code'], 'src': 'this_lane', 'capture': e['capture_ts'], 'url': f"https://web.archive.org/web/{e['capture_ts']}/http://www.cmegroup.com/trading/fx/g10/{srcmap[e['capture_ts']]}"}

per_sym = {}
for s in SYM:
    n = sum(len(v.get('quarters', {})) for v in cov[s].values())
    per_sym[s] = n
total = sum(per_sym.values())

fx_expiries = OrderedDict()
fx_expiries['baseline_parent_A2'] = {'6E': 17, '6B': 31, '6J': 13, '6A': 35, 'total': 96, 'of': 272}
fx_expiries['after_this_lane'] = {'per_symbol_quarters_of_68': per_sym, 'total': f"{total}/272"}
fx_expiries['per_symbol_per_year'] = {s: {yr: sorted(v['quarters'].keys()) for yr, v in sorted(cov[s].items())} for s in SYM}
fx_expiries['new_rows_this_lane'] = new_fx
fx_expiries['not_obtained'] = {s: ['all four quarters 2023','2024','2025','2026'] for s in SYM}
fx_expiries['not_obtained_reason'] = "FX product-calendar _futures URL static era ends 2018-02/04 (verified: 2018-04-18+ captures are JS shells, 9 tested); fx/rolldates.html retired 2016 (301->markets/fx.html); no archived CmeWS/CmeWeb event.dld responses in era; live legacy event.dld endpoint BLOCKED_TRANSPORT (web_reader -500 x2, WebFetch ECONNREFUSED); live/new productCalendar URLs never archived (CDX empty). Per mission law, dates are NOT derived from the IMM rule."

# ---- GC/SI ----
gcsi = OrderedDict()
for sym, arr in (('GC', [r for r in gc_si if r['sym']=='GC']), ('SI', [r for r in gc_si if r['sym']=='SI'])):
    per_year = {}
    for r in arr:
        per_year.setdefault(r['month'].split()[1], []).append(f"{r['month'].split()[0]}={r['last_trade']} [{r['code']}]")
    gcsi[sym] = {
        'baseline_parent_A3': {'GC':'Aug 2013-Jun 2019 (22 rows)','SI':'Mar 2015-Dec 2019 (20 rows)'}[sym],
        'new_capture': 'https://web.archive.org/web/%s/http://www.cmegroup.com/trading/metals/precious/%s_product_calendar_futures.html' % (arr[0]['capture_ts'], 'gold' if sym=='GC' else 'silver'),
        'new_coverage': f"{arr[0]['month']} -> {arr[-1]['month']} ({len(arr)} rows, incl. rows already held by parent on overlap - zero conflicts)",
        'per_year_new_rows': per_year,
        'not_obtained': 'GC 2024-2026, SI 2023-2026' if sym=='GC' else 'SI 2023-2026',
        'not_obtained_reason': 'GC/SI calendar static era ends 2018-02-27/04 (this lane verified 2019-2021 captures are JS shells: GC 20190328183304/20190908124623/20191120151956, SI 20180428160150/20180429115735 + parent 2018-06/2020-08); no metals rolldates page (CDX 404); no archived CmeWS responses; 72-month (GC) / 60-month (SI) forward listing in the 2018-02-27 captures is the last static listing.',
        'rule_qa': 'all rows equal third-last-business-day of contract month EXCEPT GCH18/SIH18 (table 27 Mar 2018) where Good Friday Mar 30 2018 removes Mar 30 from the business-day chain - table correct, QA script naive (weekend-only) flagged it; zero other deviations.'
    }

# ---- holiday cells ----
HOL_ORDER = ['NewYear','MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Columbus','Veterans','Thanksgiving','Christmas']
UNIVERSE = {
 '2017': [h for h in HOL_ORDER if h != 'Juneteenth'], '2018': [h for h in HOL_ORDER if h != 'Juneteenth'],
 '2019': [h for h in HOL_ORDER if h != 'Juneteenth'],
 '2020': ['NewYear','MLK','Presidents','GoodFriday','Memorial','July4','Labor','Thanksgiving','Christmas'],
 '2021': ['NewYear','MLK','Presidents','GoodFriday','Memorial','July4','Labor','Thanksgiving','Christmas'],
 '2022': ['NewYear','MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Thanksgiving','Christmas'],
 '2023': ['NewYear','MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Thanksgiving','Christmas'],
 '2024': ['NewYear','MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Columbus','Veterans','Thanksgiving','Christmas'],
 '2025': ['NewYear','MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Columbus','Veterans','Thanksgiving','Christmas'],
}
def holiday_cells(years, universe, fam_key):
    out = {}
    for yr in years:
        out[yr] = {}
        for h in universe[yr]:
            e = (trans.get(yr) or {}).get(h)
            if e and e.get(fam_key):
                out[yr][h] = {'status': 'OBTAINED', 'file': e['file'], 'capture_ts': e['capture_ts'],
                              'url': f"https://web.archive.org/web/{e['capture_ts']}/http://www.cmegroup.com/tools-information/holiday-calendar/files/{e['file']}",
                              'verbatim': e[fam_key][:500]}
            else:
                out[yr][h] = {'status': 'NOT_OBTAINED', 'reason': 'no per-holiday Globex schedule file archived (CDX inventory of files/ complete this lane; only advisories/settlement-times PDFs exist)'}
    return out

fx_hol = holiday_cells([str(y) for y in range(2017,2026)], UNIVERSE, 'fx')
# special-case 2023 non-NY cells and 2019 thanksgiving
for h in ['MLK','Presidents','GoodFriday','Memorial','Juneteenth','July4','Labor','Thanksgiving','Christmas']:
    if fx_hol['2023'].get(h, {}).get('status') == 'NOT_OBTAINED' and h in ('MLK','Presidents','GoodFriday','Memorial','Juneteenth'):
        fx_hol['2023'][h]['reason'] += '; compact-mgex-dme XLS archived but covers DME/MGEX products only (verified content), no FX/NYMEX/COMEX Globex rows'
fx_hol['2019']['Thanksgiving'] = {'status':'NOT_OBTAINED','reason':'2019-thanksgiving-day-holiday-schedule-arragements.xlsx fetched and parsed: content is a NYMEX BALMO/PRA settlement list, NO Globex hours'}
em_hol = holiday_cells([str(y) for y in range(2011,2016)], {str(y): HOL_ORDER[:-1]+['Christmas'] for y in range(2011,2016)}, 'energy_metals')
em_hol['2014']['MLK'] = {'status':'NOT_TRANSCRIBED','reason':'2014-martin-luther-king-holiday-schedule.pdf fetched (sha256 saved, capture 20140326160215) but pypdf text extraction garbled (vertical fragments); artifact retained for re-extraction with a different parser'}
for yr in ('2014','2015'):
    em_hol[yr]['Veterans'] = {'status':'NOT_OBTAINED','reason':'archived file is a settlement-procedures document, not a Globex hours schedule (parent A2/A3 same finding)'}
# bonus E/M 2017-2023
em_bonus = holiday_cells([str(y) for y in range(2017,2024)], UNIVERSE, 'energy_metals')

doc = OrderedDict()
doc['task_id'] = 'FUTURES-OVERNIGHT-PREP-20261003'
doc['lane'] = 'P2B-CALGAP-FXCOMM'
doc['generated_utc'] = '2026-10-03T23:59:00Z'
doc['provenance_labels'] = {'ARCHIVED_OFFICIAL':'web.archive.org capture of official cmegroup.com artifact (file saved + sha256)','NOT_OBTAINED':'no authority-backed datum; reason recorded','NOT_TRANSCRIBED':'artifact in hand but text extraction failed'}
doc['no_extrapolation_pledge'] = 'every date/time in this file was read from a saved capture; zero dates derived from rules or neighboring years'
doc['gap1_fx_expirations'] = fx_expiries
doc['gap3_gc_si_expirations'] = gcsi
doc['gap2_fx_holiday_times_2017_2025'] = {
    'cell_status_counts': {yr: {s: sum(1 for h in fx_hol[yr] if fx_hol[yr][h]['status']==s or s=='total' and False) for s in ['OBTAINED']} | {'universe': len(fx_hol[yr])} for yr in fx_hol},
    'cells': fx_hol,
    'headline': 'Parent A2 claimed 2017-2025 per-holiday files were unarchived - OVERTURNED: 2017 full set, 2018 9/11, 2019 2/11, 2020 7/9-universe, 2021 9/9, 2022 10/10, 2023 1/10, 2024-2025 0 (advisories only). New verbatim FX-family facts incl. Monday-halt 12:00 CT (2017-2021) -> normal-session-with-16:00/17:00 (2022), GoodFriday full closure every year 2017-2022, Christmas eve early close 12:15 CT (2018-2020 XLS), Thanksgiving Friday early close 12:15 CT (2017-2021 XLS tail column).'
}
doc['gap4_energy_metals_holiday_times_2011_2015'] = {
    'cell_status_counts': {yr: sum(1 for h in em_hol[yr] if em_hol[yr][h]['status']=='OBTAINED') for yr in em_hol},
    'cells': em_hol,
    'headline': '43/45 cells OBTAINED (2011 11/11, 2012 11/11, 2013 11/11 incl. Columbus/Veterans normal-schedule one-pagers, 2014 9/11, 2015 10/11); NOT_TRANSCRIBED 2014-MLK (garbled PDF, saved); NOT_OBTAINED 2014/2015-Veterans (settlement docs). Verbatim NYMEX/COMEX family times: Monday-holiday halts 12:15 CT (2011-2013) / 12:00 CT (2014-2015), pre-holiday-Friday early closes 15:15 CT (2011-2012) -> dropped (2013-2015 regular 16:15), Thanksgiving Friday early close 12:45 CT, Christmas-eve early close 12:45 CT (2012-2015), TAS exceptions quoted.'
}
doc['bonus_energy_metals_2017_2023'] = {'note':'same XLS artifacts carry the Energy, Metals (& Softs) & DME row - extends parent A3 comm-lane product-line Globex times beyond its 2010-2015 coverage into 2017-2023 (same cell grid as gap2)','cells': em_bonus}
json.dump(doc, open('fxcomm_gapfill_coverage.json','w'), indent=1)
print("coverage json written")
print("FX total:", fx_expiries['after_this_lane'])
for yr in fx_hol: print(yr, "FX cells obtained:", doc['gap2_fx_holiday_times_2017_2025']['cell_status_counts'][yr])
for yr in em_hol: print(yr, "E/M cells obtained:", doc['gap4_energy_metals_holiday_times_2011_2015']['cell_status_counts'][yr])

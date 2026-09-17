//+------------------------------------------------------------------+
//|                                          mt5_cost_collector.mq5 |
//|  READ-ONLY cost collector for my-quantitative probe              |
//|  forex_mt5_cost_probe_2026-09 (account OANDA_Global-Demo-1).     |
//|                                                                  |
//|  CONTRACT (probe_contract.json @1):                              |
//|   - This program calls ZERO order/trade functions. It never      |
//|     places, modifies, closes or cancels anything. It only        |
//|     READS symbol/account/terminal state and writes CSV files     |
//|     into the terminal's shared Files folder.                     |
//|   - ACCOUNT_LOGIN is banned by contract and never read.          |
//|   - Keep the Algo Trading (AutoTrading) button OFF. This EA      |
//|     does not need it and cannot trade without it; it also        |
//|     records the TERMINAL_TRADE_ALLOWED flag every heartbeat      |
//|     so the raw data itself proves trading stayed disabled.       |
//+------------------------------------------------------------------+
#property copyright "my-quantitative research"
#property link      "https://github.com/Zedlchoke/my-quantitative"
#property version   "1.00"
#property description "READ-ONLY MT5 cost collector (spread/spec/swap/sessions). No trade API anywhere."

input int    InpSampleSeconds    = 5;    // spread sample cadence (seconds)
input int    InpHeartbeatSeconds = 60;   // heartbeat cadence (seconds)
input int    InpSpecEveryHours   = 4;    // refresh static spec snapshot every N hours
input string InpSymbols          = "EURUSD,GBPUSD,AUDUSD,NZDUSD,USDCAD";

string   g_symbols[];
int      g_nsym = 0;
datetime g_lastSample = 0;
datetime g_lastBeat   = 0;
datetime g_lastSpec   = 0;
long     g_rowsTotal  = 0;
long     g_fileErrors = 0;
long     g_tickErrors = 0;
bool     g_gapOpen    = false;   // one-shot gap events (F-06)
string   g_lastKey[];      // last emitted row per symbol (in-run duplicate guard)

//+------------------------------------------------------------------+
// Helpers: time + enums
//+------------------------------------------------------------------+
string UtcIso(const datetime gmt)
{
   string s = TimeToString(gmt, TIME_DATE|TIME_SECONDS);
   StringReplace(s, ".", "-");
   StringReplace(s, " ", "T");
   return s + "Z"; // TimeGMT() already yields UTC
}

string TradeModeText(const long mode)
{
   if(mode == ACCOUNT_TRADE_MODE_DEMO)    return "DEMO";
   if(mode == ACCOUNT_TRADE_MODE_CONTEST) return "CONTEST";
   if(mode == ACCOUNT_TRADE_MODE_REAL)    return "REAL";
   return "UNKNOWN";
}

string SwapModeText(const long mode)
{
   // Numeric mapping on purpose: this build's SDK does not declare every
   // SYMBOL_SWAP_MODE_* named constant (owner-measured 'undeclared
   // identifier' compile errors on build 6180, A7 F-01/F-02). The enum's
   // numeric values are ABI-fixed; the RAW number is also written to each
   // spec snapshot row so the verifier/A7 can re-map independently.
   switch((int)mode)
   {
      case 0: return "DISABLED";
      case 1: return "POINTS";
      case 2: return "SYMBOL_CURRENCY";
      case 3: return "CURRENCY";
      case 4: return "MARGIN_CURRENT";
      case 5: return "CURRENCY_DEPOSIT";
      case 6: return "INTEREST_CURRENT";
      case 7: return "INTEREST_OPEN";
      case 8: return "REOPEN_CURRENT";
      case 9: return "REOPEN_FIXED";
   }
   return "UNKNOWN";
}

string DayText(const long day)
{
   if(day == 0) return "SUNDAY";
   if(day == 1) return "MONDAY";
   if(day == 2) return "TUESDAY";
   if(day == 3) return "WEDNESDAY";
   if(day == 4) return "THURSDAY";
   if(day == 5) return "FRIDAY";
   if(day == 6) return "SATURDAY";
   return "UNKNOWN";
}

double PipSize(const string sym)
{
   long   digits = SymbolInfoInteger(sym, SYMBOL_DIGITS);
   double point  = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(digits == 3 || digits == 5) return point * 10.0;
   return point;
}

//+------------------------------------------------------------------+
// Append-only writer: reopen-by-path on every write so a replaced
// file under us can never orphan a handle (Q-13 inode hygiene).
//+------------------------------------------------------------------+
bool AppendLine(const string filename, const string line)
{
   int h = FileOpen("forex_mt5_cost_probe\\" + filename,
                    FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_SHARE_READ|FILE_COMMON);
   if(h == INVALID_HANDLE)
   {
      g_fileErrors++;
      Print("cost-collector: file open FAILED for ", filename, " err=", GetLastError());
      return false;
   }
   FileSeek(h, 0, SEEK_END);
   FileWriteString(h, line + "\n");
   FileClose(h);
   return true;
}

string AccountContext()
{
   // ACCOUNT_LOGIN is BANNED by probe contract - never read, never stored.
   return "\"" + AccountInfoString(ACCOUNT_COMPANY) + "\"" +
          ",\"" + AccountInfoString(ACCOUNT_SERVER) + "\"" +
          "," + TradeModeText(AccountInfoInteger(ACCOUNT_TRADE_MODE)) +
          ",\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\"" +
          ",REDACTED_LOGIN_BY_CONTRACT" +
          "," + IntegerToString(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) +
          "," + IntegerToString(TerminalInfoInteger(TERMINAL_CONNECTED));
}

//+------------------------------------------------------------------+
// Static spec snapshot for one symbol (kind = startup/periodic/shutdown)
//+------------------------------------------------------------------+
void WriteSpecRow(const string sym, const string kind)
{
   string sessions = "";
   for(int day = 0; day < 7; day++)
   {
      for(int idx = 0; idx < 8; idx++)
      {
         datetime from = 0, to = 0;
         if(!SymbolInfoSessionTrade(sym, (ENUM_DAY_OF_WEEK)day, (uint)idx, from, to))
            break;
         long fsec = (long)from % 86400;
         long tsec = (long)to   % 86400;
         if(tsec == 0 && (long)to > 0) tsec = 86400;   // midnight end renders 24:00 (A7 F-13)
         string fs = StringFormat("%02d:%02d", (int)(fsec/3600), (int)((fsec%3600)/60));
         string ts = StringFormat("%02d:%02d", (int)(tsec/3600), (int)((tsec%3600)/60));
         if(sessions != "") sessions += ";";
         sessions += DayText(day) + "=" + fs + "-" + ts;
      }
   }
   long swapMode = SymbolInfoInteger(sym, SYMBOL_SWAP_MODE);
   string line = UtcIso(TimeGMT()) + "," + kind + "," + sym +
      "," + IntegerToString(SymbolInfoInteger(sym, SYMBOL_DIGITS)) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_POINT), 8) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE), 8) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE), 8) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE), 2) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN), 2) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX), 2) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP), 2) +
      "," + IntegerToString(SymbolInfoInteger(sym, SYMBOL_SPREAD)) +
      "," + SwapModeText(swapMode) +
      "," + IntegerToString(swapMode) +
      "," + TradeModeText(SymbolInfoInteger(sym, SYMBOL_TRADE_MODE)) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_LONG), 4) +
      "," + DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT), 4) +
      "," + DayText(SymbolInfoInteger(sym, SYMBOL_SWAP_ROLLOVER3DAYS)) +
      ",\"" + sessions + "\"" +
      "," + AccountContext();
   AppendLine("spec_snapshot.csv", line);
}

void WriteAllSpecs(const string kind)
{
   for(int i = 0; i < g_nsym; i++) WriteSpecRow(g_symbols[i], kind);
}

//+------------------------------------------------------------------+
// Tick sample for one symbol
//+------------------------------------------------------------------+
void SampleSymbol(const int idx, const datetime nowGmt)
{
   string sym = g_symbols[idx];
   MqlTick tick;
   if(!SymbolInfoTick(sym, tick))
   {
      g_tickErrors++;
      return;
   }
   // in-run duplicate guard: same (symbol, time_msc, bid, ask) is skipped
   string key = sym + "|" + IntegerToString(tick.time_msc) +
                "|" + DoubleToString(tick.bid, 8) +
                "|" + DoubleToString(tick.ask, 8);
   if(g_lastKey[idx] == key) return;
   g_lastKey[idx] = key;

   long   digits  = SymbolInfoInteger(sym, SYMBOL_DIGITS);
   double point   = SymbolInfoDouble(sym, SYMBOL_POINT);
   double pip     = PipSize(sym);
   if(point <= 0 || pip <= 0)   // A7 F-07: never divide by a degenerate point
   {
      g_tickErrors++;
      return;
   }
   long   spreadP = SymbolInfoInteger(sym, SYMBOL_SPREAD);
   double spreadC = (tick.ask - tick.bid) / point;

   string line = UtcIso(nowGmt) + "," + sym +
      "," + DoubleToString(tick.bid, (int)digits) +
      "," + DoubleToString(tick.ask, (int)digits) +
      "," + IntegerToString(spreadP) +
      "," + DoubleToString(spreadC, 1) +
      "," + DoubleToString((tick.ask - tick.bid) / pip, 2) +
      "," + IntegerToString(digits) +
      "," + IntegerToString(tick.time_msc) +
      "," + UtcIso(tick.time) +
      "," + AccountContext();
   if(AppendLine("tick_samples.csv", line)) g_rowsTotal++;
}

//+------------------------------------------------------------------+
// Heartbeat
//+------------------------------------------------------------------+
void WriteHeartbeat()
{
   int ok = 0;
   for(int i = 0; i < g_nsym; i++)
      if((long)SymbolInfoInteger(g_symbols[i], SYMBOL_TIME) > 0) ok++;
   string line = UtcIso(TimeGMT()) +
      "," + IntegerToString(TerminalInfoInteger(TERMINAL_CONNECTED)) +
      "," + IntegerToString(ok) +
      "," + IntegerToString(g_nsym - ok) +
      "," + IntegerToString(g_rowsTotal) +
      "," + IntegerToString(g_fileErrors) +
      "," + IntegerToString(g_tickErrors) +
      "," + AccountContext();
   AppendLine("heartbeat.csv", line);
}

//+------------------------------------------------------------------+
// Event row (startup / gap / shutdown)
//+------------------------------------------------------------------+
void WriteEvent(const string kind, const string detail)
{
   string line = UtcIso(TimeGMT()) + "," + kind + ",\"" + detail + "\"," + AccountContext();
   AppendLine("events.csv", line);
}

//+------------------------------------------------------------------+
int OnInit()
{
   g_nsym = StringSplit(InpSymbols, ',', g_symbols);
   if(g_nsym <= 0)
   {
      Print("cost-collector: no symbols configured");
      return INIT_FAILED;
   }
   ArrayResize(g_lastKey, g_nsym);
   for(int i = 0; i < g_nsym; i++)
   {
      StringTrimLeft(g_symbols[i]);
      StringTrimRight(g_symbols[i]);
      g_lastKey[i] = "";
      if(!SymbolSelect(g_symbols[i], true))
         Print("cost-collector: WARN symbol not available: ", g_symbols[i]);
   }

   WriteEvent("startup",
      "probe=forex_mt5_cost_probe_2026-09;schema=mt5_cost_collector@1" +
      ";sample_seconds=" + IntegerToString(InpSampleSeconds) +
      ";heartbeat_seconds=" + IntegerToString(InpHeartbeatSeconds) +
      ";trade_functions_used=NONE (read-only by contract)" +
      ";algo_trading_button_must_stay_off=true");
   WriteAllSpecs("startup_snapshot");

   EventSetTimer(MathMax(1, InpSampleSeconds));
   Print("cost-collector: started READ-ONLY. Data -> MT5 menu 'File > Open Shared Folder' -> forex_mt5_cost_probe\\");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteAllSpecs("shutdown_snapshot");
   WriteEvent("shutdown",
      "reason=" + IntegerToString(reason) +
      ";rows=" + IntegerToString(g_rowsTotal) +
      ";file_errors=" + IntegerToString(g_fileErrors) +
      ";tick_errors=" + IntegerToString(g_tickErrors));
}

void OnTimer()
{
   datetime nowGmt = TimeGMT();

   if(nowGmt - g_lastBeat >= InpHeartbeatSeconds)
   {
      WriteHeartbeat();
      g_lastBeat = nowGmt;
   }
   if(nowGmt - g_lastSpec >= (datetime)(InpSpecEveryHours * 3600))
   {
      WriteAllSpecs("periodic_snapshot");
      g_lastSpec = nowGmt;
   }
   if(nowGmt - g_lastSample < InpSampleSeconds) return;
   g_lastSample = nowGmt;

   if(TerminalInfoInteger(TERMINAL_CONNECTED) == 0)
   {
      if(!g_gapOpen)   // A7 F-06: one gap event per disconnect episode, not one per timer tick
      {
         WriteEvent("gap", "terminal disconnected - samples intentionally absent (missing=missing)");
         g_gapOpen = true;
      }
      return;
   }
   if(g_gapOpen)
   {
      WriteEvent("reconnect", "terminal reconnected - sampling resumes");
      g_gapOpen = false;
   }
   for(int i = 0; i < g_nsym; i++)
      SampleSymbol(i, nowGmt);
}
//+------------------------------------------------------------------+
// READ-ONLY ATTESTATION: this file contains no OrderSend, OrderClose,
// OrderCloseBy, OrderDelete, OrderModify, PositionOpen, PositionClose,
// PositionModify, PositionCloseBy, Buy, Sell, CTrade, or OrderCalc*
// calls. Verified by static_audit_result.json (grep) and by the
// independent A7 pre-deployment audit before deployment.
//+------------------------------------------------------------------+

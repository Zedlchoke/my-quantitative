#!/bin/zsh
# fetch.sh <name> <url> — small text fetch with HTTP status + UTC timestamp log
set -u
NAME="$1"; URL="$2"
DIR="$(cd "$(dirname "$0")" && pwd)/fetches"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
OUT="$DIR/$NAME"
CODE=$(curl -sSL --max-time 45 -o "$OUT" -w "%{http_code}" "$URL" 2>"$DIR/$NAME.curl_err")
SIZE=$(wc -c < "$OUT" | tr -d ' ')
printf "%s | %s | %s | HTTP %s | %s bytes\n" "$TS" "$NAME" "$URL" "$CODE" "$SIZE" >> "$(dirname "$0")/fetch_log.txt"
echo "$TS | $NAME | $URL | HTTP $CODE | $SIZE bytes"

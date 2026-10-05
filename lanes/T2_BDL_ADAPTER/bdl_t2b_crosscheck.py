"""T2b — OBSOLETE. Superseded by bdl_t2c_crosscheck.py.

This script contained a parameter syntax error (scalar `seasons=YYYY` instead
of array `seasons[]=YYYY`) that caused all /games requests to return HTTP 400,
leading to incorrect conclusions (later retracted). It is kept as historical
evidence only and BLOCKED from execution. Use bdl_t2c_crosscheck.py instead,
which uses the correct `dates[]=` array syntax and was verified 5/5 MATCH.

Run: python bdl_t2c_crosscheck.py   (NOT this file)
"""
import sys

print("OBSOLETE: This script is superseded by bdl_t2c_crosscheck.py.", file=sys.stderr)
print("The scalar `seasons=` syntax used here caused HTTP 400 errors.", file=sys.stderr)
print("Use: python bdl_t2c_crosscheck.py  (dates[] array syntax, 5/5 verified)", file=sys.stderr)
sys.exit(9)

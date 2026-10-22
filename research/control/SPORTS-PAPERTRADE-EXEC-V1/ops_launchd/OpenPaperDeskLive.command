#!/bin/zsh
# Open the LIVE paper desk for SPORTS-PAPERTRADE-EXEC-V1 (local only).
# The supervisor (launchd com.myquant.sptexec.ops) must be running; it serves
# 127.0.0.1:8791 only. If it is not running, start it via:
#   launchctl kickstart -k gui/$(id -u)/com.myquant.sptexec.ops
open "http://127.0.0.1:8791/"

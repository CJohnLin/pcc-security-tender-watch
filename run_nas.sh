#!/bin/sh
# Synology DSM「工作排程器」用的啟動腳本（見 docs/adr/0005）。
# 放在 NAS 的 ~/pcc/，跟 venv/、credentials.json、token.json 同一層。
cd "$(dirname "$0")" || exit 1

export UNATTENDED=1
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

mkdir -p logs
./venv/bin/python run.py >> "logs/run_$(date +%Y%m%d).log" 2>&1
status=$?

# 只留最近 30 天的 log 與輸出的 HTML，避免無限增長。
find logs -name 'run_*.log' -mtime +30 -delete 2>/dev/null
find output -name 'tenders_*.html' -mtime +30 -delete 2>/dev/null

exit $status

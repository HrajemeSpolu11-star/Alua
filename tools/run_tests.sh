#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
python -m compileall -q src tests tools
python -m unittest discover -s tests -v
python tools/audit_repo.py

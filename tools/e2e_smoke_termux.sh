#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

repo_dir="${ALUA_REPO_DIR:-$HOME/alua/Alua}"
cd "$repo_dir"

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

python_bin="${ALUA_PYTHON:-$repo_dir/.venv/bin/python}"
if [ ! -x "$python_bin" ]; then
  python_bin="${ALUA_PYTHON_FALLBACK:-python}"
fi

cycles="${ALUA_E2E_CYCLES:-8}"
sleep_seconds="${ALUA_E2E_SLEEP:-0.6}"

echo "[1/3] Kontrola Bridge + aktivní World session"
"$python_bin" -m alua doctor

echo "[2/3] Provádím $cycles kognitivních cyklů"
i=1
while [ "$i" -le "$cycles" ]; do
  "$python_bin" -m alua run --once
  sleep "$sleep_seconds"
  i=$((i + 1))
done

echo "[3/3] Ověřuji, že proběhl celý vjem -> akce -> následek -> učení"
status_json="$("$python_bin" -m alua status)"
printf '%s\n' "$status_json"

ALUA_E2E_STATUS="$status_json" "$python_bin" - <<'PY'
import json
import os
import sys

state = json.loads(os.environ["ALUA_E2E_STATUS"])
checks = {
    "active session": bool(state.get("session_id")),
    "at least one observation episode": int(state.get("episodes", 0)) >= 1,
    "at least one decision": int(state.get("decisions", 0)) >= 1,
    "at least one learned belief": int(state.get("beliefs", 0)) >= 1,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    print("E2E FAILED: " + ", ".join(failed), file=sys.stderr)
    raise SystemExit(1)
print("E2E OK: World -> Bridge -> Alua -> Bridge -> World -> sensory outcome -> belief")
PY

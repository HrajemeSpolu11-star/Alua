from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "alua"

FORBIDDEN_IMPORT_MARKERS = (
    "minetest",
    "luanti",
    "aw_agents",
    "aw_materials",
    "aw_world_senses",
    "ALUABRIDGE_WORLD_TOKEN",
)

NETWORK_IMPORTS = re.compile(
    r"^\s*(?:"
    r"from\s+(?:urllib\.(?:request|error)|http\.client|socket)\s+import\b|"
    r"import\s+(?:urllib\.(?:request|error)|http\.client|socket|requests|aiohttp)\b|"
    r"from\s+(?:requests|aiohttp)\s+import\b"
    r")",
    re.MULTILINE,
)


def main() -> int:
    failures: list[str] = []
    for path in sorted(SOURCE.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for marker in FORBIDDEN_IMPORT_MARKERS:
            if marker in source:
                failures.append(f"{rel}: zakázaná přímá vazba {marker}")
        if path.name != "bridge_client.py" and NETWORK_IMPORTS.search(source):
            failures.append(f"{rel}: síťový import je povolen pouze v bridge_client.py")
        if "subprocess" in source or "os.system" in source:
            failures.append(f"{rel}: kognitivní runtime nesmí spouštět shell")

    if failures:
        print("AUDIT FAILED")
        for failure in failures:
            print("-", failure)
        return 1
    print("AUDIT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

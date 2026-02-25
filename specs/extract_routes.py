# extract_routes.py - Extract React Router routes from App.tsx
import json
import re
from pathlib import Path

# Resolve paths: run from repo root or from specs/
ROOT = Path(__file__).resolve().parent.parent
APP_TSX = ROOT / "frontend" / "src" / "App.tsx"
OUTPUT_JSON = ROOT / "frontend" / "route-table.json"


def extract_routes(file_path: Path) -> list[dict]:
    content = file_path.read_text(encoding="utf-8")
    routes = []

    # Match <Route path="..." element={<ComponentName />} /> (single-line)
    for m in re.finditer(
        r'<Route\s+path=["\']([^"\']+)["\']\s+element=\{\s*<(\w+)\s*/>\s*\}\s*/>',
        content,
    ):
        routes.append({"path": m.group(1), "component": m.group(2)})

    # Match <Route path="..." ... /> with element on same line: element={<Name />}
    for m in re.finditer(
        r'<Route\s+path=["\']([^"\']+)["\'][^>]*element=\{\s*<(\w+)\s*/>',
        content,
    ):
        path, comp = m.group(1), m.group(2)
        if not any(r["path"] == path for r in routes):
            routes.append({"path": path, "component": comp})

    # Match index redirect: <Route index element={<Navigate ...
    if re.search(r'<Route\s+index\s+element=\{\s*<Navigate', content):
        if not any(r["path"] == "/" and r["component"] == "index" for r in routes):
            routes.append({"path": "/ (index)", "component": "Navigate"})

    # Sort by path for stable output
    routes.sort(key=lambda x: (x["path"].count("/"), x["path"]))
    return routes


if __name__ == "__main__":
    if not APP_TSX.exists():
        print(f"App.tsx not found: {APP_TSX}")
        exit(1)

    routes = extract_routes(APP_TSX)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(routes, indent=2), encoding="utf-8")
    print(f"Wrote {len(routes)} routes to {OUTPUT_JSON}")
    for r in routes:
        print(f"  {r['path']} -> {r['component']}")

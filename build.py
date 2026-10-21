#!/usr/bin/env python3
"""Build the Surface app from ../website/catalog.json.

Reads the same catalog the public website is built from, extracts what the
customer app needs (clinics, doctors, programmes and prices, the 13-question
skin analysis, device aftercare), and writes:

  index.html     the installable PWA (full document, manifest + service worker)
  artifact.html  the same page as a body fragment, for publishing as a Claude artifact

Edit src/app.html for UI and behaviour, ../website/catalog.json for content.
Never hand-edit index.html or artifact.html.
"""
import json, pathlib, re, datetime

HERE = pathlib.Path(__file__).resolve().parent
# Standalone checkout: use the vendored copy in this folder when the website folder is not a sibling.
CATALOG = HERE.parent / "website" / "catalog.json"
if not CATALOG.exists():
    CATALOG = HERE / "catalog.json"
SRC = HERE / "src" / "app.html"

c = json.loads(CATALOG.read_text(encoding="utf-8"))

def pick(d, keys):
    return {k: d.get(k) for k in keys if k in d}

data = {
    "built": datetime.date.today().isoformat(),
    "site": pick(c["site"], ["name", "short", "url", "whatsapp_number", "whatsapp_display", "whatsapp_hours", "instagram", "price_note"]),
    "clinics": [pick(k, ["code", "name", "short", "area", "address", "maps", "hours", "landmark"]) for k in c["clinics"]],
    "doctors": [pick(d, ["name", "clinics", "focus"]) for d in c["doctors"] if d.get("publish")],
    "levels": [pick(l, ["code", "name", "blurb"]) for l in c.get("levels", [])],
    "concerns": [
        {
            **pick(con, ["code", "name", "title", "intro"]),
            "offers": [pick(o, ["name", "level", "includes", "duration_min", "interval", "single", "pack3", "pack6"]) for o in con["offers"]],
        }
        for con in c["concerns"]
    ],
    "first_visit": pick(c.get("first_visit") or {"title": "Harga kunjungan pertama", "note": "", "items": []}, ["title", "note", "items"]),
    "plan": pick(c.get("plan") or {"title": "Skin Habit Plan", "price_month": None, "min_months": 3, "includes": [], "rules": ""}, ["title", "price_month", "min_months", "includes", "rules"]),
    "addons": c.get("addons", []),
    "front_door": pick(c.get("front_door") or {"name": "Konsultasi dokter gratis", "desc": "Setiap pelanggan mulai di sini."}, ["name", "desc"]),
    "assessment": {
        **pick(c["assessment"], ["title", "subtitle", "disclaimer"]),
        "scan_enabled": bool(c["assessment"].get("scan", {}).get("enabled")),
        "scan_title": c["assessment"].get("scan", {}).get("title"),
        "blocks": [
            {**pick(b, ["code", "title", "intro"]),
             "questions": [pick(q, ["id", "text", "type", "options", "options_by_concern", "placeholder", "flag", "help"]) for q in b["questions"]]}
            for b in c["assessment"]["blocks"]
        ],
    },
    "devices": [pick(d, ["slug", "name", "aftercare", "downtime", "avoid_if"]) for d in c["education"]["devices"]],
    "treatments": [pick(t, ["name", "device", "performed_by", "duration_min"]) for t in c["education"]["treatments"]],
}

# strip English twins and private keys recursively
def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items() if not k.endswith("_en") and not k.startswith("_")}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x

# Photos come from the website build (../website/assets), resized into assets/photos/ and inlined,
# so the published artifact shows them without loading anything from another host.
import base64, subprocess
WEB = HERE.parent / "website"
CACHE = HERE / "assets" / "photos"
CACHE.mkdir(parents=True, exist_ok=True)
PHOTOS = {
    "booking": "assets/clinics/ruang-treatment-1.jpg",
    "rebook": "assets/clinics/lmp-treatment-tangan.jpg",
    "analisis": "assets/clinics/lmp-treatment-alat.jpg",
    "chat": "assets/clinics/dinding-good-skin.jpg",
    "loyalty": "assets/clinics/sudut-produk-1.jpg",
    "clinic_SB": "assets/clinics/ruang-treatment-2.jpg",
    "clinic_CITOS": "assets/clinics/ruang-treatment-3.jpg",
    "clinic_LMP": "assets/clinics/lmp-alat-1.jpg",
    "clinic_TSM": "assets/clinics/tsm-resepsi.jpg",
}

def inline(rel, size, key):
    src = WEB / rel
    ext = ".png" if rel.lower().endswith(".png") else ".jpg"
    out = CACHE / (key + ext)
    if not src.exists():
        # No website checkout beside us: use the cached, already-resized copy committed in assets/photos.
        if out.exists():
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return "data:%s;base64,%s" % (mime, base64.b64encode(out.read_bytes()).decode())
        return ""
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        args = ["sips", "-Z", str(size), str(src), "--out", str(out)]
        if ext == ".jpg":
            args[1:1] = ["-s", "format", "jpeg", "-s", "formatOptions", "68"]
        subprocess.run(args, check=True, capture_output=True)
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(out.read_bytes()).decode())

photos = {k: inline(v, 720, k) for k, v in PHOTOS.items()}
photos["logo"] = inline("assets/logo-mark.png", 96, "logo")
src_docs = {d["name"]: d.get("photo", "") for d in c["doctors"]}
for d in data["doctors"]:
    rel = src_docs.get(d["name"], "")
    slug = re.sub(r"[^a-z0-9]+", "-", d["name"].lower()).strip("-")
    d["photo"] = inline(rel, 220, "dr-" + slug) if rel else ""
data["photos"] = photos
data = clean(data)
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

src = SRC.read_text(encoding="utf-8")
assert "/*__DATA__*/" in src, "src/app.html must contain /*__DATA__*/"
fragment = src.replace("/*__DATA__*/", payload)

(HERE / "artifact.html").write_text(fragment, encoding="utf-8")

full = (
    "<!doctype html>\n<html lang=\"id\">\n<head>\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
    "<meta name=\"theme-color\" content=\"#FFFFFF\" media=\"(prefers-color-scheme: light)\">\n"
    "<meta name=\"theme-color\" content=\"#161613\" media=\"(prefers-color-scheme: dark)\">\n"
    "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
    "<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\">\n"
    "<meta name=\"apple-mobile-web-app-title\" content=\"Surface\">\n"
    "<link rel=\"manifest\" href=\"manifest.webmanifest\">\n"
    "<link rel=\"icon\" href=\"assets/icon-192.png\">\n"
    "<link rel=\"apple-touch-icon\" href=\"assets/icon-192.png\">\n"
    "</head>\n<body>\n"
    + fragment +
    "\n<script>if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}</script>\n"
    "</body>\n</html>\n"
)
(HERE / "index.html").write_text(full, encoding="utf-8")

print("built index.html (%d KB) and artifact.html (%d KB) from %s" % (len(full) // 1024, len(fragment) // 1024, CATALOG.name))
print("doctors:", len(data["doctors"]), "| clinics:", len(data["clinics"]), "| programmes:", sum(len(x["offers"]) for x in data["concerns"]), "| questions:", sum(len(b["questions"]) for b in data["assessment"]["blocks"]))

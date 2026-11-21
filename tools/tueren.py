#!/usr/bin/env python3
"""Eingangstüren für narvaez-arts.com erzeugen.

Für jeden Bereich (Kunst, Cartoon, Illustration, Über mich, Kontakt) und jede Reihe aus dem Admin (z. B. Breva)
entsteht eine Kopie von index.html mit eigenem Titel, eigener Beschreibung und eigenem Vorschaubild, z. B. breva.html.
GitHub Pages liefert sie unter https://narvaez-arts.com/breva aus. window.TUER.h in der Kopie sagt der Seite,
was sie aufschlagen soll (wie der Teil hinter # in der normalen Adresse). Dazu wird sitemap.xml neu geschrieben.

Läuft automatisch über .github/workflows/tueren.yml (täglich und nach jeder Änderung an index.html);
von Hand: python3 tools/tueren.py
"""
import html, json, os, re, sys, unicodedata, urllib.request

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEITE = "https://narvaez-arts.com"
SB_URL = "https://owbbsnujnkhyyqvagtai.supabase.co"
SB_KEY = "sb_publishable_29TK9hJ-e8e4eW9rp_eA8A__EHL2Kga"   # öffentlicher Schlüssel (steht auch in index.html)
LISTE = os.path.join(WURZEL, "tools", "tueren.json")
GESCHUETZT = {"index", "404", "admin", "vorschau"}
NAME = "Eva Narváez"

BEREICHE = [   # (Adresse, was aufgeschlagen wird, Titel, Beschreibung)
    ("kunst", "kunst", f"Bildende Kunst – {NAME}", "Malerei von Eva Narváez: Aquarell, Acryl, Collage und Enkaustik – Farbe, Emotion und persönliche Erfahrung."),
    ("cartoon", "cartoon/cartoon", f"Cartoon – {NAME}", "Cartoons von Eva Narváez alias Breva: kleine Szenen aus dem Alltag, mit Witz und spanischem Temperament gezeichnet."),
    ("illustration", "cartoon/illustration", f"Illustration – {NAME}", "Illustrationen von Eva Narváez: Bilder zu Geschichten, Texten und Ideen."),
    ("ueber-mich", "ueber", f"Über mich – {NAME}", "Eva Narváez, bildende Künstlerin und Illustratorin: wer sie ist, wie sie arbeitet und was sie antreibt."),
    ("kontakt", "kontakt", f"Kontakt – {NAME}", "Kontakt zu Eva Narváez: E-Mail und Instagram für Anfragen zu Bildern, Aufträgen und Ausstellungen."),
]
TYP_WORT = {"cartoon": "Cartoons", "illustration": "Illustrationen"}


def holen(pfad):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{pfad}", headers={"apikey": SB_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def kurzname(text):
    t = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def bild_url(pfad, breite=1200):
    return f"{SB_URL}/storage/v1/render/image/public/artworks/{urllib.request.quote(pfad)}?width={breite}&height={breite * 3}&resize=contain&quality=80"


def setze(s, muster, ersatz):
    neu, n = re.subn(muster, ersatz, s, count=1)
    if n != 1:
        sys.exit(f"Stelle nicht gefunden: {muster}")
    return neu


def tuer_seite(vorlage, slug, titel, beschreibung, ziel, bild=None):
    a = lambda x: html.escape(x, quote=True)
    url = f"{SEITE}/{slug}"
    s = vorlage
    s = setze(s, r"<title>[^<]*</title>", f"<title>{a(titel)}</title>")
    s = setze(s, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{a(beschreibung)}">')
    s = setze(s, r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">')
    s = setze(s, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{a(titel)}">')
    s = setze(s, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{a(beschreibung)}">')
    s = setze(s, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">')
    if bild:
        s = setze(s, r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{a(bild)}">')
        s = re.sub(r'<meta name="twitter:image" content="[^"]*">', f'<meta name="twitter:image" content="{a(bild)}">', s, count=1)
        s = re.sub(r'\s*<meta property="og:image:(width|height|alt)" content="[^"]*">', "", s)
    marke = "<!-- Eingangstür, erzeugt von tools/tueren.py – nicht von Hand bearbeiten -->"
    s = setze(s, r'<meta charset="utf-8">', f'<meta charset="utf-8">\n{marke}\n<script>window.TUER={json.dumps({"h": ziel}, ensure_ascii=False)}</script>')
    return s


def main():
    vorlage = open(os.path.join(WURZEL, "index.html"), encoding="utf-8").read()
    werke = holen("artworks?select=category,cartoon_type,series,image_path&published=eq.true&order=sort.asc,created_at.desc")
    tueren = [(slug, titel, text, ziel, None) for slug, ziel, titel, text in BEREICHE]
    vergeben = set(GESCHUETZT) | {t[0] for t in tueren}
    gesehen = set()
    for w in werke:
        if w.get("category") != "cartoon" or not w.get("series"):
            continue
        typ = w.get("cartoon_type") if w.get("cartoon_type") in TYP_WORT else "cartoon"
        if (typ, w["series"]) in gesehen:
            continue
        gesehen.add((typ, w["series"]))
        slug = kurzname(w["series"])
        if not slug or slug in vergeben:
            print(f"übersprungen (Name schon vergeben): {w['series']}")
            continue
        vergeben.add(slug)
        erstes = next((x["image_path"] for x in werke if x.get("series") == w["series"] and x.get("image_path")), None)
        reihe = w["series"]
        tueren.append((slug, f"{reihe} – {TYP_WORT[typ]} von {NAME}",
                       f"{reihe}: eine Reihe von {TYP_WORT[typ]} von {NAME}" + (" alias Breva." if typ == "cartoon" else "."),
                       f"cartoon/{typ}/{reihe}", bild_url(erstes) if erstes else None))

    for slug, titel, text, ziel, bild in tueren:
        with open(os.path.join(WURZEL, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(tuer_seite(vorlage, slug, titel, text, ziel, bild))

    alt = json.load(open(LISTE)) if os.path.exists(LISTE) else []
    neu = [t[0] for t in tueren]
    for slug in alt:
        pfad = os.path.join(WURZEL, slug + ".html")
        if slug not in neu and slug not in GESCHUETZT and os.path.exists(pfad) and "erzeugt von tools/tueren.py" in open(pfad, encoding="utf-8").read(2000):
            os.remove(pfad)
            print(f"entfernt: {slug}.html")
    json.dump(neu, open(LISTE, "w"), indent=1)

    zeilen = [f"  <url><loc>{SEITE}/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>"]
    zeilen += [f"  <url><loc>{SEITE}/{s}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>" for s in neu]
    with open(os.path.join(WURZEL, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(zeilen) + "\n</urlset>\n")
    print("Türen:", ", ".join(neu))


if __name__ == "__main__":
    main()

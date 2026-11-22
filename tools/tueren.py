#!/usr/bin/env python3
"""Eingangstüren für narvaez-arts.com erzeugen – in drei Sprachen.

Für jeden Bereich (Kunst, Cartoon, Illustration, Über mich, Kontakt) und jede Reihe aus dem Admin (z. B. Breva)
entsteht eine Kopie von index.html mit eigenem Titel, eigener Beschreibung und eigenem Vorschaubild:
  Deutsch   kunst.html            → https://narvaez-arts.com/kunst
  Spanisch  es/bellas-artes.html  → https://narvaez-arts.com/es/bellas-artes
  Englisch  en/fine-art.html      → https://narvaez-arts.com/en/fine-art
dazu es/index.html und en/index.html als Startseiten. window.TUER.h in der Kopie sagt der Seite, was sie aufschlagen
soll; die Sprache erkennt die Seite an der Adresse (/es/, /en/). Jede Seite verweist auf ihre Fassungen in den
anderen Sprachen (hreflang), und sitemap.xml wird mit allen drei Sprachen neu geschrieben.

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
SPRACHEN = ("de", "es", "en")
LOCALE = {"de": "de_DE", "es": "es_ES", "en": "en_GB"}

# Bereich: Schlüssel → (was aufgeschlagen wird, {Sprache: (Adresse, Titel, Beschreibung)}). Adressen müssen zu SLUGS in index.html passen.
BEREICHE = {
    "kunst": ("kunst", {
        "de": ("kunst", f"Bildende Kunst – {NAME}", "Malerei von Eva Narváez: Aquarell, Acryl, Collage und Enkaustik – Farbe, Emotion und persönliche Erfahrung."),
        "es": ("bellas-artes", f"Bellas Artes – {NAME}", "Pintura de Eva Narváez: acuarela, acrílico, collage y encáustica – color, emoción y experiencia personal."),
        "en": ("fine-art", f"Fine Art – {NAME}", "Paintings by Eva Narváez: watercolour, acrylic, collage and encaustic – colour, emotion and personal experience.")}),
    "cartoon": ("cartoon/cartoon", {
        "de": ("cartoon", f"Cartoon – {NAME}", "Cartoons von Eva Narváez alias Breva: kleine Szenen aus dem Alltag, mit Witz und spanischem Temperament gezeichnet."),
        "es": ("cartoon", f"Cartoon – {NAME}", "Cartoons de Eva Narváez, alias Breva: pequeñas escenas de la vida diaria, dibujadas con humor y temperamento andaluz."),
        "en": ("cartoon", f"Cartoon – {NAME}", "Cartoons by Eva Narváez, alias Breva: little everyday scenes, drawn with humour and Spanish temperament.")}),
    "illustration": ("cartoon/illustration", {
        "de": ("illustration", f"Illustration – {NAME}", "Illustrationen von Eva Narváez: Bilder zu Geschichten, Texten und Ideen."),
        "es": ("ilustracion", f"Ilustración – {NAME}", "Ilustraciones de Eva Narváez: imágenes para historias, textos e ideas."),
        "en": ("illustration", f"Illustration – {NAME}", "Illustrations by Eva Narváez: pictures for stories, texts and ideas.")}),
    "ueber-mich": ("ueber", {
        "de": ("ueber-mich", f"Über mich – {NAME}", "Eva Narváez, bildende Künstlerin und Illustratorin: wer sie ist, wie sie arbeitet und was sie antreibt."),
        "es": ("sobre-mi", f"Sobre mí – {NAME}", "Eva Narváez, artista plástica e ilustradora de Cádiz: quién es, cómo trabaja y qué la mueve."),
        "en": ("about", f"About me – {NAME}", "Eva Narváez, visual artist and illustrator from Cádiz: who she is, how she works and what drives her.")}),
    "kontakt": ("kontakt", {
        "de": ("kontakt", f"Kontakt – {NAME}", "Kontakt zu Eva Narváez: E-Mail und Instagram für Anfragen zu Bildern, Aufträgen und Ausstellungen."),
        "es": ("contacto", f"Contacto – {NAME}", "Contacto con Eva Narváez: correo e Instagram para consultas sobre obras, encargos y exposiciones."),
        "en": ("contact", f"Contact – {NAME}", "Contact Eva Narváez: email and Instagram for enquiries about artworks, commissions and exhibitions.")}),
}
STARTSEITE = {   # Titel und Beschreibung der Startseiten /es/ und /en/ (die deutsche ist index.html selbst)
    "es": (f"{NAME} – Bellas Artes e ilustración", "Eva Narváez – artista plástica e ilustradora. Pintura, cartoon e ilustración: color, emoción y experiencia personal."),
    "en": (f"{NAME} – Fine Art & Illustration", "Eva Narváez – visual artist and illustrator. Painting, cartoon and illustration: colour, emotion and personal experience."),
}
TYP_WORT = {"de": {"cartoon": "Cartoons", "illustration": "Illustrationen"},
            "es": {"cartoon": "cartoons", "illustration": "ilustraciones"},
            "en": {"cartoon": "cartoons", "illustration": "illustrations"}}


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
    neu, n = re.subn(muster, lambda m: ersatz, s, count=1)   # Funktion: Ersatztext wird nicht als Muster gelesen
    if n != 1:
        sys.exit(f"Stelle nicht gefunden: {muster}")
    return neu


def url_von(pfad):   # Dateipfad ohne .html → öffentliche Adresse
    if pfad in ("", "index"):
        return SEITE + "/"
    if pfad.endswith("/index"):
        return f"{SEITE}/{pfad[:-6]}/"
    return f"{SEITE}/{pfad}"


def seite(vorlage, pfad, sprache, titel, beschreibung, ziel, fassungen, bild=None):
    """Eine Tür: pfad = Datei ohne .html (z. B. 'es/bellas-artes'), fassungen = {Sprache: pfad} für hreflang."""
    a = lambda x: html.escape(x, quote=True)
    url = url_von(pfad)
    s = vorlage
    s = setze(s, r'<html lang="[^"]*">', f'<html lang="{sprache}">')
    s = setze(s, r"<title>[^<]*</title>", f"<title>{a(titel)}</title>")
    s = setze(s, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{a(beschreibung)}">')
    s = setze(s, r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">')
    s = setze(s, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{a(titel)}">')
    s = setze(s, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{a(beschreibung)}">')
    s = setze(s, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">')
    andere = [l for l in SPRACHEN if l != sprache]
    s = setze(s, r'<meta property="og:locale" content="[^"]*">', f'<meta property="og:locale" content="{LOCALE[sprache]}">')
    s = re.sub(r'<meta property="og:locale:alternate" content="[^"]*">\n?', "", s)
    s = setze(s, r'(<meta property="og:locale" content="[^"]*">)',
              f'<meta property="og:locale" content="{LOCALE[sprache]}">\n' + "\n".join(f'<meta property="og:locale:alternate" content="{LOCALE[l]}">' for l in andere))
    verweise = "".join(f'<link rel="alternate" hreflang="{l}" href="{url_von(p)}">' for l, p in fassungen.items())
    if "de" in fassungen:
        verweise += f'<link rel="alternate" hreflang="x-default" href="{url_von(fassungen["de"])}">'
    s = setze(s, r"<!--sprachen-->.*?<!--/sprachen-->", f"<!--sprachen-->{verweise}<!--/sprachen-->")
    if bild:
        s = setze(s, r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{a(bild)}">')
        s = re.sub(r'<meta name="twitter:image" content="[^"]*">', f'<meta name="twitter:image" content="{a(bild)}">', s, count=1)
        s = re.sub(r'\s*<meta property="og:image:(width|height|alt)" content="[^"]*">', "", s)
    marke = "<!-- Eingangstür, erzeugt von tools/tueren.py – nicht von Hand bearbeiten -->"
    s = setze(s, r'<meta charset="utf-8">', f'<meta charset="utf-8">\n{marke}\n<script>window.TUER={json.dumps({"h": ziel, "l": sprache}, ensure_ascii=False)}</script>')
    return s


def main():
    vorlage = open(os.path.join(WURZEL, "index.html"), encoding="utf-8").read()
    werke = holen("artworks?select=category,cartoon_type,series,image_path&published=eq.true&order=sort.asc,created_at.desc")
    gruppen = []   # je Inhalt eine Gruppe: (ziel, bild, {Sprache: (pfad, titel, beschreibung)})
    # Startseiten /es/ und /en/ (Deutsch = index.html, wird nicht überschrieben, steht aber in den Verweisen)
    gruppen.append(("", None, {"de": ("index", None, None), **{l: (f"{l}/index", *STARTSEITE[l]) for l in ("es", "en")}}))
    for key, (ziel, texte) in BEREICHE.items():
        gruppen.append((ziel, None, {l: ((slug if l == "de" else f"{l}/{slug}"), t, b) for l, (slug, t, b) in texte.items()}))
    vergeben = set(GESCHUETZT) | {g[2]["de"][0] for g in gruppen} | {g[2][l][0].split("/", 1)[1] for g in gruppen for l in ("es", "en")}
    gesehen = set()
    for w in werke:
        if w.get("category") != "cartoon" or not w.get("series"):
            continue
        typ = w.get("cartoon_type") if w.get("cartoon_type") in ("cartoon", "illustration") else "cartoon"
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
        texte = {
            "de": (slug, f"{reihe} – {TYP_WORT['de'][typ]} von {NAME}", f"{reihe}: eine Reihe von {TYP_WORT['de'][typ]} von {NAME}" + (" alias Breva." if typ == "cartoon" else ".")),
            "es": (f"es/{slug}", f"{reihe} – {TYP_WORT['es'][typ].capitalize()} de {NAME}", f"{reihe}: una serie de {TYP_WORT['es'][typ]} de {NAME}" + (", alias Breva." if typ == "cartoon" else ".")),
            "en": (f"en/{slug}", f"{reihe} – {TYP_WORT['en'][typ].capitalize()} by {NAME}", f"{reihe}: a series of {TYP_WORT['en'][typ]} by {NAME}" + (", alias Breva." if typ == "cartoon" else ".")),
        }
        gruppen.append((f"cartoon/{typ}/{reihe}", bild_url(erstes) if erstes else None, texte))

    os.makedirs(os.path.join(WURZEL, "es"), exist_ok=True)
    os.makedirs(os.path.join(WURZEL, "en"), exist_ok=True)
    neu = []
    for ziel, bild, texte in gruppen:
        fassungen = {l: texte[l][0] for l in SPRACHEN}
        for l in SPRACHEN:
            pfad, titel, text = texte[l]
            if pfad == "index":
                continue   # die deutsche Startseite ist die Vorlage selbst
            with open(os.path.join(WURZEL, pfad + ".html"), "w", encoding="utf-8") as f:
                f.write(seite(vorlage, pfad, l, titel, text, ziel, fassungen, bild))
            neu.append(pfad)

    # Türen, die es nicht mehr gibt, entfernen (nur solche, die dieses Skript selbst angelegt hat)
    alt = json.load(open(LISTE)) if os.path.exists(LISTE) else []
    for pfad in alt:
        datei = os.path.join(WURZEL, pfad + ".html")
        if pfad not in neu and pfad not in GESCHUETZT and os.path.exists(datei) and "erzeugt von tools/tueren.py" in open(datei, encoding="utf-8").read(2000):
            os.remove(datei)
            print(f"entfernt: {pfad}.html")
    json.dump(neu, open(LISTE, "w"), indent=1)

    # Sitemap mit allen Sprachen; leere Bereiche (z. B. „Illustration“, solange es keine gibt) nicht bei Google anmelden –
    # die Türen selbst bleiben, damit alte Links funktionieren
    leer = set() if any(w.get("category") == "cartoon" and w.get("cartoon_type") == "illustration" for w in werke) else {"cartoon/illustration"}
    zeilen = []
    for ziel, _, texte in gruppen:
        if ziel in leer:
            continue
        alternativen = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{url_von(texte[l][0])}"/>' for l in SPRACHEN)
        for l in SPRACHEN:
            prio = "1.0" if not ziel else "0.8"
            zeilen.append(f"  <url><loc>{url_von(texte[l][0])}</loc>{alternativen}<changefreq>monthly</changefreq><priority>{prio}</priority></url>")
    with open(os.path.join(WURZEL, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(zeilen) + "\n</urlset>\n")
    print("Türen:", ", ".join(neu))


if __name__ == "__main__":
    main()

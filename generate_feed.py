#!/usr/bin/env python3
"""
Agrégateur RSS — Nîmes & Gard (hors Actu.fr)
---------------------------------------------
Fusionne un ou plusieurs flux RSS d'actualité, ne garde que les
articles pertinents pour Nîmes / le Gard, exclut systématiquement
Actu.fr, dédoublonne les articles repris par plusieurs sources, puis
régénère un flux RSS 2.0 propre (feed.xml).

Aucune dépendance externe (bibliothèque standard uniquement) afin de
tourner tel quel dans GitHub Actions sans étape d'installation.
"""

import re
import hashlib
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime, format_datetime

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

# Sources RSS à fusionner. La recherche Google Actualités agrège
# automatiquement des centaines de médias français : c'est la source
# "large" qui couvre "n'importe quel média". L'opérateur -site:actu.fr
# exclut déjà ce média au niveau de la requête elle-même.
# "when:2d" restreint aux articles des dernières 48h pour garder le
# flux focalisé sur l'actualité récente (ajustable : when:1d, when:7d…).
SOURCES = [
    "https://news.google.com/rss/search?q=(N%C3%AEmes+OR+Gard)+-site:actu.fr+when:2d&hl=fr&gl=FR&ceid=FR:fr",
]

# Pour ajouter le flux RSS natif d'un média local en plus de Google
# Actualités (souvent plus rapide que l'indexation Google) :
#   1. Ouvrez le site du média
#   2. Affichez le code source (Ctrl+U) et cherchez "application/rss+xml"
#      — ou essayez simplement <site>/feed ou <site>/rss
#   3. Ajoutez l'URL trouvée ci-dessous, par exemple :
# SOURCES.append("https://www.exemple-media.fr/feed")

# Domaines toujours exclus, quelle que soit la source (sécurité en
# plus du -site:actu.fr déjà présent dans la requête Google).
EXCLUDED_DOMAINS = ["actu.fr"]

# Un article n'est conservé que si l'un de ces mots-clés apparaît dans
# son titre ou son résumé — protège la pertinence si vous ajoutez plus
# tard des flux génériques (nationaux) non pré-filtrés par ville.
KEYWORDS = ["nimes", "nimois", "nimoise", "gard", "gardois", "gardoise"]

MAX_ITEMS = 80
OUTPUT_FILE = "feed.xml"
FEED_TITLE = "Actualités Nîmes & Gard (hors Actu.fr)"
FEED_LINK = "https://news.google.com/"
FEED_DESC = (
    "Agrégation automatique d'articles de presse concernant Nîmes et le "
    "Gard, toutes sources confondues sauf Actu.fr."
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 NimesGardRSSBot/1.0"
    )
}

# ----------------------------------------------------------------------


def normalize(text):
    """Minuscule, sans accents, ponctuation compressée : pour dédoublonner/filtrer."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def parse_feed(raw_xml):
    """Parse un flux RSS 2.0 (Google Actualités ou média classique)."""
    items = []
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError:
        return items

    channel = root.find("channel")
    if channel is None:
        return items

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = item.findtext("pubDate")
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""

        try:
            pub_dt = parsedate_to_datetime(pub) if pub else None
            if pub_dt and pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pub_dt = None

        items.append(
            {
                "title": title,
                "link": link,
                "desc": desc,
                "pub_dt": pub_dt,
                "source": source,
            }
        )
    return items


def is_excluded(item):
    haystack = f"{item['link']} {item['source']}".lower()
    return any(domain in haystack for domain in EXCLUDED_DOMAINS)


def is_relevant(item):
    haystack = normalize(f"{item['title']} {item['desc']}")
    return any(normalize(kw) in haystack for kw in KEYWORDS)


def dedup_key(item):
    """Clé de dédoublonnage basée sur le titre normalisé : deux médias qui
    reprennent la même dépêche/actualité ont des titres quasi identiques
    mais des liens différents (chacun vers son propre site)."""
    norm_title = normalize(item["title"])
    if norm_title:
        return norm_title
    return item["link"] or hashlib.sha1((item["desc"] or "").encode()).hexdigest()


def build_feed(items):
    items = sorted(
        items,
        key=lambda i: i["pub_dt"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:MAX_ITEMS]

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESC
    ET.SubElement(channel, "language").text = "fr-fr"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))

    for item in items:
        it = ET.SubElement(channel, "item")
        ET.SubElement(it, "title").text = item["title"]
        ET.SubElement(it, "link").text = item["link"]
        ET.SubElement(it, "guid").text = item["link"] or dedup_key(item)
        if item["desc"]:
            ET.SubElement(it, "description").text = item["desc"]
        if item["source"]:
            ET.SubElement(it, "source").text = item["source"]
        if item["pub_dt"]:
            ET.SubElement(it, "pubDate").text = format_datetime(item["pub_dt"])

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)


def main():
    all_items = []
    for url in SOURCES:
        try:
            raw = fetch(url)
            all_items.extend(parse_feed(raw))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] échec sur {url}: {exc}")

    filtered = [i for i in all_items if not is_excluded(i) and is_relevant(i)]

    best_by_key = {}
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    for i in filtered:
        key = dedup_key(i)
        current = best_by_key.get(key)
        if current is None or (i["pub_dt"] or epoch) > (current["pub_dt"] or epoch):
            best_by_key[key] = i
    unique = list(best_by_key.values())

    build_feed(unique)
    print(f"{len(unique)} article(s) écrit(s) dans {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

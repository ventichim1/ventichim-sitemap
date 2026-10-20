"""Bouwt een hreflang-sitemap voor ventichim.be (Belgie) en ventichim.nl (Nederland).

Bron: de sitemap die Vendisto zelf maakt (https://www.ventichim.be/Sitemap/Google). Die koppelt elke
Nederlandstalige pagina al aan de Franse en Engelse versie, maar zet alles op www.ventichim.nl en zegt
niet voor welk land een adres bedoeld is. Dit script maakt daar per pagina een groep van zes adressen van:

    www.ventichim.be/nl/...  nl-BE   (ook x-default)
    www.ventichim.be/fr/...  fr      (alle Franstaligen: Belgie, Frankrijk, Luxemburg)
    www.ventichim.be/en/...  en
    www.ventichim.nl/nl/...  nl-NL
    www.ventichim.nl/fr/...  fr-NL
    www.ventichim.nl/en/...  en-NL

Elk adres in de groep noemt alle andere (zo wil Google het). Pagina's die niet (meer) bestaan, worden
eruit gelaten: Vendisto stuurt die met een 302 naar /Error/404.

Gebruik:
    python bouw_sitemap.py            sitemap bouwen in .\\site, status van nieuwe adressen nakijken
    python bouw_sitemap.py --alles    status van alle adressen opnieuw nakijken
    python bouw_sitemap.py --geen-controle   niets nakijken (sneller, alleen om te testen)
"""

import argparse
import concurrent.futures
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

BRON = "https://www.ventichim.be/Sitemap/Google"
BE = "https://www.ventichim.be"
NL = "https://www.ventichim.nl"
BASIS_URL = "https://sitemap.ventichim.be"
HIER = pathlib.Path(__file__).resolve().parent
UIT = HIER / "site"
STATUS = HIER / "status.json"
UA = "Mozilla/5.0 (compatible; VentichimSitemap/1.0; +https://www.ventichim.be)"
HERCONTROLE_NA_DAGEN = 7

# (host, taal) -> hreflang-code
CODES = {
    (BE, "nl"): "nl-BE",
    (BE, "fr"): "fr",
    (BE, "en"): "en",
    (NL, "nl"): "nl-NL",
    (NL, "fr"): "fr-NL",
    (NL, "en"): "en-NL",
}
TALEN = ("nl", "fr", "en")
WEG = re.compile(r"^/kennisbank-voorbeeld-")  # proefpagina's zonder taal, horen niet in Google


def haal(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8-sig")


def pad_van(url):
    return urllib.parse.urlsplit(url).path


def codeer(pad):
    """Pad URL-veilig maken (o.a. de ø in maten); bestaande %-codes blijven staan."""
    return urllib.parse.quote(pad, safe="/%-._~!$&'()*+,;=:@")


def lees_bron(xml):
    """Geeft (groepen, losse) terug. groep = {taal: pad}, los = (pad, lastmod)."""
    groepen, losse = [], []
    for blok in re.findall(r"<url>.*?</url>", xml, flags=re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", blok).group(1).strip()
        lm = re.search(r"<lastmod>([^<]+)</lastmod>", blok)
        lastmod = lm.group(1).strip() if lm else None
        alt = dict(re.findall(r'hreflang="([a-z]{2})"\s+href="([^"]+)"', blok))
        pad = pad_van(loc)
        if WEG.match(pad):
            continue
        if all(t in alt for t in TALEN):
            groepen.append({"lastmod": lastmod, **{t: pad_van(alt[t]) for t in TALEN}})
        else:
            losse.append((pad, lastmod))
    return groepen, losse


def status_van(pad):
    """200 = bestaat. Vendisto stuurt een onbestaande pagina met 302 naar /Error/404."""

    class GeenVolgen(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(GeenVolgen)
    req = urllib.request.Request(BE + codeer(pad), headers={"User-Agent": UA})
    try:
        with opener.open(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0  # netwerkfout: later opnieuw proberen


def controleer(paden, alles):
    oud = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    nu = dt.datetime.now(dt.timezone.utc)
    te_doen = []
    for p in paden:
        r = oud.get(p)
        verlopen = r is None or alles or r["code"] == 0 or (
            nu - dt.datetime.fromisoformat(r["op"])).days >= HERCONTROLE_NA_DAGEN
        if verlopen:
            te_doen.append(p)
    print(f"status nakijken: {len(te_doen)} van {len(paden)} adressen", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i, (p, code) in enumerate(zip(te_doen, pool.map(status_van, te_doen)), 1):
            oud[p] = {"code": code, "op": nu.isoformat(timespec="seconds")}
            if i % 500 == 0:
                print(f"  {i}/{len(te_doen)}", flush=True)
    bewaard = {p: oud[p] for p in paden if p in oud}
    STATUS.write_text(json.dumps(bewaard, ensure_ascii=False, indent=0), encoding="utf-8")
    return {p: v["code"] for p, v in bewaard.items()}


def url_blok(loc, lastmod, links):
    regels = [f"<url><loc>{escape(loc)}</loc>"]
    if lastmod:
        regels.append(f"<lastmod>{escape(lastmod)}</lastmod>")
    for code, href in links:
        regels.append(f'<xhtml:link rel="alternate" hreflang="{code}" href="{escape(href)}"/>')
    regels.append("</url>")
    return "".join(regels)


KOP = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
       'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')


def bouw(groepen, losse):
    bestanden = {k: [] for k in CODES}
    for g in groepen:
        links = [(CODES[(h, t)], h + codeer(g[t])) for h in (BE, NL) for t in TALEN]
        links.append(("x-default", BE + codeer(g["nl"])))
        for h in (BE, NL):
            for t in TALEN:
                bestanden[(h, t)].append(url_blok(h + codeer(g[t]), g["lastmod"], links))
    # pagina's zonder vertaalkoppeling (vaste pagina's): alleen het paar Belgie/Nederland
    for pad, lastmod in losse:
        taal = pad.strip("/").split("/")[0] if pad.strip("/") else "nl"
        if taal not in TALEN:
            continue
        links = [(CODES[(BE, taal)], BE + codeer(pad)), (CODES[(NL, taal)], NL + codeer(pad))]
        for h in (BE, NL):
            bestanden[(h, taal)].append(url_blok(h + codeer(pad), lastmod, links))

    UIT.mkdir(exist_ok=True)
    namen = []
    for (h, t), blokken in bestanden.items():
        naam = f"sitemap-{'be' if h == BE else 'nl'}-{t}.xml"
        (UIT / naam).write_text(KOP + "\n".join(blokken) + "\n</urlset>\n", encoding="utf-8")
        namen.append((naam, len(blokken)))
    vandaag = dt.date.today().isoformat()
    index = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    index += [f"<sitemap><loc>{BASIS_URL}/{n}</loc><lastmod>{vandaag}</lastmod></sitemap>"
              for n, _ in namen]
    index.append("</sitemapindex>")
    (UIT / "sitemap_index.xml").write_text("\n".join(index) + "\n", encoding="utf-8")
    (UIT / "CNAME").write_text("sitemap.ventichim.be\n", encoding="utf-8")
    (UIT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASIS_URL}/sitemap_index.xml\n",
                                    encoding="utf-8")
    (UIT / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Ventichim sitemap</title>'
        '<p>Sitemap van <a href="https://www.ventichim.be">www.ventichim.be</a> en '
        '<a href="https://www.ventichim.nl">www.ventichim.nl</a>: '
        '<a href="sitemap_index.xml">sitemap_index.xml</a></p>\n', encoding="utf-8")
    (UIT / ".nojekyll").write_text("", encoding="utf-8")
    return namen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alles", action="store_true", help="status van alle adressen opnieuw nakijken")
    ap.add_argument("--geen-controle", action="store_true", help="geen statuscontrole (test)")
    a = ap.parse_args()

    xml = haal(BRON)
    groepen, losse = lees_bron(xml)
    print(f"bron: {len(groepen)} vertaalde pagina's, {len(losse)} losse pagina's")
    if len(groepen) < 1000:
        sys.exit("Te weinig pagina's in de Vendisto-sitemap; vorige versie blijft staan.")

    if not a.geen_controle:
        codes = controleer([g["nl"] for g in groepen] + [p for p, _ in losse], a.alles)
        voor = len(groepen)
        groepen = [g for g in groepen if codes.get(g["nl"]) == 200]
        losse = [(p, lm) for p, lm in losse if codes.get(p) == 200]
        print(f"weggelaten (bestaan niet meer): {voor - len(groepen)} vertaalde pagina's")

    for naam, n in bouw(groepen, losse):
        print(f"{naam}: {n} adressen")


if __name__ == "__main__":
    main()

# Hreflang-sitemap ventichim.be + ventichim.nl

Doel: Google laten weten dat **www.ventichim.be** de Belgische versie is en **www.ventichim.nl** de
Nederlandse, zodat Google in Nederland .nl toont en in België .be, en de twee elkaar niet beconcurreren.
Gestart op 19-10-2026, zonder Integrace.

## Hoe het werkt

`bouw_sitemap.py` haalt de sitemap die Vendisto zelf maakt (`https://www.ventichim.be/Sitemap/Google`).
Die koppelt elke Nederlandstalige pagina al aan de Franse en Engelse versie, maar zet alles op
www.ventichim.nl en zegt niet voor welk land een adres is. Het script maakt per pagina een groep van zes:

| Adres | hreflang |
|---|---|
| www.ventichim.be/nl/... | nl-BE (ook x-default) |
| www.ventichim.be/fr/... | fr (alle Franstaligen) |
| www.ventichim.be/en/... | en |
| www.ventichim.nl/nl/... | nl-NL |
| www.ventichim.nl/fr/... | fr-NL |
| www.ventichim.nl/en/... | en-NL |

Pagina's die niet meer bestaan (Vendisto stuurt die met 302 naar /Error/404) laat het weg; de status
van elk adres staat in `status.json` en wordt na 7 dagen opnieuw nagekeken. Proefpagina's
`/kennisbank-voorbeeld-*` gaan er altijd uit.

Uitvoer in `site\`: zes sitemaps (`sitemap-be-nl.xml` ... `sitemap-nl-en.xml`), `sitemap_index.xml`,
`robots.txt`, `CNAME` (sitemap.ventichim.be) en een kleine `index.html`.

```
python bouw_sitemap.py                 # bouwen, status van nieuwe/oude adressen nakijken
python bouw_sitemap.py --alles         # status van alles opnieuw
python bouw_sitemap.py --geen-controle # snel testen zonder statuscontrole
```

## Waarom een eigen subdomein

Google aanvaardt een sitemap op een ander adres zolang alle domeinen erin geverifieerd zijn in
dezelfde Search Console (cross-site submission). Sinds 19-10-2026 staan sc-domain:ventichim.be en
sc-domain:ventichim.nl op Stevens Google-account. Vendisto zelf kan geen bestanden op www.ventichim.be
zetten (afbeeldingen staan op een CDN-domein), robots.txt en de Vendisto-sitemap kunnen we niet aanpassen.

## Online sinds 20-10-2026

- Openbare repo **github.com/ventichim1/ventichim-sitemap** (dit script, `status.json`, workflow
  `.github/workflows/sitemap.yml`). De workflow draait elke nacht om 03:15 UTC (en via "Run workflow"),
  bouwt de sitemap, zet `status.json` terug (houdt de planning actief) en publiceert via GitHub Pages.
- Combell, DNS ventichim.be: CNAME `sitemap` -> `ventichim1.github.io`. GitHub Pages: eigen domein
  sitemap.ventichim.be, https afgedwongen (Let's Encrypt via GitHub).
- Search Console (sc-domain:ventichim.be, Stevens Google-account, dat ook sc-domain:ventichim.nl heeft):
  `https://sitemap.ventichim.be/sitemap_index.xml` ingediend op 20-10-2026, status "Succesvol".
- Wijzigen: script aanpassen, in de repo zetten (Add file > Upload files), daarna "Run workflow".

## Mail "Run failed: Sitemap bouwen"

GitHub mailt als de nachtelijke run mislukt. De sitemap van de vorige dag blijft dan gewoon online staan;
er gaat niets verloren en de volgende nacht probeert hij het opnieuw.

- 22-10-2026: de laatste stap (publiceren) vond het pakket "github-pages" niet, één seconde nadat het
  klaargezet was. Hapering bij GitHub, niet in het script. Sindsdien wacht de workflow dan 90 seconden
  en probeert hij het één keer opnieuw; pas als ook dat mislukt, komt er een mail.
- Zelf herstellen: Actions > Sitemap bouwen > **Run workflow** (main, vinkje "alles" uit). "Re-run jobs"
  werkt sinds 22-10-2026 ook: de stap "Status bewaren" zet status.json nu bovenop de nieuwste main.
- Foutmelding lezen zonder in te loggen (repo is openbaar):
  `https://api.github.com/repos/ventichim1/ventichim-sitemap/actions/runs` (laatste runs),
  `.../actions/runs/<run-id>/jobs` (welke stap) en `.../check-runs/<job-id>/annotations` (de melding).

## Mail "Soft 404" (26-10-2026)

Search Console meldde een "Soft 404" voor een pagina uit deze sitemap: de Franse versie van de overgangsmof
CIOG. Oorzaak: de webshop crasht op een adres langer dan 260 tekens (302 naar een lege /Error-pagina die 200
geeft; één te lang adresdeel geeft 400). Franse categorienamen zijn lang, dus vooral FR loopt daartegen aan.
Het script keurde tot dan alleen de Nederlandse pagina; sinds 26-10-2026 keurt het elke taal apart en laat
het een Franse of Engelse versie die niet werkt weg (de rest van de groep blijft staan). In het log van de
run staat de lijst "weggelaten vertalingen die niet werken". Staat daar iets, dan is de oplossing de titel
van dat product in die taal inkorten in Vendisto (de shop zet zelf een 301 van het oude naar het nieuwe adres,
behalve voor een adres dat te lang is: dat blijft een foutpagina).

De oude Vendisto-sitemap `https://www.ventichim.be/sitemap.xml` staat ook in Search Console (sinds
13-08-2025, door iemand anders ingediend) met 6.184 fouten "URL niet toegestaan": alle adressen staan op
www.ventichim.nl. Die heeft dus nooit gewerkt.

De sitemap bevat alleen adressen die nu al openbaar in de Vendisto-sitemap staan; er zit niets geheims in.

## Bevindingen 19-10-2026

- Vendisto-sitemap: 6.184 adressen, allemaal op www.ventichim.nl; 6.145 Nederlandstalige pagina's met
  koppeling naar FR en EN, maar de Franse en Engelse productpagina's staan er zelf niet in als adres.
- Er staan dode adressen in (bv. DIZ-groepen: 302 naar /Error/404).
- 8 proefpagina's `/kennisbank-voorbeeld-1..8` staan in de sitemap; die horen offline of uit de sitemap.
- .be en .nl hebben elk een canonical naar zichzelf, wat bij hreflang precies zo moet.

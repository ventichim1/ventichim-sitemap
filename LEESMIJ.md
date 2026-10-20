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

## Nog te doen (vraagt Stevens uitdrukkelijke toestemming)

1. Steven meldt zich zelf aan bij GitHub (account `ventichim1`) in Chrome.
2. Openbare repo `ventichim-sitemap` met dit script en een nachtelijke GitHub Actions-workflow die de
   sitemap bouwt, `status.json` terugzet (houdt de planning actief) en publiceert via GitHub Pages.
3. Bij Combell (DNS ventichim.be): CNAME `sitemap` -> `ventichim1.github.io`; in GitHub Pages het eigen
   domein sitemap.ventichim.be instellen en https afdwingen.
4. In Search Console (property ventichim.be): `https://sitemap.ventichim.be/sitemap_index.xml` indienen;
   na een paar dagen bij Internationale targeting / Sitemaps nakijken of Google ze leest.

De sitemap bevat alleen adressen die nu al openbaar in de Vendisto-sitemap staan; er zit niets geheims in.

## Bevindingen 19-10-2026

- Vendisto-sitemap: 6.184 adressen, allemaal op www.ventichim.nl; 6.145 Nederlandstalige pagina's met
  koppeling naar FR en EN, maar de Franse en Engelse productpagina's staan er zelf niet in als adres.
- Er staan dode adressen in (bv. DIZ-groepen: 302 naar /Error/404).
- 8 proefpagina's `/kennisbank-voorbeeld-1..8` staan in de sitemap; die horen offline of uit de sitemap.
- .be en .nl hebben elk een canonical naar zichzelf, wat bij hreflang precies zo moet.

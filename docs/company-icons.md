# Company icons in the energy app

The user requested a further search for missing company logos on 2026-10-25. Scope: the 43 distinct company names currently returned by the ten visible Layer example queries, not every inactive name in the source registry.

- 18 visible companies have retained official assets and work offline.
- 13 have a configured website and retain the existing remote favicon fallback; an icon is not guaranteed.
- 12 have no confirmed website/logo mapping and remain text-only.

The asset bundle contains 19 official website icons or logos, including a site not currently in those answers. Each file's source URL, MIME type and SHA-256 are in `app/company-icons/manifest.json`. Brand assets remain the property of their respective owners. Icons are display metadata and do not establish an entity link or change ownership rules.

Eight newly checked official sites:

- [Alianza Petrolera](https://alianzapetrolera.com.ar/)
- [Bentia Energy](https://bentiaenergy.com/)
- [EDHIPSA](https://www.edhipsa.com.ar/)
- [Interoil](https://www.interoil.no/?page_id=7)
- [Quintana Energy](https://quintanaep.com/)
- [TanGo Energy Argentina](https://tangoenergia.com/)
- [Venoil Energía](https://www.venoil-energia.com/nosotros/)
- [REFSA](https://www.recursosyenergia.com.ar/Portada)

The similarly named Patagonia Resources recruiting business was excluded: it is not evidence for the oil operator. Corporate acquisitions and historical names were not treated as automatic permission to substitute a new parent brand.

Unconfirmed names:

- BREST S.A. DE SERVICIOS PETROLEROS
- CAPETROL ARGENTINA S.A.
- ENAP SIPETROL ARGENTINA S.A.
- FLXS OGE S.A
- G Y G OIL SERVICE SRL
- GRECOIL y CIA. S.R.L.
- KILWER S.A.
- PATAGONIA RESOURCES S.A.
- PETROLERA EL TREBOL S.A.
- PETROLERA SANTA MARIA SAU
- SELVA MARIA OIL S.A.
- VACA MUERTA INVERSIONES S.A.

`layer/sitios.manual.yaml` retains the source-name mappings; `app/sitios.yaml` contains the normalized runtime mappings. Local assets are preferred before the existing Google/DuckDuckGo fallback. No runtime scraping was added. Failed external lookups may still leave a blank icon; company names always remain visible.

The official retained assets are checked for source receipts, byte fingerprints and offline rendering. To refresh an existing retained asset, fetch its recorded `source_url`, verify the actual image, and update its fingerprint; do not replace an icon with a guessed brand.

White-only icons from Aconcagua and Interoil were excluded after visual inspection because they disappear on the answer table background; their configured sites retain the remote fallback.

# Petróleo y gas con datos de afuera: Wikidata

Una sola consulta SPARQL, ejecutada en GraphDB, que combina dos grafos:

- **Rastro**: las 12 empresas que tienen LEI (de GLEIF), el petróleo de 2025 que les corresponde según su participación en cada concesión (el mismo número del paso 1 de la demo) y, aparte, todo el que declaran como operadoras.
- **Wikidata**, en internet: la misma empresa por su LEI, con su sede, en qué bolsa cotiza, su dueño o matriz y su sitio web.

El cruce es el **LEI**: Rastro y Wikidata usan el mismo identificador, así que no hace falta cargar nada ni escribir un enlace nuevo.

```bash
curl -s -H 'Accept: text/csv' --data-urlencode query@layer/energia/externo/wikidata.rq http://localhost:7210/repositories/rastro
```

Necesita internet. Para la demo en vivo, el resultado del 20 oct 2026 está en `resultado-2026-10-20.csv`:

| Empresa | Su parte, 2025 (m³) | Declara como operadora (m³) | Sede | Cotiza en | Sitio |
|---|---|---|---|---|---|
| YPF | 12,6 millones | 21,4 millones | Buenos Aires | Bolsa de Nueva York, Bolsa de Comercio de Buenos Aires | ypf.com |
| Pan American Energy | 5,6 millones | 6,2 millones | Buenos Aires | — | pan-energy.com |
| Pampa Energía | 0,62 millones | 0,56 millones | Buenos Aires | Bolsa de Nueva York | pampaenergia.com |

**Solo 3 de las 12 empresas tienen su LEI en Wikidata.** Que YPF y Pampa cotizan en Nueva York no está en ninguna de las seis fuentes de Rastro. Ninguna de las tres tiene cargado en Wikidata un dueño o una matriz.

Por nombre exacto aparecen otras cuatro (Pluspetrol, Tecpetrol, Compañía General de Combustibles y Vista), pero no se usan: el nombre es el del grupo y no el de la sociedad argentina, y Vista tiene dos entradas («Vista Energy» y «Vista Oil & Gas»). El cruce por nombre necesitaría una revisión; el LEI, no.

**Requisito:** Wikidata pide que quien consulta se identifique. GraphDB lo hace con `-Dhttp.agent` en `infra/docker-compose.yml`. Wikidata a veces limita las consultas (una por minuto); si responde con error, esperar un par de minutos.

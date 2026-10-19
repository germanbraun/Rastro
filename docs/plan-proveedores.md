# Segundo dominio: proveedores del Estado (EE. UU.)

> **¿Con quién está haciendo negocios el gobierno de EE. UU.?**

El mismo Rastro, con otros datos: los contratos federales de EE. UU., las empresas que los reciben, sus grupos empresarios y las listas de control del gobierno. Demuestra que Rastro sirve para cualquier dominio, con un caso que entiende cualquier persona de negocios: compras, riesgo y compliance.

## Por qué este caso

Tiene los mismos ingredientes que el de oncología:

| En oncología | En proveedores |
|---|---|
| El mismo fármaco escrito de tres formas | La misma empresa escrita de varias formas: «ACME Inc.», «ACME, INC», «Acme Holdings» |
| Cáncer de pulmón incluye sus subtipos (MeSH) | Un grupo incluye sus filiales; un sector incluye sus subsectores (NAICS) |
| Por qué Rastro dice que un ensayo prueba un fármaco | Por qué Rastro dice que una empresa es parte de un grupo |

Y un caso real de nombres confusos, ya visto en los datos: en 2013 la vieja SAIC pasó a llamarse Leidos y una empresa nueva tomó el nombre SAIC. USAspending registra al proveedor «Science Applications International Corporation» con las dos matrices.

## Fuentes (verificadas el 18 oct 2026, desde Docker)

| Fuente | Qué trae | Licencia | Acceso |
|---|---|---|---|
| **USAspending** | Contratos federales, proveedor (UEI), agencia, sector (NAICS), monto y la matriz de cada proveedor, con historia | Dominio público | API abierta, sin clave |
| **GLEIF** | El identificador global de empresas (LEI), nombre legal, país y matriz final | CC0 | API abierta, sin clave |
| **Wikidata** | Para las empresas grandes: LEI, industria, sede, si cotiza en bolsa | CC0 | SPARQL abierto |
| **Lista Consolidada de Control** (trade.gov) | Las listas de control del gobierno de EE. UU. en un solo archivo, incluida OFAC | Dominio público | CSV abierto (16 MB) |
| **NAICS** (Census) | La jerarquía de sectores: 2 a 6 dígitos | Dominio público | CSV abierto |

La lista de empresas inhabilitadas de SAM.gov sería ideal, pero pide una cuenta: queda para una segunda etapa.

## Recorte

Contratos del año fiscal 2025 (oct 2024 a sep 2025) de **más de US$10 millones**: **36.147 contratos**, todas las agencias y sectores. Es un tamaño parecido al de oncología.

## El diccionario de negocio (borrador)

- **Contrato**: monto, fecha, agencia, sector.
- **Proveedor**: la empresa que recibe el contrato (UEI de SAM).
- **Grupo**: la matriz de un proveedor; un grupo incluye sus filiales.
- **Agencia**: el organismo que contrata (Defensa, Salud, Energía…).
- **Sector**: código NAICS; un sector incluye sus subsectores.
- **País**: de la matriz final (GLEIF).
- **Entrada en una lista de control**: de la Lista Consolidada.
- **Evidencia** de cada enlace: por qué Rastro dice que un proveedor es parte de un grupo, tiene tal LEI o coincide con tal entrada de una lista.

## Preguntas de negocio (borrador)

1. ¿Cuánto facturó al gobierno el grupo Leidos en 2025, contando todas sus empresas?
2. ¿Cuáles son los 5 grupos que más facturaron en servicios informáticos (incluidos sus subsectores)?
3. ¿Qué agencias concentran más de un tercio de su gasto en un solo grupo?
4. ¿Qué proveedores tienen su matriz final fuera de EE. UU.?
5. ¿Algún proveedor, o su grupo, aparece en una lista de control del gobierno?
6. ¿Cuántos proveedores distintos tiene el Departamento de Defensa en construcción?
7. ¿Qué grupos que cotizan en bolsa facturaron más de US$1.000 millones?
8. ¿Por qué Rastro dice que esta empresa es parte de este grupo?

Probablemente la 5 dé «ninguno» o casi: los contratistas grandes rara vez están en esas listas. Un «ninguno» bien respaldado también es una respuesta valiosa para compliance.

## Dónde está la heterogeneidad

- **De datos (entity linking):** proveedor ↔ LEI de GLEIF, por nombre normalizado (sin «Inc.», «LLC», «Corp.») y estado; proveedor o grupo ↔ entrada de la Lista Consolidada, por nombre y alias; grupo ↔ Wikidata, por LEI.
- **De esquema:** el mismo concepto en columnas distintas, como `recipient_uei` y `parent_uei` en USAspending o `lei` en GLEIF y `P1278` en Wikidata.
- **Jerarquías:** grupo → filiales (USAspending y GLEIF) y sector → subsectores (NAICS), precalculadas como `mesh.ancestor`.

## Arquitectura

La misma que oncología:
- **Datos:** el mismo Postgres, con esquemas nuevos (`usaspending`, `gleif`, `csl`, `naics`).
- **Capa semántica:** un segundo Ontop con su propia ontología y su propio archivo de mapeos. Ontop lee un solo archivo de mapeos, y así cada dominio queda separado.
- **App:** un selector de dominio. Las pestañas, los dos modos y la evidencia son los mismos.

## Fases

| Fase | Qué | Checkpoint |
|---|---|---|
| P0 · Datos ✅ | Cargadores de USAspending (contratos y matrices), GLEIF, Lista Consolidada y NAICS | Conteos por fuente |
| P1 · Preguntas y diccionario | Las 8 preguntas, la ontología y sus SPARQL | Las 8 responden contra el segundo Ontop |
| P2 · Enlaces | Proveedor ↔ LEI, proveedor ↔ lista, grupo ↔ Wikidata, con su evidencia; revisión de una muestra | Precisión medida |
| P3 · Evaluación | Sin Rastro (SQL directo) contra con Rastro, consistencia y cambio, igual que en oncología | Las tres pruebas con números |
| P4 · App | El selector de dominio, las preguntas en palabras simples y la evidencia | Demo sin terminal |
| P5 · Demo | Diapositivas y guion, con un segundo ejemplo de punta a punta | Alguien de ventas la da con el guion |

Esfuerzo estimado: parecido al de las fases 0 a 3 de oncología, con la ventaja de reusar todo lo aprendido.

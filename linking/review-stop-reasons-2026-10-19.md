# Revisión de los motivos de detención — 19 oct 2026

Las reglas de `linking/stop_reasons.sql` clasifican el motivo que escribió cada sponsor (12.611 ensayos detenidos con motivo escrito). Un ensayo puede tener varios motivos. La revisión la hizo un asistente de IA (Claude Code), leyendo cada texto; falta que la confirme una persona (`docs/verificacion-humana.md`).

## Cómo se midió

Tres controles, en orden:

1. **Los 26 ensayos de la pregunta sobre textos**, clasificados antes a mano: con la primera versión de las reglas, coincidían 23 de 26. Las reglas se ajustaron con esos casos, así que este número es optimista.
2. **Primera muestra al azar de 50** (sin esos 26): 38 de los 42 motivos asignados eran correctos (**90 %**), y 10 ensayos con un motivo reconocible quedaban como «otro» («terminated by the Sponsor», «benefit-risk», «no patient enter this study»). Se sumaron esas reglas.
3. **Segunda muestra al azar de 50**, independiente de las anteriores:

| | Resultado |
|---|---|
| Motivos asignados correctos | **45 de 49 (92 %)** |
| Ensayos con al menos un motivo correcto | **42 de 50 (84 %)** |
| Ensayos que quedaron como «otro» teniendo un motivo reconocible | 7 |

Los errores de la segunda muestra son motivos de más: «Enrollment was stopped based on the DMC's recommendation» también como falta de pacientes; «seriously impacted by COVID» como seguridad. También encontró un error de las reglas: la limpieza de negaciones borraba «did not meet efficacy goals». Se corrigió (las negaciones de eficacia se sacan solo en la forma «not related / due / driven… to efficacy») y se sumaron las reglas de los 7 que faltaban. Ese ajuste no se volvió a medir con una tercera muestra.

## Qué quiere decir

- Cuando Rastro dice que un ensayo se detuvo por un motivo, acierta 9 de cada 10 veces en estas muestras.
- Alrededor de 2 de cada 10 ensayos quedan como «otro»: textos sin motivo («Study aborted», «Trial not initiated») o formas que las reglas todavía no cubren. Se ven en la evidencia, con su texto.
- Cada motivo guarda su evidencia: la parte del texto que coincidió y la regla.

## Para repetir la muestra

```sql
SELECT setseed(0.77);
WITH t AS (SELECT nct_id, string_agg(reason_id, ',' ORDER BY reason_id) AS motivos
           FROM linking.trial_stop_reason GROUP BY nct_id)
SELECT t.nct_id, t.motivos, s.why_stopped
FROM t JOIN aact.studies s USING (nct_id)
ORDER BY random() LIMIT 50;
```

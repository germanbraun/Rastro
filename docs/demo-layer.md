# Rastro Layer · recorrido breve

Abrir **Demo**, primer momento, o **Preguntar → primera pregunta → Responder**.

1. **La respuesta** (slide 5). «Cuánto le corresponde a cada empresa según su participación registrada. Es distinto de cuánto declara como operadora».
2. **Las conexiones** (slide 6). Activar **¿Por qué este número?**, elegir **CHEVRON** y **LOMA CAMPANA**. «La producción de los pozos se conecta con los socios de la misma concesión. Su parte es producción × participación; el total suma todas sus concesiones».
3. **La evidencia** (slide 7). Abrir **Ver los registros originales** y **Ver cómo se conectaron los nombres**. «El texto del mapa conserva el nombre original; el enlace apunta a una empresa compartida y dice con qué regla se unió». Mostrar que la confirmación humana sigue pendiente cuando así lo dice la evidencia.

El mensaje: **las fuentes se traducen al mismo vocabulario y las entidades se conectan una vez; las preguntas reutilizan esas definiciones**. SQL sobre los mismos enlaces también puede obtener el resultado. No prometer mayor precisión por usar RDF.

Opcional: abrir **Comparar producción operada y participación** y **Ver todas las concesiones de esta empresa**. La tabla de respuesta también muestra el gas que le corresponde, en miles de m³; no hace falta activar la vista técnica.

Para un perfil técnico: activar **Ver detalles técnicos** y abrir los identificadores y consultas. Para una persona de negocio: mantenerlos cerrados.

La app consulta los datos actuales. Las slides se generan con `python docs/slides/layer_story.py` a partir de la instantánea `docs/experiments/layer-answer/chevron.json`; después actualizar los pies y ejecutar `python docs/slides/build.py`. Los volúmenes de las slides son una instantánea, no resultados independientes de exactitud.

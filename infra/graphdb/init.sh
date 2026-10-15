#!/bin/sh
# Espera a GraphDB y crea el repositorio "rastro" si no existe.
set -eu
GDB=http://graphdb:7200

echo "Esperando a GraphDB..."
i=0
until curl -sf "$GDB/rest/repositories" >/dev/null; do
  i=$((i + 1))
  [ "$i" -gt 120 ] && { echo "GraphDB no respondió a tiempo"; exit 1; }
  sleep 2
done

if curl -sf "$GDB/rest/repositories/rastro" >/dev/null; then
  echo "El repositorio rastro ya existe"
else
  curl -sf -X POST "$GDB/rest/repositories" -F "config=@/config/repo-config.ttl"
  echo "Repositorio rastro creado"
fi

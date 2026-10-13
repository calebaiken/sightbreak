#!/usr/bin/env bash
set -euo pipefail
# Local development only; loopback port, dedicated volume, fictional data.
image='postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3'
if docker container inspect sightbreak-postgres >/dev/null 2>&1; then
  docker start sightbreak-postgres >/dev/null
else
  docker run -d --name sightbreak-postgres -p 127.0.0.1:55432:5432 \
    -e POSTGRES_USER=sightbreak -e POSTGRES_PASSWORD=sightbreak_local_only \
    -e POSTGRES_DB=sightbreak -v sightbreak-postgres:/var/lib/postgresql/data "$image"
fi
for attempt in {1..30}; do
  if docker exec sightbreak-postgres pg_isready -U sightbreak -d sightbreak >/dev/null; then exit 0; fi
  sleep 1
done
exit 1

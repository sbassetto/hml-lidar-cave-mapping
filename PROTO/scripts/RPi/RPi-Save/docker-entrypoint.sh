#!/usr/bin/env bash
set -e
echo "[entrypoint] default routes:"
ip route show default
exec "$@"

#!/bin/sh
set -eu
: "${SHARED_DB_URL:?SHARED_DB_URL must name the shared CI database}"
curl -X DELETE "${SHARED_DB_URL}/test-data"

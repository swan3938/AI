#!/usr/bin/env bash
set -e
mkdir -p bluewow-activation/backend/app/data/uploads
cp -n bluewow-activation/backend/config.example.env bluewow-activation/backend/.env || true
echo "ready"

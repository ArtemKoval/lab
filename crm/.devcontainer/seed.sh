#!/usr/bin/env bash
cd /workspaces/crm || exit 1
uv sync --quiet
CRM_DOMAIN=library uv run --no-sync python validate.py library
CRM_DOMAIN=library uv run --no-sync python -m backend.seed

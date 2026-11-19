#!/usr/bin/env bash
cd /workspaces/crm || exit 1
pkill -f "vite dashboard" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f spawn_main 2>/dev/null || true
pkill -f concurrently 2>/dev/null || true
pkill -f auth/server.mjs 2>/dev/null || true
sleep 1
[ -f .env ] || cp .env.example .env 2>/dev/null || touch .env
BASE=$(hostname -i | awk '{print $1}')
CRM_DOMAIN=library CRM_API="http:$BASE:8000"   VITE_AUTH_URL="http:$BASE:8004" AUTH_URL="http://localhost:8004"   AUTH_DEV_PASSWORD=crm-dev HOST=0.0.0.0 nohup npm run dev >/tmp/crm-dev.log 2>&1 &

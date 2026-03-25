#!/usr/bin/env bash
# Greenfield bootstrap: compose up (optional), wait for health, trigger fetch + optional I-O/concentration + train.
# Privileged calls use TRAINING_TOKEN (recommended) or JWT from POST /api/auth/token.
#
# Usage:
#   ./scripts/first-time-deploy.sh [--dry-run] [--skip-up] [--skip-fetch] [--skip-train] [--fetch-io] [--fetch-concentration]
# Env:
#   COMPOSE_FILE   default: docker-compose.prod.yml
#   API_BASE       default: http://127.0.0.1  (via Caddy :80 in prod compose)
#   TRAINING_TOKEN required for POST triggers unless you use --dry-run
#   COMPOSE_ENV_FILE  optional path passed as docker compose --env-file

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
API_BASE="${API_BASE:-http://127.0.0.1}"
DRY_RUN=0
SKIP_UP=0
SKIP_FETCH=0
SKIP_TRAIN=0
FETCH_IO=0
FETCH_CONC=0

while [[ $# -gt 0 ]]; do
	case "$1" in
	--dry-run) DRY_RUN=1 ;;
	--skip-up) SKIP_UP=1 ;;
	--skip-fetch) SKIP_FETCH=1 ;;
	--skip-train) SKIP_TRAIN=1 ;;
	--fetch-io) FETCH_IO=1 ;;
	--fetch-concentration) FETCH_CONC=1 ;;
	-h | --help)
		echo "Usage: $0 [--dry-run] [--skip-up] [--skip-fetch] [--skip-train] [--fetch-io] [--fetch-concentration]"
		echo "Env: COMPOSE_FILE COMPOSE_ENV_FILE API_BASE TRAINING_TOKEN POSTGRES_PASSWORD REDIS_PASSWORD (for compose)"
		exit 0
		;;
	*)
		echo "Unknown option: $1" >&2
		exit 1
		;;
	esac
	shift
done

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "Missing required command: $1" >&2
		exit 1
	}
}

run_curl() {
	if [[ "$DRY_RUN" -eq 1 ]]; then
		printf '[dry-run] curl'; printf ' %q' "$@"; printf '\n'
		return 0
	fi
	curl "$@"
}

auth_header() {
	if [[ "$DRY_RUN" -eq 1 ]]; then
		printf 'Authorization: Bearer <TRAINING_TOKEN>'
		return 0
	fi
	if [[ -z "${TRAINING_TOKEN:-}" ]]; then
		echo "TRAINING_TOKEN is not set (required for automated POST /api/... triggers)." >&2
		echo "Generate: python -c \"import secrets; print(secrets.token_urlsafe(48))\"" >&2
		exit 1
	fi
	printf 'Authorization: Bearer %s' "$TRAINING_TOKEN"
}

require_cmd docker
docker compose version >/dev/null 2>&1 || {
	echo "Docker Compose V2 is required (docker compose)." >&2
	exit 1
}

if [[ "$SKIP_UP" -eq 0 ]]; then
	compose_cmd=(docker compose -f "$COMPOSE_FILE")
	[[ -n "${COMPOSE_ENV_FILE:-}" ]] && compose_cmd+=(--env-file "$COMPOSE_ENV_FILE")
	if [[ "$DRY_RUN" -eq 1 ]]; then
		printf '[dry-run]'; printf ' %q' "${compose_cmd[@]}"; printf ' up -d --build\n'
	else
		"${compose_cmd[@]}" up -d --build
	fi
fi

echo "Waiting for $API_BASE/health ..."
for _ in $(seq 1 120); do
	if [[ "$DRY_RUN" -eq 1 ]]; then
		break
	fi
	if curl -fsS --max-time 5 "$API_BASE/health" >/dev/null 2>&1; then
		echo "Backend healthy."
		break
	fi
	sleep 2
done

if [[ "$DRY_RUN" -ne 1 ]] && ! curl -fsS --max-time 5 "$API_BASE/health" >/dev/null 2>&1; then
	echo "Timed out waiting for health at $API_BASE/health" >&2
	exit 1
fi

if [[ "$SKIP_FETCH" -eq 0 ]]; then
	AH=$(auth_header)
	run_curl -fsS -X POST "$API_BASE/api/data/fetch" \
		-H "$AH" \
		-H "Accept: application/json"
	echo
	echo "Macro fetch enqueued (Celery). Check worker logs if it does not progress."
fi

if [[ "$FETCH_IO" -eq 1 ]]; then
	AH=$(auth_header)
	run_curl -fsS -X POST "$API_BASE/api/data/fetch-io" \
		-H "$AH" \
		-H "Accept: application/json"
	echo
	echo "I-O fetch enqueued."
fi

if [[ "$FETCH_CONC" -eq 1 ]]; then
	AH=$(auth_header)
	run_curl -fsS -X POST "$API_BASE/api/data/fetch-concentration" \
		-H "$AH" \
		-H "Accept: application/json"
	echo
	echo "Concentration fetch enqueued."
fi

if [[ "$SKIP_TRAIN" -eq 0 ]]; then
	AH=$(auth_header)
	run_curl -fsS -X POST "$API_BASE/api/forecasting/train" \
		-H "$AH" \
		-H "Accept: application/json"
	echo
	echo "Training enqueued. Polling /api/forecasting/training/log (first run may take a long time) ..."
	if [[ "$DRY_RUN" -eq 1 ]]; then
		exit 0
	fi
	for _ in $(seq 1 720); do
		st=1
		json=$(curl -fsS --max-time 30 "$API_BASE/api/forecasting/training/log") || json='{"entries":[]}'
		if command -v python3 >/dev/null 2>&1; then
			set +e
			python3 -c "
import json, sys
try:
    entries = json.loads(sys.argv[1]).get('entries', [])
except json.JSONDecodeError:
    sys.exit(1)
for e in entries:
    if e.get('name') == 'pipeline':
        s = e.get('status')
        if s == 'complete':
            sys.exit(0)
        if s == 'error':
            sys.exit(2)
sys.exit(1)
" "$json"
			st=$?
			set -e
		else
			if echo "$json" | grep -q '"name"[[:space:]]*:[[:space:]]*"pipeline"'; then
				if echo "$json" | grep -q '"status"[[:space:]]*:[[:space:]]*"complete"'; then
					st=0
				elif echo "$json" | grep -q '"status"[[:space:]]*:[[:space:]]*"error"'; then
					st=2
				else
					st=1
				fi
			else
				st=1
			fi
		fi
		if [[ "$st" -eq 0 ]]; then
			echo "Training pipeline reported complete."
			exit 0
		fi
		if [[ "$st" -eq 2 ]]; then
			echo "Training pipeline reported error. Last log response:" >&2
			echo "$json" >&2
			exit 1
		fi
		sleep 30
	done
	echo "Timed out waiting for training completion (adjust script loop or check logs)." >&2
	exit 1
fi

echo "Done (training skipped or completed path not executed)."

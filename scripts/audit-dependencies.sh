#!/usr/bin/env bash
# Audit Python dependencies for known vulnerabilities.
#
# Prerequisites: pip install pip-audit safety
# Usage: bash scripts/audit-dependencies.sh

set -euo pipefail

echo "=== ECPM Dependency Audit ==="
echo ""

echo "--- pip-audit ---"
if command -v pip-audit &>/dev/null; then
    pip-audit --strict --desc on 2>&1 || true
else
    echo "SKIP: pip-audit not installed (pip install pip-audit)"
fi

echo ""
echo "--- safety check ---"
if command -v safety &>/dev/null; then
    safety check 2>&1 || true
else
    echo "SKIP: safety not installed (pip install safety)"
fi

echo ""
echo "--- npm audit (frontend) ---"
if [ -d "frontend" ]; then
    (cd frontend && npm audit --production 2>&1 || true)
else
    echo "SKIP: frontend directory not found"
fi

echo ""
echo "=== Audit Complete ==="

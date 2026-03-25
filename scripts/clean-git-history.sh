#!/usr/bin/env bash
# Remove .env files from git history.
#
# WARNING: This rewrites history. Coordinate with all contributors before running.
#   - All team members must re-clone after this runs.
#   - Force push required (git push --force --all && git push --force --tags).
#
# Prerequisites: pip install git-filter-repo
#
# Usage: bash scripts/clean-git-history.sh

set -euo pipefail

echo "=== ECPM Git History Cleanup ==="
echo ""
echo "This script will PERMANENTLY remove .env files from git history."
echo "All team members will need to re-clone the repository after this."
echo ""
read -rp "Are you sure? (type YES to continue): " confirm
if [[ "$confirm" != "YES" ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Step 1: Removing .env files from history..."
git filter-repo --invert-paths --path .env --path .env.local --path .env.production --force

echo ""
echo "Step 2: Running garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "=== Done ==="
echo ""
echo "Next steps (MANUAL):"
echo "  1. git push --force --all && git push --force --tags"
echo "  2. Notify all contributors to re-clone"
echo "  3. Revoke and rotate API keys on FRED, BEA, and Census portals"
echo "  4. Rotate the Postgres and Redis passwords in .env"

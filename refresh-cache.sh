#!/bin/sh
# Quick script to refresh the indicator cache

echo "Refreshing ECPM indicator cache..."
curl -X POST http://localhost:8000/api/cache/refresh | jq '.'

#!/bin/bash
set -e

echo "🌱 Running seeds.py to create demo user and data..."
python seed.py

echo "✅ Seeds completed! Starting Gunicorn..."
gunicorn wsgi:app

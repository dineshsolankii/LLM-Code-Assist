#!/bin/bash
set -e
echo "=== LLM Code Assist Entrypoint ==="

# ── Helper: normalize DATABASE_URL for psycopg2 ─────────────────────────────
# psycopg2 requires "postgresql://" not "postgres://"
normalize_db_url() {
    echo "${DATABASE_URL}" | sed 's|^postgres://|postgresql://|'
}

# ── Wait for PostgreSQL ──────────────────────────────────────────────────────
echo "Waiting for PostgreSQL..."
DB_URL=$(normalize_db_url)
attempt=0
max=30
delay=2
while [ $attempt -lt $max ]; do
    if python -c "import psycopg2; psycopg2.connect('${DB_URL}').close()" 2>/dev/null; then
        echo "PostgreSQL ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "  PostgreSQL attempt ${attempt}/${max}, retrying in ${delay}s..."
    sleep $delay
    # Exponential backoff up to 10s
    delay=$(( delay < 10 ? delay + 1 : 10 ))
done

if [ $attempt -ge $max ]; then
    echo "ERROR: PostgreSQL did not become ready in time. Exiting."
    exit 1
fi

# ── Wait for Redis ───────────────────────────────────────────────────────────
echo "Waiting for Redis..."
REDIS_HOST=$(echo "${REDIS_URL:-redis://redis:6379/0}" | sed 's|redis://||' | cut -d: -f1)
REDIS_PORT=$(echo "${REDIS_URL:-redis://redis:6379/0}" | sed 's|redis://||' | cut -d: -f2 | cut -d/ -f1)
attempt=0
max=20
while [ $attempt -lt $max ]; do
    if python -c "import redis; redis.Redis(host='${REDIS_HOST}', port=${REDIS_PORT}).ping()" 2>/dev/null; then
        echo "Redis ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Redis attempt ${attempt}/${max}, retrying in 2s..."
    sleep 2
done

if [ $attempt -ge $max ]; then
    echo "WARNING: Redis did not respond. Continuing anyway..."
fi

# ── Initialize database tables ───────────────────────────────────────────────
echo "Initializing database..."
python -c "
from app import create_app
app = create_app('production')
with app.app_context():
    from app.extensions import db
    db.create_all()
    print('DB tables ready.')
" || echo "WARNING: DB init skipped (may already be initialized)"

# ── Pull Ollama model synchronously if needed ─────────────────────────────────
OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${OLLAMA_MODEL:-qwen2.5-coder:3b}"

echo "Checking Ollama at ${OLLAMA_URL}..."
if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    EXISTING=$(curl -sf "${OLLAMA_URL}/api/tags" | python -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print(' '.join(models))
" 2>/dev/null)

    # Check if our target model is already present
    MODEL_BASE=$(echo "${MODEL}" | cut -d: -f1)
    if echo "${EXISTING}" | grep -q "${MODEL_BASE}"; then
        echo "Model '${MODEL}' already available."
    else
        echo "Pulling model '${MODEL}' (this may take several minutes)..."
        # Synchronous pull — wait for completion
        if curl -sf "${OLLAMA_URL}/api/pull" \
            -H 'Content-Type: application/json' \
            -d "{\"name\":\"${MODEL}\",\"stream\":false}" \
            --max-time 1800 >/dev/null 2>&1; then
            echo "Model '${MODEL}' ready."
        else
            echo "WARNING: Model pull failed or timed out. App will start anyway."
        fi
    fi
else
    echo "WARNING: Ollama not reachable at ${OLLAMA_URL}. Model not pulled."
fi

echo "Starting application..."
exec "$@"

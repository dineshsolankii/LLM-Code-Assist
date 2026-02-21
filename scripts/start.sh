#!/usr/bin/env bash
# ============================================================
# LLM Code Assist — Local Development Startup Script
# Handles: OS detection, system resources, Ollama install,
# model selection (Apple Silicon aware), PostgreSQL, Redis,
# Python venv, DB init, Celery workers, Flask app
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; PURPLE='\033[0;35m'; NC='\033[0m'
BOLD='\033[1m'

log()    { echo -e "${GREEN}${BOLD}[✓]${NC} $1"; }
warn()   { echo -e "${YELLOW}${BOLD}[!]${NC} $1"; }
error()  { echo -e "${RED}${BOLD}[✗]${NC} $1" >&2; }
info()   { echo -e "${BLUE}${BOLD}[i]${NC} $1"; }
header() { echo -e "\n${CYAN}${BOLD}━━━ $1 ━━━${NC}\n"; }
step()   { echo -e "${PURPLE}${BOLD}  →${NC} $1"; }

# Parse flags
SKIP_MODEL=${SKIP_MODEL:-false}
DEV_MODE=${DEV_MODE:-true}

# ─── OS & Package Manager Detection ────────────────────────
detect_os() {
    header "System Detection"
    ARCH=$(uname -m)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
        IS_APPLE_SILICON=false
        [[ "$ARCH" == "arm64" ]] && IS_APPLE_SILICON=true
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"; PKG_MANAGER="apt"
        IS_APPLE_SILICON=false
    elif [[ -f /etc/redhat-release ]]; then
        OS="redhat"; PKG_MANAGER="dnf"
        IS_APPLE_SILICON=false
    elif [[ -f /etc/arch-release ]]; then
        OS="arch"; PKG_MANAGER="pacman"
        IS_APPLE_SILICON=false
    else
        OS="unknown"; PKG_MANAGER="unknown"
        IS_APPLE_SILICON=false
    fi

    if $IS_APPLE_SILICON; then
        log "Apple Silicon Mac detected (${ARCH})"
    else
        log "OS: ${OS} (${ARCH}) | Package manager: ${PKG_MANAGER}"
    fi
}

# ─── System Resources ───────────────────────────────────────
detect_resources() {
    header "System Resources"

    if [[ "$OS" == "macos" ]]; then
        TOTAL_RAM_GB=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f", $1/1024/1024/1024}' || echo 8)
    else
        TOTAL_RAM_GB=$(awk '/^MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 8)
    fi

    GPU_VRAM_GB=0
    if command -v nvidia-smi &>/dev/null; then
        GPU_VRAM_GB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null \
            | head -1 | awk '{printf "%.0f", $1/1024}' || echo 0)
        [[ "$GPU_VRAM_GB" -gt 0 ]] && log "NVIDIA GPU: ${GPU_VRAM_GB}GB VRAM"
    fi

    log "Total RAM: ${TOTAL_RAM_GB}GB"
    [[ $GPU_VRAM_GB -gt 0 ]] && log "GPU VRAM: ${GPU_VRAM_GB}GB"
}

# ─── Smart Model Selection ──────────────────────────────────
select_model() {
    header "Model Selection"

    if $IS_APPLE_SILICON; then
        # On Apple Silicon, Ollama uses unified memory but is capped at ~75%
        AVAIL=$(awk "BEGIN{printf \"%.0f\", ${TOTAL_RAM_GB} * 0.75}")
        step "Apple Silicon: ${TOTAL_RAM_GB}GB unified memory → ${AVAIL}GB effective for LLM"
    else
        # Use whichever is larger: RAM or GPU VRAM
        if [[ $GPU_VRAM_GB -gt $TOTAL_RAM_GB ]]; then
            AVAIL=$GPU_VRAM_GB
            step "Using GPU VRAM: ${AVAIL}GB"
        else
            AVAIL=$TOTAL_RAM_GB
            step "Using system RAM: ${AVAIL}GB"
        fi
    fi

    # Model thresholds (Ollama quantized sizes)
    if   [ "$AVAIL" -ge 30 ]; then MODEL="qwen2.5-coder:32b"
    elif [ "$AVAIL" -ge 14 ]; then MODEL="qwen2.5-coder:14b"
    elif [ "$AVAIL" -ge 7  ]; then MODEL="qwen2.5-coder:7b"
    elif [ "$AVAIL" -ge 4  ]; then MODEL="qwen2.5-coder:3b"
    else                            MODEL="qwen2.5-coder:1.5b"
    fi

    log "Selected model: ${BOLD}$MODEL${NC} (${AVAIL}GB effective)"
}

# ─── Ollama Installation ────────────────────────────────────
install_ollama() {
    header "Ollama Setup"

    if command -v ollama &>/dev/null; then
        OLLAMA_VERSION=$(ollama --version 2>/dev/null | head -1 || echo "unknown")
        log "Ollama already installed: $OLLAMA_VERSION"
        return 0
    fi

    info "Installing Ollama..."
    if curl -fsSL https://ollama.ai/install.sh | sh; then
        log "Ollama installed successfully"
    else
        error "Ollama installation failed. Install manually: https://ollama.ai"
        exit 1
    fi
}

start_ollama() {
    if curl -sf http://localhost:11434/api/tags &>/dev/null; then
        log "Ollama already running"
        return 0
    fi

    info "Starting Ollama service..."
    if [[ "$OS" == "macos" ]]; then
        nohup ollama serve > /tmp/ollama.log 2>&1 &
    elif command -v systemctl &>/dev/null && systemctl list-unit-files ollama.service &>/dev/null; then
        sudo systemctl start ollama 2>/dev/null || \
            nohup ollama serve > /tmp/ollama.log 2>&1 &
    else
        nohup ollama serve > /tmp/ollama.log 2>&1 &
    fi

    # Wait up to 30s for Ollama to start
    for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/api/tags &>/dev/null; then
            log "Ollama started successfully"
            return 0
        fi
        sleep 1
    done
    warn "Ollama may not have started. Check /tmp/ollama.log"
}

pull_model() {
    header "Model Download"

    if [ "$SKIP_MODEL" = "true" ]; then
        warn "Skipping model download (SKIP_MODEL=true)"
        return 0
    fi

    # Check if model already available
    if ollama list 2>/dev/null | grep -q "^${MODEL%%:*}"; then
        log "Model $MODEL already available locally"
        return 0
    fi

    info "Downloading $MODEL (this may take several minutes)..."
    info "  Size guide: 1.5b~1GB, 3b~2GB, 7b~4.7GB, 14b~9GB, 32b~20GB"
    if ollama pull "$MODEL"; then
        log "Model $MODEL downloaded and ready"
    else
        warn "Failed to download $MODEL — trying smaller model..."
        MODEL="qwen2.5-coder:1.5b"
        ollama pull "$MODEL" || warn "Could not download fallback model either"
    fi
}

# ─── Local Services (PostgreSQL + Redis) ────────────────────
start_local_services() {
    header "Starting Local Services"

    case "$OS" in
        macos)
            # PostgreSQL
            if brew services list 2>/dev/null | grep -qE "postgresql.*started"; then
                log "PostgreSQL already running"
            else
                step "Starting PostgreSQL..."
                brew services start postgresql@16 2>/dev/null || \
                brew services start postgresql    2>/dev/null || \
                warn "Start PostgreSQL manually: brew services start postgresql@16"
            fi

            # Redis
            if brew services list 2>/dev/null | grep -qE "redis.*started"; then
                log "Redis already running"
            else
                step "Starting Redis..."
                brew services start redis 2>/dev/null || warn "Start Redis manually: brew services start redis"
            fi
            ;;
        debian|ubuntu)
            sudo systemctl start postgresql 2>/dev/null && log "PostgreSQL started" || warn "Start: sudo systemctl start postgresql"
            sudo systemctl start redis-server 2>/dev/null && log "Redis started" || warn "Start: sudo systemctl start redis-server"
            ;;
        redhat)
            sudo systemctl start postgresql 2>/dev/null && log "PostgreSQL started" || warn "Start: sudo systemctl start postgresql"
            sudo systemctl start redis 2>/dev/null && log "Redis started" || warn "Start: sudo systemctl start redis"
            ;;
        arch)
            sudo systemctl start postgresql 2>/dev/null && log "PostgreSQL started" || true
            sudo systemctl start redis 2>/dev/null && log "Redis started" || true
            ;;
        *)
            warn "Unknown OS — start PostgreSQL and Redis manually"
            ;;
    esac
}

wait_for_postgres() {
    info "Waiting for PostgreSQL..."
    local max=20 attempt=1 delay=2

    while [ $attempt -le $max ]; do
        if pg_isready -h localhost -p 5432 &>/dev/null 2>&1 || \
           python3 -c "import psycopg2; psycopg2.connect(host='localhost',dbname='postgres').close()" &>/dev/null 2>&1; then
            log "PostgreSQL is ready"
            return 0
        fi
        step "Waiting for PostgreSQL (attempt ${attempt}/${max}, retry in ${delay}s)..."
        sleep $delay
        attempt=$((attempt + 1))
        [ $delay -lt 16 ] && delay=$((delay * 2))
    done

    warn "PostgreSQL not responding — will try SQLite fallback"
}

wait_for_redis() {
    info "Waiting for Redis..."
    for i in $(seq 1 15); do
        if redis-cli ping &>/dev/null 2>&1; then
            log "Redis is ready"
            return 0
        fi
        sleep 1
    done
    warn "Redis not responding — sessions will use filesystem fallback"
}

# ─── .env File Generation ───────────────────────────────────
generate_env() {
    header "Environment Configuration"
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

    if [ -f "$PROJECT_DIR/.env" ]; then
        log ".env file exists"
        return 0
    fi

    warn ".env not found — generating with defaults..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "dev-secret-key-change-me")

    cat > "$PROJECT_DIR/.env" << ENVEOF
# LLM Code Assist — Environment Configuration
# Generated by start.sh on $(date)
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=development

# Set to 'false' and add Google OAuth credentials for production
SKIP_AUTH=true

# Database (PostgreSQL)
POSTGRES_USER=llm_user
POSTGRES_PASSWORD=llm_password
DATABASE_URL=postgresql://llm_user:llm_password@localhost:5432/llm_code_assist

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/3

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Google OAuth (set SKIP_AUTH=false and fill in for production)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Logging
LOG_LEVEL=INFO
ENVEOF

    log ".env created at $PROJECT_DIR/.env"
    warn "Review $PROJECT_DIR/.env and set SKIP_AUTH=false with Google OAuth for production"
}

# ─── Python Environment ─────────────────────────────────────
setup_python() {
    header "Python Environment"
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_DIR"

    if [ ! -d "venv" ]; then
        info "Creating virtual environment..."
        python3 -m venv venv
    fi
    # shellcheck disable=SC1091
    source venv/bin/activate
    log "Virtual environment activated"

    info "Upgrading pip and installing dependencies..."
    pip install --quiet --upgrade pip setuptools wheel
    pip install --quiet -r requirements.txt
    log "All dependencies installed"

    # Load .env
    if [ -f ".env" ]; then
        set -o allexport
        # shellcheck disable=SC1091
        source .env
        set +o allexport
        log ".env loaded"
    fi
}

# ─── Database Initialization ────────────────────────────────
init_database() {
    header "Database Initialization"

    if python -c "
import os, sys
os.environ.setdefault('FLASK_ENV','development')
try:
    from app import create_app
    from app.extensions import db
    app = create_app('development')
    with app.app_context():
        db.create_all()
        print('Database tables created/verified')
except Exception as e:
    print(f'Warning: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1; then
        log "Database initialized"
    else
        warn "DB initialization skipped — ensure PostgreSQL is running and DATABASE_URL is correct"
    fi
}

# ─── Launch Application ─────────────────────────────────────
start_app() {
    header "Starting LLM Code Assist"

    echo ""
    echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║         LLM Code Assist — Starting Up          ║${NC}"
    echo -e "${CYAN}${BOLD}╠════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}${BOLD}║${NC}  %-44s${CYAN}${BOLD}║${NC}\n" "🌐 Web UI:   http://localhost:8001"
    printf "${CYAN}${BOLD}║${NC}  %-44s${CYAN}${BOLD}║${NC}\n" "🤖 Ollama:   http://localhost:11434"
    printf "${CYAN}${BOLD}║${NC}  %-44s${CYAN}${BOLD}║${NC}\n" "📦 Model:    $MODEL"
    printf "${CYAN}${BOLD}║${NC}  %-44s${CYAN}${BOLD}║${NC}\n" "🔑 Auth:     ${SKIP_AUTH:-false}"
    echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════╝${NC}"
    echo ""

    # Start Celery worker (background)
    celery -A celery_app worker --loglevel=warning --concurrency=2 \
        > /tmp/celery-worker.log 2>&1 &
    WORKER_PID=$!
    log "Celery worker started (PID: $WORKER_PID)"

    # Start Celery beat (background)
    celery -A celery_app beat --loglevel=warning \
        > /tmp/celery-beat.log 2>&1 &
    BEAT_PID=$!
    log "Celery beat started (PID: $BEAT_PID)"

    # Graceful shutdown on Ctrl+C or exit
    cleanup() {
        echo ""
        info "Shutting down..."
        kill "$WORKER_PID" "$BEAT_PID" 2>/dev/null || true
        wait "$WORKER_PID" "$BEAT_PID" 2>/dev/null || true
        log "Shutdown complete"
    }
    trap cleanup EXIT INT TERM

    # Start Flask app
    python run.py
}

# ─── Main ───────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "   ██████╗ ██████╗ ██████╗ ███████╗"
    echo "  ██╔════╝██╔═══██╗██╔══██╗██╔════╝"
    echo "  ██║     ██║   ██║██║  ██║█████╗  "
    echo "  ██║     ██║   ██║██║  ██║██╔══╝  "
    echo "  ╚██████╗╚██████╔╝██████╔╝███████╗"
    echo "   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝"
    echo "       LLM Code Assist v2.0"
    echo -e "${NC}"

    detect_os
    detect_resources
    select_model
    generate_env
    install_ollama
    start_ollama
    pull_model
    start_local_services
    wait_for_postgres
    wait_for_redis
    setup_python
    init_database
    start_app
}

main "$@"

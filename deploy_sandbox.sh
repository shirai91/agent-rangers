#!/bin/bash
#
# Agent Rangers Sandbox Deployment Script
# Usage: ./deploy_sandbox.sh [command] [options]
#
# Commands:
#   deploy    - Build and deploy to sandbox
#   start     - Start sandbox services
#   stop      - Stop sandbox services
#   restart   - Restart sandbox services
#   status    - Show sandbox status
#   logs      - Tail sandbox logs
#   rollback  - Rollback to previous version
#   init      - Initialize sandbox environment (first time setup)
#

set -e

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="/home/shirai91/deployments/agent-rangers"
BACKUP_DIR="${DEPLOY_ROOT}/backups"
LOGS_DIR="${DEPLOY_ROOT}/logs"
PIDS_DIR="${DEPLOY_ROOT}/pids"

# Ports
BACKEND_PORT=8100
FRONTEND_PORT=5174

# Database
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="agent_rangers_sandbox"
DB_USER="soloboy"
DB_PASSWORD="eW880dRvPhVRIBi3IajQRt77"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_pid() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "$pid"
            return 0
        fi
    fi
    echo ""
    return 1
}

# =============================================================================
# Commands
# =============================================================================

cmd_init() {
    log_info "Initializing sandbox environment..."
    
    # Create directories
    mkdir -p "${DEPLOY_ROOT}"/{backend,frontend,logs,pids,backups}
    
    # Create sandbox .env file
    cat > "${DEPLOY_ROOT}/backend/.env" << EOF
# Sandbox Environment
ENV=sandbox
DEBUG=False

# Database (sandbox)
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis (shared)
REDIS_URL=redis://localhost:6380

# CORS (sandbox ports)
CORS_ORIGINS=http://localhost:${FRONTEND_PORT},http://192.168.1.225:${FRONTEND_PORT}

# AI Provider
AI_PROVIDER_MODE=oauth
CLAUDE_CONFIG_DIR=/home/shirai91/.claude

# API
API_V1_PREFIX=/api
PROJECT_NAME=Agent Rangers API (Sandbox)
EOF

    # Create Python venv
    if [ ! -d "${DEPLOY_ROOT}/backend/venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv "${DEPLOY_ROOT}/backend/venv"
    fi
    
    log_success "Sandbox environment initialized!"
}

cmd_deploy() {
    local skip_tests=false
    local skip_build=false
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests) skip_tests=true; shift ;;
            --skip-build) skip_build=true; shift ;;
            *) shift ;;
        esac
    done
    
    log_info "Starting deployment to sandbox..."
    
    # Get current git info
    cd "$PROJECT_ROOT"
    local commit_hash=$(git rev-parse --short HEAD)
    local commit_msg=$(git log -1 --pretty=%B | head -1)
    local deploy_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    log_info "Deploying commit: ${commit_hash} - ${commit_msg}"
    
    # Run tests (optional)
    if [ "$skip_tests" = false ]; then
        log_info "Running tests..."
        # Add test command here if you have tests
        # cd backend && source venv/bin/activate && pytest
        log_warn "Tests skipped (not configured)"
    fi
    
    # Build frontend
    if [ "$skip_build" = false ]; then
        log_info "Building frontend..."
        cd "${PROJECT_ROOT}/frontend"
        
        # Update API URL for sandbox
        cat > .env.production << EOF
VITE_API_URL=http://192.168.1.225:${BACKEND_PORT}
VITE_WS_URL=ws://192.168.1.225:${BACKEND_PORT}
EOF
        
        npm install --silent
        npm run build
        log_success "Frontend built successfully"
    fi
    
    # Stop services
    cmd_stop 2>/dev/null || true
    
    # Backup current deployment
    if [ -d "${DEPLOY_ROOT}/backend/app" ]; then
        log_info "Backing up current deployment..."
        local backup_name="backup_$(date '+%Y%m%d_%H%M%S')"
        mkdir -p "${BACKUP_DIR}/${backup_name}"
        cp -r "${DEPLOY_ROOT}/backend/app" "${BACKUP_DIR}/${backup_name}/"
        cp -r "${DEPLOY_ROOT}/frontend" "${BACKUP_DIR}/${backup_name}/" 2>/dev/null || true
        [ -f "${DEPLOY_ROOT}/version.txt" ] && cp "${DEPLOY_ROOT}/version.txt" "${BACKUP_DIR}/${backup_name}/"
        
        # Keep only last 3 backups
        cd "${BACKUP_DIR}"
        ls -t | tail -n +4 | xargs -r rm -rf
        log_success "Backup created: ${backup_name}"
    fi
    
    # Copy backend
    log_info "Deploying backend..."
    rsync -av --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.env' \
        --exclude '.pytest_cache' \
        "${PROJECT_ROOT}/backend/" "${DEPLOY_ROOT}/backend/"
    
    # Copy frontend dist
    log_info "Deploying frontend..."
    rm -rf "${DEPLOY_ROOT}/frontend/dist"
    cp -r "${PROJECT_ROOT}/frontend/dist" "${DEPLOY_ROOT}/frontend/"
    
    # Install/update Python dependencies
    log_info "Installing Python dependencies..."
    source "${DEPLOY_ROOT}/backend/venv/bin/activate"
    pip install -q -r "${DEPLOY_ROOT}/backend/requirements.txt"
    deactivate
    
    # Run database migrations
    log_info "Running database migrations..."
    source "${DEPLOY_ROOT}/backend/venv/bin/activate"
    cd "${DEPLOY_ROOT}/backend"
    # Alembic migrations if configured
    # alembic upgrade head
    log_warn "Migrations skipped (run manually if needed)"
    deactivate
    
    # Save version info
    cat > "${DEPLOY_ROOT}/version.txt" << EOF
commit: ${commit_hash}
message: ${commit_msg}
deployed: ${deploy_time}
deployed_by: $(whoami)
EOF
    
    # Start services
    cmd_start
    
    # Health check
    sleep 3
    log_info "Running health check..."
    if curl -s "http://localhost:${BACKEND_PORT}/health" | grep -q "healthy"; then
        log_success "Backend health check passed!"
    else
        log_error "Backend health check failed!"
        exit 1
    fi
    
    log_success "Deployment completed successfully!"
    echo ""
    echo "  Backend:  http://192.168.1.225:${BACKEND_PORT}"
    echo "  Frontend: http://192.168.1.225:${FRONTEND_PORT}"
    echo ""
}

cmd_start() {
    log_info "Starting sandbox services..."
    
    # Ensure directories exist
    mkdir -p "${LOGS_DIR}" "${PIDS_DIR}"
    
    # Start backend
    local backend_pid=$(check_pid "${PIDS_DIR}/backend.pid")
    if [ -n "$backend_pid" ]; then
        log_warn "Backend already running (PID: ${backend_pid})"
    else
        log_info "Starting backend on port ${BACKEND_PORT}..."
        source "${DEPLOY_ROOT}/backend/venv/bin/activate"
        cd "${DEPLOY_ROOT}/backend"
        nohup uvicorn app.main:app \
            --host 0.0.0.0 \
            --port ${BACKEND_PORT} \
            > "${LOGS_DIR}/backend.log" 2>&1 &
        echo $! > "${PIDS_DIR}/backend.pid"
        deactivate
        log_success "Backend started (PID: $(cat ${PIDS_DIR}/backend.pid))"
    fi
    
    # Start frontend (serve static files)
    local frontend_pid=$(check_pid "${PIDS_DIR}/frontend.pid")
    if [ -n "$frontend_pid" ]; then
        log_warn "Frontend already running (PID: ${frontend_pid})"
    else
        log_info "Starting frontend on port ${FRONTEND_PORT}..."
        cd "${DEPLOY_ROOT}/frontend"
        nohup npx serve dist -l ${FRONTEND_PORT} \
            > "${LOGS_DIR}/frontend.log" 2>&1 &
        echo $! > "${PIDS_DIR}/frontend.pid"
        log_success "Frontend started (PID: $(cat ${PIDS_DIR}/frontend.pid))"
    fi
}

cmd_stop() {
    log_info "Stopping sandbox services..."
    
    # Stop backend
    local backend_pid=$(check_pid "${PIDS_DIR}/backend.pid")
    if [ -n "$backend_pid" ]; then
        kill "$backend_pid" 2>/dev/null || true
        rm -f "${PIDS_DIR}/backend.pid"
        log_success "Backend stopped"
    else
        log_warn "Backend not running"
    fi
    
    # Stop frontend
    local frontend_pid=$(check_pid "${PIDS_DIR}/frontend.pid")
    if [ -n "$frontend_pid" ]; then
        kill "$frontend_pid" 2>/dev/null || true
        rm -f "${PIDS_DIR}/frontend.pid"
        log_success "Frontend stopped"
    else
        log_warn "Frontend not running"
    fi
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo ""
    echo "=========================================="
    echo "  Agent Rangers Sandbox Status"
    echo "=========================================="
    echo ""
    
    # Version info
    if [ -f "${DEPLOY_ROOT}/version.txt" ]; then
        echo "Deployment:"
        cat "${DEPLOY_ROOT}/version.txt" | sed 's/^/  /'
        echo ""
    fi
    
    # Backend status
    local backend_pid=$(check_pid "${PIDS_DIR}/backend.pid")
    if [ -n "$backend_pid" ]; then
        echo -e "Backend:  ${GREEN}● Running${NC} (PID: ${backend_pid}, Port: ${BACKEND_PORT})"
        local health=$(curl -s "http://localhost:${BACKEND_PORT}/health" 2>/dev/null || echo "unreachable")
        echo "          Health: ${health}"
    else
        echo -e "Backend:  ${RED}○ Stopped${NC}"
    fi
    
    # Frontend status
    local frontend_pid=$(check_pid "${PIDS_DIR}/frontend.pid")
    if [ -n "$frontend_pid" ]; then
        echo -e "Frontend: ${GREEN}● Running${NC} (PID: ${frontend_pid}, Port: ${FRONTEND_PORT})"
    else
        echo -e "Frontend: ${RED}○ Stopped${NC}"
    fi
    
    echo ""
    echo "URLs:"
    echo "  Backend:  http://192.168.1.225:${BACKEND_PORT}"
    echo "  Frontend: http://192.168.1.225:${FRONTEND_PORT}"
    echo ""
}

cmd_logs() {
    local service="${1:-all}"
    
    case $service in
        backend)
            tail -f "${LOGS_DIR}/backend.log"
            ;;
        frontend)
            tail -f "${LOGS_DIR}/frontend.log"
            ;;
        all|*)
            tail -f "${LOGS_DIR}/backend.log" "${LOGS_DIR}/frontend.log"
            ;;
    esac
}

cmd_rollback() {
    log_info "Available backups:"
    ls -1t "${BACKUP_DIR}" 2>/dev/null || { log_error "No backups found"; exit 1; }
    
    echo ""
    read -p "Enter backup name to restore (or 'latest'): " backup_name
    
    if [ "$backup_name" = "latest" ]; then
        backup_name=$(ls -1t "${BACKUP_DIR}" | head -1)
    fi
    
    if [ ! -d "${BACKUP_DIR}/${backup_name}" ]; then
        log_error "Backup not found: ${backup_name}"
        exit 1
    fi
    
    log_info "Rolling back to: ${backup_name}"
    
    cmd_stop
    
    # Restore backend
    rm -rf "${DEPLOY_ROOT}/backend/app"
    cp -r "${BACKUP_DIR}/${backup_name}/app" "${DEPLOY_ROOT}/backend/"
    
    # Restore frontend
    if [ -d "${BACKUP_DIR}/${backup_name}/frontend" ]; then
        rm -rf "${DEPLOY_ROOT}/frontend"
        cp -r "${BACKUP_DIR}/${backup_name}/frontend" "${DEPLOY_ROOT}/"
    fi
    
    # Restore version
    [ -f "${BACKUP_DIR}/${backup_name}/version.txt" ] && \
        cp "${BACKUP_DIR}/${backup_name}/version.txt" "${DEPLOY_ROOT}/"
    
    cmd_start
    
    log_success "Rollback completed!"
}

cmd_help() {
    echo "Agent Rangers Sandbox Deployment Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  init          Initialize sandbox environment (first time)"
    echo "  deploy        Build and deploy to sandbox"
    echo "                  --skip-tests  Skip running tests"
    echo "                  --skip-build  Skip frontend build"
    echo "  start         Start sandbox services"
    echo "  stop          Stop sandbox services"
    echo "  restart       Restart sandbox services"
    echo "  status        Show sandbox status"
    echo "  logs [svc]    Tail logs (backend|frontend|all)"
    echo "  rollback      Rollback to previous version"
    echo "  help          Show this help"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

command="${1:-help}"
shift || true

case $command in
    init)     cmd_init "$@" ;;
    deploy)   cmd_deploy "$@" ;;
    start)    cmd_start "$@" ;;
    stop)     cmd_stop "$@" ;;
    restart)  cmd_restart "$@" ;;
    status)   cmd_status "$@" ;;
    logs)     cmd_logs "$@" ;;
    rollback) cmd_rollback "$@" ;;
    help|*)   cmd_help ;;
esac

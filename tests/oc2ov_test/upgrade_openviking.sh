#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/root/project/OpenViking"
BACKUP_DIR="/root/project/OpenViking_backup"
LOG_FILE="/var/log/openviking_upgrade.log"
MAX_RETRIES=3
RETRY_DELAY=10

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "OpenViking Upgrade Script Started"
log "========================================="

log "[1/7] Checking prerequisites..."
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: OpenViking directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

log "[2/7] Backing up current version..."
if [ -d "$BACKUP_DIR" ]; then
    rm -rf "$BACKUP_DIR"
fi
cp -r "$PROJECT_DIR" "$BACKUP_DIR"
log "Backup created at: $BACKUP_DIR"

log "[3/7] Pulling latest code from main branch..."
git fetch origin
git reset --hard origin/main
git clean -fd
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Current commit: $CURRENT_COMMIT"

log "[4/7] Checking OpenViking installation mode..."
INSTALL_MODE=$(python3 -c "import openviking; import os; path = openviking.__file__; print('dev' if 'site-packages' not in path else 'site-packages')" 2>/dev/null || echo "not_installed")
log "Current installation mode: $INSTALL_MODE"

if [ "$INSTALL_MODE" = "site-packages" ]; then
    log "⚠️  OpenViking is installed in site-packages mode"
    log "Uninstalling to switch to development mode..."
    pip3 uninstall -y openviking 2>&1 | tee -a "$LOG_FILE" || true
    log "✅ Uninstalled site-packages version"
fi

log "[5/7] Cleaning previous build artifacts..."
make clean 2>/dev/null || true
log "Clean completed"

log "[6/7] Building and installing OpenViking in development mode..."
BUILD_SUCCESS=false
for i in $(seq 1 $MAX_RETRIES); do
    log "Build attempt $i/$MAX_RETRIES..."
    
    if make build 2>&1 | tee -a "$LOG_FILE"; then
        BUILD_SUCCESS=true
        log "Build completed successfully on attempt $i"
        
        INSTALL_PATH=$(python3 -c "import openviking; print(openviking.__file__)" 2>/dev/null || echo "unknown")
        log "OpenViking installed at: $INSTALL_PATH"
        
        if [[ "$INSTALL_PATH" == *"$PROJECT_DIR"* ]]; then
            log "✅ Confirmed: Using development mode (source code directory)"
        else
            log "⚠️  Warning: Not using source code directory"
            log "Expected path to contain: $PROJECT_DIR"
            log "Actual path: $INSTALL_PATH"
        fi
        break
    else
        if [ $i -lt $MAX_RETRIES ]; then
            log "Build failed on attempt $i, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            make clean 2>/dev/null || true
        fi
    fi
done

if [ "$BUILD_SUCCESS" = false ]; then
    log "ERROR: Build failed after $MAX_RETRIES attempts"
    log "Restoring backup..."
    rm -rf "$PROJECT_DIR"
    mv "$BACKUP_DIR" "$PROJECT_DIR"
    log "Backup restored"
    exit 1
fi

log "[7/8] Restarting OpenClaw service..."
if [ -f ~/.openclaw/openviking.env ]; then
    source ~/.openclaw/openviking.env
else
    log "WARNING: ~/.openclaw/openviking.env not found"
fi

RESTART_SUCCESS=false
for i in $(seq 1 $MAX_RETRIES); do
    log "Restart attempt $i/$MAX_RETRIES..."
    
    if openclaw gateway restart 2>&1 | tee -a "$LOG_FILE"; then
        sleep 5
        
        if openclaw gateway status 2>&1 | tee -a "$LOG_FILE" | grep -q "running"; then
            RESTART_SUCCESS=true
            log "OpenClaw gateway restarted successfully on attempt $i"
            break
        else
            log "Gateway not running after restart, retrying..."
            sleep $RETRY_DELAY
        fi
    else
        if [ $i -lt $MAX_RETRIES ]; then
            log "Restart failed on attempt $i, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    fi
done

if [ "$RESTART_SUCCESS" = false ]; then
    log "ERROR: Failed to restart OpenClaw gateway after $MAX_RETRIES attempts"
    log "Please check OpenClaw logs manually"
    exit 1
fi

log "[8/8] Verifying OpenViking installation..."
OPENVIKING_VERSION=$(python3 -c "import openviking; print(openviking.__version__)" 2>/dev/null || echo "unknown")
log "OpenViking version: $OPENVIKING_VERSION"

OPENCLAW_VERSION=$(openclaw --version 2>/dev/null || echo "unknown")
log "OpenClaw version: $OPENCLAW_VERSION"

log "========================================="
log "OpenViking Upgrade Completed Successfully"
log "========================================="
log "Commit: $CURRENT_COMMIT"
log "OpenViking: $OPENVIKING_VERSION"
log "OpenClaw: $OPENCLAW_VERSION"
log "Backup: $BACKUP_DIR"

exit 0
